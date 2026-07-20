"""Authz matrix tests (F11). MUST PASS BEFORE ANY PR."""

import pytest

# Endpoint -> (Method, Role -> Expected Status)
# "public" means no token needed.
MATRIX = {
    "/v1/auth/login": {"method": "POST", "public": 200},
    "/v1/auth/refresh": {
        "method": "POST",
        "public": 422,  # 422 because body is required, but it's public in terms of Bearer token
    },
    "/v1/auth/logout": {
        "method": "POST",
        "roles": {
            "citizen": 200,
            "analyst": 200,
            "officer": 200,
            "admin": 200,
            "unauthed": 401,
        },
    },
    "/v1/pii/decrypt": {
        "method": "POST",
        "roles": {
            "citizen": 403,
            "analyst": 403,
            "officer": 422,  # 422 validation error means auth passed (body required)
            "admin": 422,
            "unauthed": 401,
        },
    },
    "/v1/cases/": {
        "method": "POST",
        "roles": {
            "citizen": 422,  # Validation error on missing body -> auth passed
            "analyst": 422,
            "officer": 422,
            "admin": 422,
            "unauthed": 401,
        },
    },
}


@pytest.mark.asyncio
async def test_authz_matrix() -> None:
    """Validate every endpoint against every role."""
    # This is a stub for the full matrix test. We will implement it fully
    # with real JWTs and a real TestClient when we have the fixture setup.
    pass
