"""v1 API Router."""
from fastapi import APIRouter

from app.api.v1 import auth, cases, pii

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(pii.router)
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
