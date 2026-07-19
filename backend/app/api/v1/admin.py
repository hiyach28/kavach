"""Admin API — batch import and system management (F26)."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser, require_min_role
from app.core.errors import ok
from app.models.graph import Campaign, Case, CaseStatus, Entity

router = APIRouter(prefix="/admin", tags=["admin"])


class BulkCaseImportItem(BaseModel):
    """A single case to import in bulk."""
    text: str = Field(..., max_length=50000, description="Complaint text (raw — will be de-identified)")
    district: str | None = None
    language: str | None = "hi"


class BulkCaseImportRequest(BaseModel):
    cases: list[BulkCaseImportItem] = Field(..., max_length=1000)


@router.post("/import/cases", dependencies=[Depends(require_min_role("admin"))])
async def bulk_import_cases(
    req: BulkCaseImportRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Bulk import cases (admin only).

    Each case's text is de-identified and PII vaulted, then the case is
    enqueued to the async worker pipeline. Max 1,000 cases per request.
    """
    from app.core.redis import redis_pool
    from app.services.deidentify import deidentify
    from app.services.pii_service import store_and_tokenize

    pii_key = settings.PII_MASTER_KEY.encode("utf-8").ljust(32, b"\0")[:32]
    imported = 0
    errors: list[str] = []

    for item in req.cases:
        try:
            case_id = uuid.uuid4()

            # 1. De-identify
            deid_result = deidentify(item.text)

            # 2. Vault PII
            if deid_result["extracted"]:
                await store_and_tokenize(
                    deid_result["extracted"], case_id, db, pii_key,
                )

            # 3. Insert case
            from app.models.graph import Case, CaseStatus as CS
            new_case = Case(
                id=case_id,
                status=CS.queued,
                district=item.district,
                language=item.language or "hi",
            )
            db.add(new_case)

            # 4. Enqueue worker
            if redis_pool:
                await redis_pool.enqueue_job(
                    "process_case",
                    case_id=str(case_id),
                    masked_text=deid_result["masked_text"],
                )

            imported += 1

        except Exception as exc:
            errors.append(f"Case at index {imported + len(errors)}: {exc}")

    await db.commit()

    return ok({
        "imported": imported,
        "errors": errors,
        "total": len(req.cases),
    })


@router.get("/stats", dependencies=[Depends(require_min_role("analyst"))])
async def admin_stats(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """System-wide statistics (analyst+)."""
    # Case counts by status
    status_counts = (await db.execute(
        select(Case.status, func.count(Case.id))
        .group_by(Case.status)
    )).all()
    by_status = {str(row[0]): row[1] for row in status_counts}

    # Campaign count
    campaign_count = (await db.execute(
        select(func.count(Campaign.id))
    )).scalar() or 0

    # Entity count
    entity_count = (await db.execute(
        select(func.count(Entity.id))
    )).scalar() or 0

    return ok({
        "total_cases": sum(by_status.values()),
        "cases_by_status": by_status,
        "total_campaigns": campaign_count,
        "total_entities": entity_count,
    })
