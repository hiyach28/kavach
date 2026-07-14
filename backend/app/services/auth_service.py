"""Authentication service (Phase 1)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AuthError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    token_jti,
    verify_password,
)
from app.models.user import User

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


async def login(
    email: str,
    password: str,
    db: AsyncSession,
    r: aioredis.Redis,
) -> dict[str, str]:
    """Verify credentials, enforce lockout, return tokens."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthError("Invalid email or password")  # Generic error to prevent enumeration

    # Check lockout
    now = datetime.now(UTC)
    if user.locked_until and user.locked_until > now:
        raise AuthError("Account temporarily locked due to failed attempts")

    if not verify_password(password, user.hashed_password):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + LOCKOUT_DURATION
        await db.commit()
        raise AuthError("Invalid email or password")

    # Success: reset failed attempts
    if user.failed_attempts > 0 or user.locked_until:
        user.failed_attempts = 0
        user.locked_until = None
        await db.commit()

    return {
        "access_token": create_access_token(str(user.id), user.role, user.district_scope),
        "refresh_token": create_refresh_token(str(user.id)),
        "role": user.role,
    }


async def refresh(
    refresh_token: str,
    db: AsyncSession,
    r: aioredis.Redis,
) -> dict[str, str]:
    """Rotate access token if refresh token is valid."""
    try:
        claims = decode_token(refresh_token)
    except Exception as err:
        raise AuthError("Invalid or expired refresh token") from err

    if claims.get("type") != "refresh":
        raise AuthError("Expected refresh token")

    jti = claims.get("jti", "")
    if await r.exists(f"denylist:{jti}"):
        raise AuthError("Refresh token has been revoked")

    user_id_str = claims.get("sub")
    if not user_id_str:
        raise AuthError("Invalid token subject")
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as err:
        raise AuthError("Invalid token subject format") from err

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthError("User not found")

    # Success: generate new access token
    return {
        "access_token": create_access_token(str(user.id), user.role, user.district_scope),
    }


async def logout(token: str, r: aioredis.Redis) -> None:
    """Denylist the token. TTL is remaining lifetime."""
    jti = token_jti(token)
    if not jti:
        return

    try:
        claims = decode_token(token)
    except Exception:
        return  # If it's already expired/invalid, we don't need to denylist it

    exp = claims.get("exp")
    if exp:
        now = int(datetime.now(UTC).timestamp())
        ttl = exp - now
        if ttl > 0:
            await r.setex(f"denylist:{jti}", ttl, "1")
