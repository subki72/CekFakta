"""
FactGuard (Cek Fakta) — FastAPI Backend Entry Point

This is the main entry point for the FastAPI application.
On Vercel, this file is served as a serverless function via vercel.json rewrites.
Locally, run with: uvicorn api.main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import analyses, analyze, community, cron, feedback, trending
from api.utils.rate_limiter import RateLimitExceeded

load_dotenv()
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation: audit presence of critical production configuration (M5)
    critical_vars = ["GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [k for k in critical_vars if not os.getenv(k)]
    if missing:
        logger.warning(
            f"[STARTUP AUDIT] Missing essential environment variables: {', '.join(missing)}. "
            "Downstream operations relying on these services will fail."
        )
    yield


app = FastAPI(
    title="FactGuard AI API",
    description="API untuk mendeteksi objektivitas narasi politik Indonesia",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow Next.js frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        os.getenv("FRONTEND_URL", ""),  # Production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(analyze.router, prefix="/api", tags=["Analyze"])
app.include_router(analyses.router, prefix="/api", tags=["Analyses"])
app.include_router(trending.router, prefix="/api", tags=["Trending"])
app.include_router(community.router, prefix="/api", tags=["Community"])
app.include_router(cron.router, prefix="/api/cron", tags=["Cron"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Global handler for rate limit errors (BR13: 3 req/min/IP)."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Terlalu banyak permintaan. Silakan tunggu sebentar sebelum mencoba lagi.",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure all HTTPExceptions follow the standard APIError contract."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": detail,
            "code": f"HTTP_{exc.status_code}",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler to prevent server crashes with structured logging."""
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Terjadi kesalahan internal. Silakan coba lagi nanti.",
            "code": "INTERNAL_ERROR",
        },
    )


@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"success": True, "data": {"status": "ok"}}

