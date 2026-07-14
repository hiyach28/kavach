"""FastAPI dependencies: authentication, RBAC, district scoping (F10, F11)."""
from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.errors import AuthError, ForbiddenError
from app.core.security import decode_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)

# Role hierarchy — higher index = more privilege
_ROLE_ORDER = ["citizen", "analyst", "officer", "admin"]


async def _get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(settings.REDIS_URL)  # type: ignore[no-untyped-call]


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate Bearer token, check Redis denylist, return User row."""
    if creds is None:
        raise AuthError("Missing Bearer token")
    token = creds.credentials
    try:
        claims = decode_token(token)
    except JWTError:
        raise AuthError("Invalid or expired token")

    if claims.get("type") != "access":
        raise AuthError("Expected access token")

    # Check denylist
    jti = claims.get("jti", "")
    r = await _get_redis()
    try:
        if await r.exists(f"denylist:{jti}"):
            raise AuthError("Token has been revoked")
    finally:
        await r.aclose()

    user_id = claims.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):  # type: ignore[no-untyped-def]
    """Dependency factory: restrict endpoint to specific roles."""
    async def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"Requires role: {' or '.join(roles)}")
        return user
    return _check


def require_min_role(min_role: str):  # type: ignore[no-untyped-def]
    """Dependency factory: restrict to min_role or higher in the hierarchy."""
    min_idx = _ROLE_ORDER.index(min_role)

    async def _check(user: CurrentUser) -> User:
        if _ROLE_ORDER.index(user.role) < min_idx:
            raise ForbiddenError(f"Requires at least {min_role} role")
        return user
    return _check


def get_district_filter(user: User) -> list[str] | None:
    """Return district scope list, or None if user can see all (officer/admin)."""
    if user.role in ("officer", "admin"):
        return None  # unrestricted
    return user.district_scope or []
