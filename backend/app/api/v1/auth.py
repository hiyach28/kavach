"""Auth endpoints (F10)."""
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser, _get_redis
from app.core.errors import ok
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(
    req: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[aioredis.Redis, Depends(_get_redis)],  # type: ignore[type-arg]
) -> dict:
    """Login with email/password. Returns access and refresh tokens."""
    tokens = await auth_service.login(req.email, req.password, db, r)
    return ok(tokens)


@router.post("/refresh")
async def refresh(
    req: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[aioredis.Redis, Depends(_get_redis)],  # type: ignore[type-arg]
) -> dict:
    """Refresh access token."""
    tokens = await auth_service.refresh(req.refresh_token, db, r)
    return ok(tokens)


@router.post("/logout")
async def logout(
    request: Request,
    r: Annotated[aioredis.Redis, Depends(_get_redis)],  # type: ignore[type-arg]
    user: CurrentUser,
) -> dict:
    """Logout current user by denylisting their token."""
    # We need the raw token to denylist it
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        await auth_service.logout(token, r)
    return ok({"success": True})
