"""Request middleware: trace_id injection, security headers, rate-limit setup.

Rate limits (F15):
  - Shield endpoints: 20 req/min per IP
  - Terminal endpoints: 120 req/min per authenticated user
  - Applied via slowapi decorators on individual routes.
"""
from __future__ import annotations

import uuid

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import set_trace_id

# ── Rate limiter (slowapi) — attach to app in main.py ───────────────────────
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    from fastapi.responses import JSONResponse

    from app.core.errors import err
    return JSONResponse(
        status_code=429,
        content=err("RATE_LIMITED", "Too many requests — slow down"),
        headers={"Retry-After": "60"},
    )


# ── Trace ID + security headers middleware ───────────────────────────────────
class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        tid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_trace_id(tid)

        response: Response = await call_next(request)

        # Inject trace ID into response
        response.headers["X-Request-ID"] = tid

        # Security headers (F15, docs/03 §3)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        )

        return response


# avoid circular import
from typing import Any  # noqa: E402
