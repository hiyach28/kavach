"""Cases API (F20)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import redis
from app.core.database import get_db
from app.core.deps import CurrentUser, get_pii_vault_key
from app.models.graph import Case, CaseStatus
from app.services.deidentify import deidentify
from app.services.pii_service import store_and_tokenize

router = APIRouter()


class CaseCreateRequest(BaseModel):
    text: str = Field(..., max_length=50000)
    district: str | None = None
    language: str | None = None


class CaseCreateResponse(BaseModel):
    case_id: uuid.UUID
    status: CaseStatus


@router.post("/", response_model=CaseCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_case(
    request: CaseCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    pii_key: Annotated[bytes, Depends(get_pii_vault_key)],
) -> CaseCreateResponse:
    """
    F20: Async Case Intake.
    Validates, masks, vaults, inserts as `queued`, and enqueues to arq worker.
    """
    case_id = uuid.uuid4()

    # 1. Mask text synchronously
    deid_result = deidentify(request.text)

    # 2. Vault extracted PII
    if deid_result["extracted"]:
        # store_and_tokenize deduplicates and stores into pii_vault, then commits
        await store_and_tokenize(deid_result["extracted"], case_id, db, pii_key)

    # 3. Insert case record
    new_case = Case(
        id=case_id,
        status=CaseStatus.queued,
        district=request.district,
        language=request.language,
    )
    db.add(new_case)
    await db.commit()

    # 4. Enqueue to arq worker
    if redis.redis_pool:
        # Pass the masked text to the worker for LLM classification and extraction
        await redis.redis_pool.enqueue_job(
            "process_case", case_id=str(case_id), masked_text=deid_result["masked_text"]
        )

    return CaseCreateResponse(case_id=case_id, status=CaseStatus.queued)
