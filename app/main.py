"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.schemas.common import HealthResponse
from app.utils.exceptions import register_exception_handlers

settings = get_settings()

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s (env=%s)", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    # In production, API docs/schema are disabled by default - they're a
    # convenience for development, not something that needs to be publicly
    # exposed on a live deployment. Set APP_ENV=production to disable them;
    # any other value (development, staging, ...) keeps them on.
    is_production = settings.APP_ENV.lower() == "production"

    app = FastAPI(
        title=settings.APP_NAME,
        description="Backend API for the AI-Powered Placement Management System.",
        version="0.2.0",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
        lifespan=lifespan,
    )

    # --- CORS ---
    # Origins come from the CORS_ORIGINS env var (comma-separated), never
    # hardcoded, so dev/staging/prod can each set their own allowed origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Global error handling ---
    register_exception_handlers(app)

    # --- Routers ---
    # All feature routers (auth, students, jobs, ...) are registered inside
    # app/api/v1/router.py, so this is the only include_router call main.py
    # will ever need.
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # --- Health check ---
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    def health_check() -> HealthResponse:
        return HealthResponse(
            status="ok",
            message="AI Placement Management System API is running",
        )

    return app


app = create_app()
