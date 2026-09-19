"""POST /api/language/detect — Language identification via IndicLID"""
from fastapi import APIRouter
from app.schemas.schemas import LanguageDetectRequest, LanguageDetectResponse
from app.services.language_service import language_detection_service

router = APIRouter()


@router.post("/language/detect", response_model=LanguageDetectResponse)
async def detect_language(request: LanguageDetectRequest):
    lang_info = await language_detection_service.detect(request.text)
    lang_status = language_detection_service.get_status()

    return LanguageDetectResponse(
        primary_language=lang_info.primary_language,
        language_name=lang_info.language_name,
        languages=lang_info.languages,
        script=lang_info.script,
        is_code_mixed=lang_info.is_code_mixed,
        confidence=lang_info.confidence,
        model="IndicLID" if lang_status["indiclid_available"] else "heuristic_fallback",
    )
