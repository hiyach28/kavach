"""Entity extraction and hashed graph service (F22).

Extracts infrastructure entities from complaint text, normalises them,
hashes with SHA-256, then upserts into the `entities` table and creates
`case_entity_links` edges. report_count is incremented atomically.

Entities extracted: PHONE, UPI, EMAIL, URL, HANDLE, AADHAAR, PAN, IFSC.
Normalisation rules ensure the same number in two formats → one entity.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import CaseEntityLink, Entity, EntityType


# ── Regex patterns (ordered by priority / specificity) ──────────────────────
# These mirror the de-identification patterns but are purpose-built for
# *extraction and normalisation*, not masking.
_PATTERNS: list[tuple[EntityType, re.Pattern[str]]] = [
    # UPI before EMAIL so "name@upi" doesn't become EMAIL
    (EntityType.UPI,    re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@(?:upi|paytm|gpay|phonepe|ybl|okhdfcbank|okaxis|oksbi|okicici|apl|axl|ibl|hdfcbank|sbi|pnb|boi|cnrb|unionbank|bandhanbank|kotak|indus|airtel|jio)\b", re.IGNORECASE)),
    (EntityType.EMAIL,  re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE)),
    (EntityType.AADHAAR,re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")),
    (EntityType.PAN,    re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    (EntityType.IFSC,   re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    (EntityType.PHONE,  re.compile(r"(?:\+91[\s\-]?)?[6789]\d{9}\b")),
    # URL before HANDLE to avoid partial matches
    (EntityType.URL,    re.compile(r"https?://[^\s]+")),
    (EntityType.HANDLE, re.compile(r"@[a-zA-Z0-9_]{3,32}\b")),
]

# Known UPI suffixes for normalisation
_UPI_SUFFIXES = {
    "upi", "paytm", "gpay", "phonepe", "ybl", "okhdfcbank", "okaxis",
    "oksbi", "okicici", "apl", "axl", "ibl", "hdfcbank", "sbi", "pnb",
    "boi", "cnrb", "unionbank", "bandhanbank", "kotak", "indus", "airtel",
    "jio",
}


# ── Normalisation ────────────────────────────────────────────────────────────

def _normalise(entity_type: EntityType, raw: str) -> str:
    """Return a canonical form of the entity value."""
    match entity_type:
        case EntityType.PHONE:
            # Strip +91, spaces, hyphens; keep 10-digit number
            digits = re.sub(r"[^\d]", "", raw)
            return digits[-10:] if len(digits) >= 10 else digits
        case EntityType.UPI | EntityType.EMAIL:
            return raw.lower().strip()
        case EntityType.AADHAAR:
            return re.sub(r"[\s\-]", "", raw)
        case EntityType.URL:
            # Lowercase scheme + host; preserve path
            return raw.lower().strip().rstrip("/")
        case EntityType.HANDLE:
            return raw.lower().strip()
        case _:
            return raw.upper().strip()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# ── Extraction ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ExtractedEntity:
    type: EntityType
    normalised: str
    value_hash: str


def extract_entities(text: str) -> list[ExtractedEntity]:
    """
    Extract and deduplicate entities from complaint text.
    Returns a list of ExtractedEntity (normalised + hashed).
    """
    seen_hashes: set[str] = set()
    result: list[ExtractedEntity] = []

    for entity_type, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group()
            norm = _normalise(entity_type, raw)
            h = _sha256(f"{entity_type.value}:{norm}")
            if h not in seen_hashes:
                seen_hashes.add(h)
                result.append(ExtractedEntity(type=entity_type, normalised=norm, value_hash=h))

    return result


# ── DB upsert ────────────────────────────────────────────────────────────────

async def upsert_entities(
    case_id: uuid.UUID,
    entities: list[ExtractedEntity],
    db: AsyncSession,
) -> list[Entity]:
    """
    Upsert each entity into the `entities` table (atomic report_count increment)
    and create `case_entity_links` edges.  Returns list of Entity rows.
    """
    if not entities:
        return []

    now = datetime.now(UTC)
    db_entities: list[Entity] = []

    for ent in entities:
        # Try to find existing entity by hash
        result = await db.execute(
            select(Entity).where(Entity.value_hash == ent.value_hash)
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            new_ent = Entity(
                type=ent.type,
                value_hash=ent.value_hash,
                first_seen=now,
                report_count=1,
            )
            db.add(new_ent)
            await db.flush()  # get the ID without committing
            db_entities.append(new_ent)
            entity_id = new_ent.id
        else:
            # Atomic increment
            await db.execute(
                update(Entity)
                .where(Entity.id == existing.id)
                .values(report_count=Entity.report_count + 1)
            )
            db_entities.append(existing)
            entity_id = existing.id

        # Create edge (ignore duplicate)
        link_result = await db.execute(
            select(CaseEntityLink).where(
                CaseEntityLink.case_id == case_id,
                CaseEntityLink.entity_id == entity_id,
            )
        )
        if link_result.scalar_one_or_none() is None:
            db.add(CaseEntityLink(case_id=case_id, entity_id=entity_id, created_at=now))

    await db.flush()
    return db_entities
