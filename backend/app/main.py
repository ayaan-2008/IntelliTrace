from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.config.constants import API_V1_PREFIX
from app.db.database import engine, get_db
from app.routers import (
    alerts_router,
    analytics_router,
    auth_router,
    devices_router,
    telemetry_router,
    users_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="IntelliTrace API",
    description="Smart Wearable Security & Health Monitoring System Backend",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

allowed_origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(devices_router, prefix=API_V1_PREFIX)
app.include_router(telemetry_router, prefix=API_V1_PREFIX)
app.include_router(analytics_router, prefix=API_V1_PREFIX)
app.include_router(alerts_router, prefix=API_V1_PREFIX)


@app.get("/health")
async def health_check():
    db_ok = True
    try:
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            break
    except Exception:
        db_ok = False
    status = "healthy" if db_ok else "degraded"
    return {"status": status, "service": "intellitrace-api", "database": "connected" if db_ok else "disconnected"}


@app.get("/")
async def root():
    return {
        "service": "IntelliTrace API",
        "version": "0.1.0",
        "docs": "/docs",
    }
