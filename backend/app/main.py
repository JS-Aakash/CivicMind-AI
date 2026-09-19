"""
CivicMind AI — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import health, models, language, ai, grievances, incidents, map_routes, routing_routes, media_routes, command_center

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info("=" * 60)
    logger.info("CivicMind AI — Backend Starting")
    logger.info(f"Environment: {'DEMO' if settings.DEMO_MODE else 'PRODUCTION'}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info("=" * 60)

    # Pre-load MuRIL on startup (non-blocking; model loads lazily)
    try:
        from app.services.muril_service import muril_service
        await muril_service.initialize()
        logger.info("MuRIL service initialized")
    except Exception as e:
        logger.warning(f"MuRIL service initialization deferred: {e}")

    # Initialize IndicLID language service
    try:
        from app.services.language_service import language_detection_service
        await language_detection_service.initialize()
        logger.info("Language detection service initialized")
    except Exception as e:
        logger.warning(f"Language detection service initialization deferred: {e}")

    # Seed Module 4 incidents and complaints
    try:
        from scripts.seed_module4_demo import generate_module4_demo_complaints
        from app.services.muril_classifier import muril_classifier_service
        from app.services.incident_service import incident_service
        complaints = generate_module4_demo_complaints()
        for c in complaints:
            if "embedding" not in c or not c["embedding"]:
                c["embedding"] = muril_classifier_service.get_embedding(c["text"])
        incident_service.seed_complaints(complaints)
        incident_service.recompute_all_incidents(time_window_hours=720, dry_run=False)
        logger.info("Module 4 incidents & geolocated complaints initialized successfully")
    except Exception as e:
        logger.warning(f"Module 4 seeding deferred: {e}")

    logger.info("CivicMind AI backend ready")
    yield

    logger.info("CivicMind AI backend shutting down")


app = FastAPI(
    title="CivicMind AI",
    description="Multilingual Civic Grievance Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(models.router, prefix="/api", tags=["Models"])
app.include_router(language.router, prefix="/api", tags=["Language"])
app.include_router(ai.router, prefix="/api", tags=["AI"])
app.include_router(grievances.router, prefix="/api", tags=["Grievances"])
app.include_router(incidents.router, prefix="/api", tags=["Incidents"])
app.include_router(map_routes.router, prefix="/api", tags=["Map"])
app.include_router(routing_routes.router, prefix="/api", tags=["Routing & SLA"])
app.include_router(media_routes.router, prefix="/api", tags=["Media & Multimodal"])
app.include_router(command_center.router, tags=["Command Center & Analytics"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "type": type(exc).__name__},
    )
