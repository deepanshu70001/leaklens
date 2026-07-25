"""
LeakLens — FastAPI entrypoint.
CORS, router registration, rate limiting, and app lifecycle.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection


# ── Rate Limiter (in-memory, no Redis) ───────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


# ── App Lifecycle ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


# ── FastAPI App ──────────────────────────────────────────────────────
app = FastAPI(
    title="LeakLens API",
    description="Detect subscription leaks, flag price hikes, and simulate savings growth.",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────────────
raw_origins = [o.strip().rstrip("/") for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

if "*" in raw_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=raw_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )



# ── Health Check ─────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "leaklens-api", "version": "1.0.0"}


# ── Register Routers ────────────────────────────────────────────────
from app.routers import (
    auth_router,
    ingest_router,
    subscriptions_router,
    dashboard_router,
    actions_router,
    growth_router,
    negotiate_router,
    whatsapp_router,
)

app.include_router(auth_router.router)
app.include_router(ingest_router.router)
app.include_router(subscriptions_router.router)
app.include_router(dashboard_router.router)
app.include_router(actions_router.router)
app.include_router(growth_router.router)
app.include_router(negotiate_router.router)
app.include_router(whatsapp_router.router)
