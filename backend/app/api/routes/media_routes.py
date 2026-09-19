"""
CivicMind AI — Media & Multimodal Intelligence Routes (Module 5)
Endpoints:
- POST /api/media/audio — Upload and transcribe voice grievance
- POST /api/media/images — Upload and analyze photo evidence with Qwen3-VL
- GET  /api/media/{media_id} — Serve media or thumbnail file
- GET  /api/media/{media_id}/status — Check async processing status
- POST /api/media/{media_id}/retry — Retry failed media analysis
- GET  /api/models/multimodal — Multimodal models status (Whisper & Qwen3-VL)
- GET  /api/health/vision — Ollama Qwen3-VL health probe
"""
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
from datetime import datetime, timezone

from app.services.media_service import media_service
from app.services.vision_service import vision_service
from app.services.voice_service import voice_service
from app.schemas.schemas import (
    MediaUploadResponse,
    VoiceTranscribeResponse,
    VisionAnalysisResult,
    MultimodalModelStatus,
)

router = APIRouter()


@router.post("/media/audio", response_model=VoiceTranscribeResponse)
async def upload_and_transcribe_audio(
    file: UploadFile = File(...),
    language_hint: Optional[str] = Form(None),
    complaint_id: Optional[str] = Form(None),
):
    """
    Accepts citizen audio file, validates, securely stores, and transcribes using local Whisper.
    """
    content = await file.read()
    valid, err_msg = media_service.validate_file(file.filename or "voice.wav", content, "audio")
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # Save audio record
    media_record = media_service.save_audio(content, file.filename or "voice.wav", complaint_id)

    # Transcribe audio locally with Whisper
    transcription = voice_service.transcribe_audio(
        audio_path=media_record["storage_path"],
        media_id=media_record["id"],
        language_hint=language_hint,
    )

    return VoiceTranscribeResponse(
        transcription_id=transcription["transcription_id"],
        media_id=media_record["id"],
        raw_transcript=transcription["raw_transcript"],
        edited_transcript=transcription["edited_transcript"],
        language=transcription["language"],
        language_name=transcription["language_name"],
        confidence=transcription["confidence"],
        duration_seconds=transcription["duration_seconds"],
        model_name=transcription["model_name"],
        model_version=transcription["model_version"],
        created_at=datetime.fromisoformat(transcription["created_at"]),
    )


@router.post("/media/images", response_model=VisionAnalysisResult)
async def upload_and_analyze_image(
    file: UploadFile = File(...),
    complaint_text: Optional[str] = Form(None),
    complaint_id: Optional[str] = Form(None),
):
    """
    Accepts citizen photo evidence, validates, stores securely, and extracts structured visual evidence using Qwen3-VL 4B.
    """
    content = await file.read()
    valid, err_msg = media_service.validate_file(file.filename or "evidence.jpg", content, "image")
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    # Save image & generate thumbnail
    media_record = media_service.save_image(content, file.filename or "evidence.jpg", complaint_id)

    # Analyze with local Qwen3-VL
    vision_result = vision_service.analyze_image(
        image_path=media_record["storage_path"],
        media_id=media_record["id"],
        complaint_text=complaint_text,
    )

    return VisionAnalysisResult(
        analysis_id=vision_result["analysis_id"],
        media_id=media_record["id"],
        observations=vision_result["observations"],
        objects=vision_result["objects"],
        possible_hazards=vision_result["possible_hazards"],
        evidence_category=vision_result["evidence_category"],
        severity_signal=vision_result["severity_signal"],
        confidence=vision_result["confidence"],
        model_name=vision_result["model_name"],
        model_version=vision_result["model_version"],
        prompt_version=vision_result["prompt_version"],
        created_at=datetime.fromisoformat(vision_result["created_at"]),
    )


@router.get("/media/{media_id}")
async def get_media_file(media_id: str, thumb: bool = Query(False)):
    """
    Serves uploaded media image or thumbnail with path traversal prevention.
    """
    media = media_service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail=f"Media {media_id} not found")

    file_path = media["thumbnail_path"] if thumb and media.get("thumbnail_path") else media["storage_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Media file not found on storage")

    return FileResponse(file_path, media_type=media.get("mime_type", "application/octet-stream"))


@router.get("/media/{media_id}/status")
async def get_media_status(media_id: str):
    """
    Returns media processing status and analysis summaries.
    """
    media = media_service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail=f"Media {media_id} not found")

    vision_data = vision_service._analysis_cache.get(media_id)
    voice_data = voice_service._transcription_cache.get(media_id)

    return {
        "media_id": media_id,
        "media_type": media["media_type"],
        "processing_status": media["processing_status"],
        "has_vision_analysis": vision_data is not None,
        "vision_analysis": vision_data,
        "has_voice_transcription": voice_data is not None,
        "voice_transcription": voice_data,
        "created_at": media["created_at"],
    }


@router.post("/media/{media_id}/retry")
async def retry_media_analysis(media_id: str):
    """
    Retries failed image analysis or voice transcription.
    """
    media = media_service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail=f"Media {media_id} not found")

    if media["media_type"] == "image":
        vision_service._analysis_cache.pop(media_id, None)
        result = vision_service.analyze_image(media["storage_path"], media_id=media_id)
        return {"status": "completed", "result": result}
    elif media["media_type"] == "audio":
        voice_service._transcription_cache.pop(media_id, None)
        result = voice_service.transcribe_audio(media["storage_path"], media_id=media_id)
        return {"status": "completed", "result": result}

    raise HTTPException(status_code=400, detail="Unknown media type")


@router.get("/models/multimodal", response_model=MultimodalModelStatus)
async def get_multimodal_model_status():
    """
    Returns availability, versions, and device allocations for local Whisper and Qwen3-VL models.
    """
    whisper_status = voice_service.get_model_status()
    vision_status = vision_service.check_health()

    return MultimodalModelStatus(
        whisper=whisper_status,
        vision=vision_status,
        ollama_endpoint=vision_service.ollama_url,
        local=True,
    )


@router.get("/health/vision")
async def get_vision_health():
    """
    Probes Ollama connection and Qwen3-VL model responsiveness.
    """
    health = vision_service.check_health()
    if not health.get("available"):
        return JSONResponse(status_code=503, content=health)
    return health
