"""v1 API Router."""
from fastapi import APIRouter

from app.api.v1 import admin, auth, campaigns, cases, pii, shield

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(pii.router)
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(campaigns.router)
api_router.include_router(admin.router)
api_router.include_router(shield.router, prefix="/shield", tags=["shield"])
