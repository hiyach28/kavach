#!/usr/bin/env python3
"""F26: Batch CSV/JSON importer for KAVACH cases.

Imports cases through the same pipeline as the API: de-identify → vault PII →
insert case record → enqueue worker for LLM/entity/clustering pipeline.

Usage:
    # CSV import (NCRP/1930-style columns)
    python backend/scripts/batch_import.py cases.csv --format csv

    # JSON array import
    python backend/scripts/batch_import.py cases.json --format json

    # Dry-run (validate without writing)
    python backend/scripts/batch_import.py cases.csv --dry-run

CSV columns (auto-detected from header):
    text, district, language
    (fraud_type and status are optional — they will be populated by the pipeline)

JSON format:
    [{"text": "...", "district": "...", "language": "..."}]
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

# Add backend/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.redis import close_redis_pool, init_redis_pool  # noqa: E402
from app.models.graph import Case, CaseStatus  # noqa: E402
from app.services.deidentify import deidentify  # noqa: E402
from app.services.pii_service import store_and_tokenize  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("batch_import")


def parse_csv(path: Path) -> list[dict[str, Any]]:
    """Parse CSV file with NCRP-style columns."""
    records: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            normalised = {}
            for k, v in row.items():
                key = k.strip().lower().replace(" ", "_")
                normalised[key] = (v or "").strip()

            record: dict[str, Any] = {
                "text": normalised.get(
                    "text",
                    normalised.get("complaint", normalised.get("description", "")),
                ),
                "district": normalised.get("district", ""),
                "language": normalised.get("language", "hi"),
            }
            if "fraud_type" in normalised:
                record["fraud_type"] = normalised["fraud_type"]
            if "status" in normalised:
                record["status"] = normalised["status"]
            if record["text"]:
                records.append(record)

    return records


def parse_json(path: Path) -> list[dict[str, Any]]:
    """Parse JSON array file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "cases" in data:
        data = data["cases"]

    records: list[dict[str, Any]] = []
    for item in data:
        record = {
            "text": item.get("text", item.get("complaint", "")),
            "district": item.get("district", ""),
            "language": item.get("language", "hi"),
        }
        if "fraud_type" in item:
            record["fraud_type"] = item["fraud_type"]
        if record["text"]:
            records.append(record)

    return records


async def import_records(
    records: list[dict[str, Any]],
    *,
    dry_run: bool = False,
    batch_size: int = 50,
    pii_key: bytes | None = None,
    enqueue: bool = False,
) -> dict[str, Any]:
    """Insert records through the KAVACH pipeline.

    De-identifies text, vaults PII, inserts case, and optionally enqueues
    the async worker pipeline.

    Returns summary statistics.
    """
    total = len(records)
    inserted = 0
    errors = 0
    skipped = 0

    if not pii_key:
        pii_key = settings.PII_MASTER_KEY.encode("utf-8").ljust(32, b"\0")[:32]

    if dry_run:
        logger.info("Dry-run: %d records validated, none written.", total)
        return {"total": total, "inserted": 0, "errors": 0, "dry_run": True}

    # Initialise Redis pool if enqueuing
    if enqueue:
        await init_redis_pool()

    from app.core.redis import redis_pool as rp

    async with AsyncSessionLocal() as db:
        for i in range(0, total, batch_size):
            batch = records[i : i + batch_size]
            for j, record in enumerate(batch):
                try:
                    case_id = uuid.uuid4()
                    text = record["text"]

                    # 1. De-identify
                    deid_result = deidentify(text)
                    masked_text = deid_result["masked_text"]

                    # 2. Vault PII
                    if deid_result["extracted"]:
                        await store_and_tokenize(
                            deid_result["extracted"],
                            case_id,
                            db,
                            pii_key,
                        )

                    # 3. Insert case record (raw text is NEVER stored — only masked)
                    new_case = Case(
                        id=case_id,
                        status=CaseStatus.queued,
                        district=record.get("district") or None,
                        language=record.get("language") or "hi",
                    )
                    if "fraud_type" in record and record["fraud_type"]:
                        # Allow pre-classified imports to skip LLM step
                        from app.models.graph import FraudType

                        try:
                            new_case.fraud_type = FraudType(record["fraud_type"])
                            new_case.status = CaseStatus.extracting
                        except ValueError:
                            logger.warning(
                                "  Unknown fraud_type '%s' for record %d, will auto-classify",
                                record["fraud_type"],
                                i + j,
                            )

                    db.add(new_case)

                    # 4. Optional: enqueue worker
                    if enqueue and rp:
                        await rp.enqueue_job(
                            "process_case",
                            case_id=str(case_id),
                            masked_text=masked_text,
                        )

                    inserted += 1

                except Exception as exc:
                    logger.error("Error importing record %d: %s", i + j, exc)
                    errors += 1

            await db.flush()
            logger.info(
                "  Batch %d/%d: %d records processed",
                i // batch_size + 1,
                (total - 1) // batch_size + 1,
                len(batch),
            )

        await db.commit()

    if enqueue:
        await close_redis_pool()

    logger.info("Import complete: %d inserted, %d errors / %d total", inserted, errors, total)
    return {
        "total": total,
        "inserted": inserted,
        "errors": errors,
        "skipped": skipped,
        "dry_run": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="KAVACH batch case importer")
    parser.add_argument("file", type=str, help="Path to CSV or JSON file")
    parser.add_argument(
        "--format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="File format (auto-detects from extension)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without importing")
    parser.add_argument(
        "--enqueue", action="store_true", help="Enqueue worker jobs after import (requires Redis)"
    )
    parser.add_argument("--batch-size", type=int, default=50, help="DB batch size (default: 50)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        logger.error("File not found: %s", path)
        sys.exit(1)

    fmt = args.format
    if fmt == "auto":
        if path.suffix.lower() == ".csv":
            fmt = "csv"
        elif path.suffix.lower() == ".json":
            fmt = "json"
        else:
            logger.error(
                "Could not detect format from extension. Use --format csv or --format json"
            )
            sys.exit(1)

    logger.info("Loading %s file: %s", fmt.upper(), path)
    records = parse_csv(path) if fmt == "csv" else parse_json(path)

    if not records:
        logger.error("No valid records found in file.")
        sys.exit(1)

    logger.info("Found %d records to import", len(records))
    summary = asyncio.run(
        import_records(
            records,
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            enqueue=args.enqueue,
        )
    )

    if summary["errors"]:
        logger.warning("Import completed with %d errors.", summary["errors"])
        sys.exit(1)


if __name__ == "__main__":
    main()
