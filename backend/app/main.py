from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine

from app.routes.fraudscope import router as fraudscope_router
from app.routes.networkx_routes import router as networkx_router
from app.routes.crimemap import router as crimemap_router

# Auto-create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="KAVACH API", description="Fraud Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fraudscope_router, prefix="/api", tags=["FraudScope"])
app.include_router(networkx_router, prefix="/api", tags=["NetworkX"])
app.include_router(crimemap_router, prefix="/api", tags=["CrimeMap"])

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "KAVACH Backend is running with full routers!"}
