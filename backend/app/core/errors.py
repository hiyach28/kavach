"""Typed error envelope and exception hierarchy.

Every response — success or failure — uses:
  {success: bool, data: Any | null, error: {code, message} | null, trace_id: str}

Hard rule: no bare except, no stack traces to clients (docs/03 §3).
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Trace ID context var (set per request in middleware) ────────────────────
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    return _trace_id_var.get() or str(uuid.uuid4())


def set_trace_id(tid: str) -> None:
    _trace_id_var.set(tid)


# ── Response envelope ────────────────────────────────────────────────────────
class ErrorDetail(BaseModel):
    code: str
    message: str


class Envelope(BaseModel):
    success: bool
    data: Any = None
    error: ErrorDetail | None = None
    trace_id: str


def ok(data: Any = None) -> dict[str, Any]:
    return Envelope(success=True, data=data, trace_id=get_trace_id()).model_dump()


def err(code: str, message: str, *, data: Any = None) -> dict[str, Any]:
    return Envelope(
        success=False,
        data=data,
        error=ErrorDetail(code=code, message=message),
        trace_id=get_trace_id(),
    ).model_dump()


# ── Exception hierarchy ──────────────────────────────────────────────────────
class KavachException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(KavachException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__("AUTH_ERROR", message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(KavachException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__("FORBIDDEN", message, status.HTTP_403_FORBIDDEN)


class NotFoundError(KavachException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__("NOT_FOUND", f"{resource} not found", status.HTTP_404_NOT_FOUND)


class ValidationError(KavachException):
    def __init__(self, message: str) -> None:
        super().__init__("VALIDATION_ERROR", message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class RateLimitError(KavachException):
    def __init__(self) -> None:
        super().__init__("RATE_LIMITED", "Too many requests", status.HTTP_429_TOO_MANY_REQUESTS)


# ── FastAPI exception handlers ───────────────────────────────────────────────
async def kavach_exception_handler(request: Request, exc: KavachException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=err(exc.code, exc.message),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all — never expose internal details to clients."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=err("INTERNAL_ERROR", "An unexpected error occurred"),
    )
