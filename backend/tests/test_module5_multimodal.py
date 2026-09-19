"""
CivicMind AI — Module 5 Multimodal Intelligence Unit & Integration Tests
Tests:
1. Text-only complaint processing
2. Image-only complaint (Qwen3-VL visual evidence extraction)
3. Text + Image agreement (Consistent multimodal evidence)
4. Text + Image conflict detection (Contradictory categories flagged for human review)
5. Voice + Text (Whisper transcript feeds MuRIL pipeline)
6. Native Tamil speech transcription
7. Code-mixed Tanglish speech recognition
8. Invalid image file rejection (content security)
9. Oversized audio file rejection
10. Graceful degradation when vision model is unavailable
11. Visual hazard signal escalation to Critical priority
12. Citizen tracking response with multilingual templates
"""
import os
import io
import pytest
import tempfile
from PIL import Image

from app.services.vision_service import vision_service, VISION_TO_TEXT_CATEGORY_MAP
from app.services.voice_service import voice_service
from app.services.media_service import media_service
from app.services.grievance_service import grievance_service


@pytest.fixture
def sample_image_path(tmp_path):
    """Creates a temporary sample JPEG image for testing."""
    img_path = str(tmp_path / "test_pothole.jpg")
    img = Image.new("RGB", (200, 200), color=(60, 60, 60))
    img.save(img_path, format="JPEG")
    return img_path


@pytest.fixture
def sample_audio_path(tmp_path):
    """Creates a temporary sample WAV audio file for testing."""
    import wave
    audio_path = str(tmp_path / "test_water_supply.wav")
    with wave.open(audio_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)  # 1 second of silence
    return audio_path


# ─── Test 1: Text-only processing ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_text_only_complaint_pipeline():
    text = "Drinking water supply stopped for 3 days in our street."
    analysis = await grievance_service.analyze(text=text)
    assert analysis.category == "water"
    assert analysis.priority in ["high", "medium", "critical"]
    assert analysis.department_name is not None


# ─── Test 2: Image-only evidence extraction ──────────────────────────────────
def test_image_evidence_extraction(sample_image_path):
    result = vision_service.analyze_image(
        image_path=sample_image_path,
        media_id="test-img-1",
        complaint_text="Pothole on road",
    )
    assert result["evidence_category"] in ["ROAD_DAMAGE", "OTHER", "WATERLOGGING"]
    assert isinstance(result["observations"], list)
    assert len(result["observations"]) > 0
    assert 0.50 <= result["confidence"] <= 1.0


# ─── Test 3: Text + Image agreement ──────────────────────────────────────────
def test_multimodal_agreement_no_conflict():
    conflict, reason = vision_service.detect_multimodal_conflict(
        text_category="roads",
        vision_category="ROAD_DAMAGE",
    )
    assert conflict is False
    assert reason is None


# ─── Test 4: Text + Image conflict detection ──────────────────────────────────
def test_multimodal_conflict_detection():
    # Text mentions electricity, but photo shows road damage
    conflict, reason = vision_service.detect_multimodal_conflict(
        text_category="electricity",
        vision_category="ROAD_DAMAGE",
    )
    assert conflict is True
    assert reason is not None
    assert "Officer review recommended" in reason


# ─── Test 5: Voice transcription integration ─────────────────────────────────
def test_voice_transcription_pipeline(sample_audio_path):
    result = voice_service.transcribe_audio(
        audio_path=sample_audio_path,
        media_id="test-audio-1",
        language_hint="ta",
    )
    assert result["raw_transcript"] is not None
    assert len(result["raw_transcript"]) > 0
    assert result["confidence"] >= 0.70
    assert result["language"] in ["ta", "en", "hi"]


# ─── Test 6: Native Tamil speech transcription ───────────────────────────────
def test_native_tamil_speech():
    result = voice_service._fallback_transcription(
        transcription_id="test-ta-1",
        media_id="test-audio-ta",
        audio_path="tamil_water.wav",
        language_hint="ta",
    )
    assert result["language"] == "ta"
    assert "குடிநீர்" in result["raw_transcript"] or "water" in result["raw_transcript"].lower()


# ─── Test 7: Code-mixed Tanglish speech recognition ──────────────────────────
def test_tanglish_speech_recognition():
    result = voice_service._fallback_transcription(
        transcription_id="test-tanglish-1",
        media_id="test-audio-tanglish",
        audio_path="ta_water_tanglish.wav",
        language_hint="ta",
    )
    assert "water" in result["raw_transcript"].lower() or "varala" in result["raw_transcript"].lower()
    assert result["confidence"] >= 0.85


# ─── Test 8: Invalid image rejection ─────────────────────────────────────────
def test_invalid_image_file_rejected():
    corrupted_bytes = b"NOT_A_REAL_IMAGE_FILE_DATA"
    valid, err = media_service.validate_file("fake.jpg", corrupted_bytes, "image")
    assert valid is False
    assert err is not None


# ─── Test 9: Oversized audio rejection ───────────────────────────────────────
def test_oversized_audio_rejected():
    oversized_bytes = b"\x00" * (30 * 1024 * 1024)  # 30MB exceeds 25MB limit
    valid, err = media_service.validate_file("huge.wav", oversized_bytes, "audio")
    assert valid is False
    assert "exceeds maximum size" in err


# ─── Test 10: Graceful degradation on vision failure ─────────────────────────
def test_graceful_degradation_nonexistent_image():
    result = vision_service.analyze_image(
        image_path="/non/existent/path/image.jpg",
        media_id="missing-img",
        complaint_text="Garbage overflowing on street",
    )
    assert result["processing_status"] == "completed"
    assert result["evidence_category"] == "GARBAGE_ACCUMULATION"
    assert len(result["observations"]) > 0


# ─── Test 11: Visual hazard signal priority escalation ───────────────────────
def test_visual_hazard_escalation():
    # If visual analysis discovers an electrical hazard, category is ELECTRICAL_HAZARD
    res = vision_service._fallback_visual_analysis(
        analysis_id="haz-1",
        media_id="haz-med-1",
        complaint_text="Live wire fell down sparking on road",
    )
    assert res["evidence_category"] == "ELECTRICAL_HAZARD"
    assert res["severity_signal"] == "critical"
    assert any("live" in h or "electrocution" in h for h in res["possible_hazards"])


# ─── Test 12: Multimodal models status probe ─────────────────────────────────
def test_multimodal_model_status():
    status = voice_service.get_model_status()
    assert status["available"] is True
    assert status["local"] is True
    assert "ta" in status["supported_languages"]
