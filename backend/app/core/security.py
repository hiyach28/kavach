"""Security utilities: JWT, password hashing, SHA-256 helpers.

LLM key policy: docs/06 §3 — this module never touches LLM credentials.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# ── Password hashing (argon2) ───────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    return str(_pwd_context.hash(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return bool(_pwd_context.verify(plain, hashed))


# ── SHA-256 canonical hash (used for graph entity keys + PII tokens) ────────
def sha256_hex(value: str) -> str:
    """Deterministic SHA-256 hex digest — used for entity/PII token keys."""
    return hashlib.sha256(value.encode()).hexdigest()


# ── JWT ─────────────────────────────────────────────────────────────────────
_ALGORITHM = "HS256"
_ACCESS_EXPIRE = timedelta(minutes=15)
_REFRESH_EXPIRE = timedelta(days=7)


def create_access_token(sub: str, role: str, district_scope: list[str] | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "role": role,
        "district_scope": district_scope or [],
        "type": "access",
        "exp": datetime.now(UTC) + _ACCESS_EXPIRE,
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)  # type: ignore[no-any-return]


def create_refresh_token(sub: str) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "type": "refresh",
        "exp": datetime.now(UTC) + _REFRESH_EXPIRE,
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)  # type: ignore[no-any-return]


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on any failure."""
    return dict(jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM]))


def token_jti(token: str) -> str | None:
    """Extract jti claim without full validation (for denylist key)."""
    try:
        claims = decode_token(token)
        return str(claims.get("jti", ""))
    except JWTError:
        return None
