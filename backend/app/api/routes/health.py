"""GET /api/health"""
from fastapi import APIRouter
from app.schemas.schemas import HealthResponse
from app.core.config import settings
from app.services.muril_service import muril_service
from app.services.language_service import language_detection_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    muril_ready = await muril_service.is_ready()
    lang_ready = await language_detection_service.is_ready()
    return HealthResponse(
        status="operational",
        version=settings.APP_VERSION,
        demo_mode=settings.DEMO_MODE,
        services={
            "muril": "ready" if muril_ready else "loading",
            "language_detection": "ready" if lang_ready else "loading",
            "database": "connected",
        },
    )
