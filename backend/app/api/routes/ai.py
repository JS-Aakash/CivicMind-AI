"""
POST /api/ai/embedding — Get MuRIL embedding for text
POST /api/grievances/analyze — Full grievance analysis pipeline
"""
from fastapi import APIRouter
from app.schemas.schemas import (
    EmbeddingRequest, EmbeddingResponse,
    GrievanceAnalyzeRequest, GrievanceAnalyzeResponse,
)
from app.services.muril_service import muril_service
from app.services.grievance_service import grievance_service
from app.core.config import settings

router = APIRouter()


@router.post("/ai/embedding", response_model=EmbeddingResponse)
async def get_embedding(request: EmbeddingRequest):
    """Generate MuRIL semantic embedding for any multilingual text."""
    result = await muril_service.embed(request.text)
    return EmbeddingResponse(
        embedding=result.embedding,
        model=result.model,
        dimensions=result.dimensions,
    )


@router.post("/grievances/analyze", response_model=GrievanceAnalyzeResponse)
async def analyze_grievance(request: GrievanceAnalyzeRequest):
    """
    Full grievance analysis pipeline:
    IndicLID language detection → MuRIL embedding → Mock classification → Department routing
    
    Note: Classification is DEMO in Module 1. Real MuRIL predictions in Module 2.
    """
    analysis = await grievance_service.analyze(
        text=request.text,
        location_text=request.location_text,
    )
    return GrievanceAnalyzeResponse(
        analysis=analysis,
        demo_mode=settings.DEMO_MODE,
    )
