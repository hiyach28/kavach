"""arq worker entrypoint — Phase 2B (F20-F24).

Job: process_case
  Drives the case status machine:
    queued → classifying → extracting → linking → clustered
                                               ↘ needs_manual_review
    Any unhandled exception → failed(reason)

Idempotency: each stage checks current status before proceeding, so
replaying a job after a crash is safe.
"""
from __future__ import annotations

import logging
import uuid

from arq.connections import RedisSettings
from sqlalchemy import update

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.models.graph import Case, CaseStatus, SemanticLink
from app.services import llm_client, entity_extractor, embeddings, clustering

logger = logging.getLogger("kavach.worker")

_CONFIDENCE_THRESHOLD = 0.5   # below this → needs_manual_review


async def process_case(
    ctx: dict,
    case_id: str,
    masked_text: str,
) -> dict:
    """
    Full intelligence pipeline for a single case.
    Returns a summary dict for arq result storage.
    """
    cid = uuid.UUID(case_id)

    async with AsyncSessionLocal() as db:
        try:
            # ── 1. CLASSIFYING ──────────────────────────────────────────────
            await db.execute(
                update(Case).where(Case.id == cid).values(status=CaseStatus.classifying)
            )
            await db.commit()

            verdict = llm_client.classify(masked_text)

            # Decide if we need manual review
            needs_review = verdict.confidence < _CONFIDENCE_THRESHOLD or bool(verdict.reason)

            if needs_review:
                await db.execute(
                    update(Case)
                    .where(Case.id == cid)
                    .values(
                        status=CaseStatus.needs_manual_review,
                        fraud_type=verdict.fraud_type,
                        risk=verdict.risk,
                        confidence=verdict.confidence,
                    )
                )
                await db.commit()
                logger.info("case %s → needs_manual_review (conf=%.2f)", cid, verdict.confidence)
                return {"case_id": case_id, "status": "needs_manual_review"}

            # Write classification results
            await db.execute(
                update(Case)
                .where(Case.id == cid)
                .values(
                    fraud_type=verdict.fraud_type,
                    risk=verdict.risk,
                    confidence=verdict.confidence,
                )
            )
            await db.commit()

            # ── 2. EXTRACTING ───────────────────────────────────────────────
            await db.execute(
                update(Case).where(Case.id == cid).values(status=CaseStatus.extracting)
            )
            await db.commit()

            entities = entity_extractor.extract_entities(masked_text)
            await entity_extractor.upsert_entities(cid, entities, db)
            await db.commit()

            # ── 3. LINKING (embed + semantic edges) ─────────────────────────
            await db.execute(
                update(Case).where(Case.id == cid).values(status=CaseStatus.linking)
            )
            await db.commit()

            vec = embeddings.embed(masked_text)
            # Persist embedding on case row
            await db.execute(
                update(Case).where(Case.id == cid).values(embedding=vec)
            )
            await db.commit()

            # Find semantically similar cases and create SemanticLink edges
            similar = await embeddings.top_k_similar(vec, db, k=10, exclude_case_id=cid)
            for sim_case_id, score in similar:
                if score >= clustering.SEMANTIC_THRESHOLD:
                    # Insert both directions idempotently
                    for a, b in [(cid, sim_case_id), (sim_case_id, cid)]:
                        from sqlalchemy import select as sa_select
                        existing = (await db.execute(
                            sa_select(SemanticLink).where(
                                SemanticLink.a_id == a,
                                SemanticLink.b_id == b,
                            )
                        )).scalar_one_or_none()
                        if not existing:
                            db.add(SemanticLink(a_id=a, b_id=b, score=score))
            await db.commit()

            # ── 4. CLUSTERING ───────────────────────────────────────────────
            campaign_id = await clustering.cluster_case(cid, db)
            await db.commit()

            await db.execute(
                update(Case)
                .where(Case.id == cid)
                .values(status=CaseStatus.clustered, campaign_id=campaign_id)
            )
            await db.commit()

            logger.info(
                "case %s → clustered (campaign=%s, fraud_type=%s, confidence=%.2f)",
                cid, campaign_id, verdict.fraud_type, verdict.confidence,
            )
            return {
                "case_id": case_id,
                "status": "clustered",
                "campaign_id": str(campaign_id) if campaign_id else None,
                "fraud_type": verdict.fraud_type.value,
                "confidence": verdict.confidence,
            }

        except Exception as exc:
            logger.exception("process_case %s failed: %s", case_id, exc)
            try:
                async with AsyncSessionLocal() as err_db:
                    await err_db.execute(
                        update(Case)
                        .where(Case.id == cid)
                        .values(status=CaseStatus.failed)
                    )
                    await err_db.commit()
            except Exception:
                pass  # Don't mask the original exception
            raise


# ── Worker settings ─────────────────────────────────────────────────────────

async def ping(ctx: dict) -> str:
    """Smoke-test job — always returns 'pong'."""
    return "pong"


class WorkerSettings:
    functions = [ping, process_case]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 300        # 5 minutes max per job
    retry_jobs = True
    max_tries = 3
    keep_result = 3600       # keep results for 1 hour
