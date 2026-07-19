"""Campaigns API — takedown briefs (F25) and campaign listing."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.errors import NotFoundError, ok
from app.services import takedown_brief as td

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/")
async def list_campaigns(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    min_cases: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List known campaigns with summary statistics."""
    campaigns = await td.list_campaigns(
        db, limit=limit, offset=offset, min_cases=min_cases,
    )
    return ok({"campaigns": campaigns, "total": len(campaigns)})


@router.get("/{campaign_id}/brief")
async def get_takedown_brief(
    campaign_id: str,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    force_refresh: bool = Query(False, alias="force"),
) -> dict[str, Any]:
    """Get (or compute) takedown brief for a campaign.

    By default returns the cached brief. Pass ``force=true`` to recompute.
    """
    try:
        cid = uuid.UUID(campaign_id)
    except ValueError:
        raise NotFoundError(f"Invalid campaign ID: {campaign_id}")

    try:
        brief = await td.compute_takedown_brief(cid, db, force_refresh=force_refresh)
    except ValueError as exc:
        raise NotFoundError(str(exc))

    return ok({"brief": brief})
