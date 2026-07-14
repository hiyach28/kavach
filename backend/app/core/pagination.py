"""Pagination utilities — mandatory on all list endpoints (F15)."""
from __future__ import annotations

from typing import Any, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

MAX_PAGE_SIZE = 100


class PaginationParams:
    """FastAPI dependency for consistent pagination across all list endpoints."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        limit: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE, description="Items per page (max 100)"),
    ) -> None:
        self.page = page
        self.limit = limit

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PagedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    pages: int
    limit: int


async def paginate(
    session: AsyncSession,
    query: Any,
    params: PaginationParams,
) -> PagedResponse:
    """Run a count + paginated select, return PagedResponse."""
    count_q = select(func.count()).select_from(query.subquery())
    total: int = (await session.execute(count_q)).scalar_one()

    rows = (await session.execute(query.offset(params.offset).limit(params.limit))).scalars().all()

    pages = max(1, -(-total // params.limit))  # ceiling division
    return PagedResponse(
        items=list(rows),
        total=total,
        page=params.page,
        pages=pages,
        limit=params.limit,
    )
