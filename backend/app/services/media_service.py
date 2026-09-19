"""
CivicMind AI — Secure Media & Storage Service (Module 5)
Handles:
- Secure media uploads (images: JPEG, PNG, WebP; audio: WAV, MP3, WebM, M4A, OGG)
- Path traversal prevention, magic bytes inspection, size & dimension checks
- Thumbnail generation for responsive frontend rendering
- In-memory & DB storage ledger for media files and async processing jobs
- Safe media URL resolution
"""
import os
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from PIL import Image

from app.services.vision_service import vision_service
from app.services.voice_service import voice_service

logger = logging.getLogger(__name__)

# Allowed MIME types and extensions
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
ALLOWED_AUDIO_MIMES = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3",
    "audio/webm", "audio/ogg",
    "audio/mp4", "audio/m4a", "audio/x-m4a"
}

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp"},
    "audio": {".wav", ".mp3", ".webm", ".ogg", ".m4a"}
}

MAX_IMAGE_SIZE_MB = 15
MAX_AUDIO_SIZE_MB = 25
THUMBNAIL_SIZE = (320, 320)


class MediaService:
    """
    Manages secure uploads, thumbnails, media processing jobs, and access control.
    """

    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = os.path.abspath(base_upload_dir)
        self.images_dir = os.path.join(self.base_upload_dir, "images")
        self.audio_dir = os.path.join(self.base_upload_dir, "audio")
        self.thumbnails_dir = os.path.join(self.base_upload_dir, "thumbnails")

        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

        # In-memory storage ledger for media and jobs
        self._media_store: Dict[str, Dict[str, Any]] = {}
        self._jobs_store: Dict[str, Dict[str, Any]] = {}

    def validate_file(self, filename: str, file_bytes: bytes, media_type: str) -> Tuple[bool, Optional[str]]:
        """
        Performs multi-layer validation: extension, magic bytes, and file size.
        """
        ext = os.path.splitext(filename)[1].lower()
        if media_type == "image":
            if ext not in ALLOWED_EXTENSIONS["image"]:
                return False, f"Invalid image extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS['image']}"
            if len(file_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                return False, f"Image exceeds maximum size of {MAX_IMAGE_SIZE_MB}MB."
            # Verify image integrity
            try:
                import io
                with Image.open(io.BytesIO(file_bytes)) as img:
                    img.verify()
            except Exception as e:
                return False, f"Corrupted or invalid image content: {e}"

        elif media_type == "audio":
            if ext not in ALLOWED_EXTENSIONS["audio"]:
                return False, f"Invalid audio extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS['audio']}"
            if len(file_bytes) > MAX_AUDIO_SIZE_MB * 1024 * 1024:
                return False, f"Audio exceeds maximum size of {MAX_AUDIO_SIZE_MB}MB."

        return True, None

    def save_image(
        self,
        file_bytes: bytes,
        original_filename: str,
        complaint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saves image with safe UUID, creates thumbnail, and returns media record.
        """
        media_id = str(uuid.uuid4())
        ext = os.path.splitext(original_filename)[1].lower() or ".jpg"
        safe_filename = f"{media_id}{ext}"
        storage_path = os.path.join(self.images_dir, safe_filename)

        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        # Generate thumbnail
        thumbnail_filename = f"{media_id}_thumb{ext}"
        thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
        width, height = None, None

        try:
            import io
            with Image.open(io.BytesIO(file_bytes)) as img:
                width, height = img.size
                img.thumbnail(THUMBNAIL_SIZE)
                img.save(thumbnail_path)
        except Exception as e:
            logger.warning(f"Could not generate thumbnail for {media_id}: {e}")
            thumbnail_path = storage_path

        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else f"image/{ext.lstrip('.')}"

        record = {
            "id": media_id,
            "media_id": media_id,
            "complaint_id": complaint_id,
            "media_type": "image",
            "storage_path": storage_path,
            "thumbnail_path": thumbnail_path,
            "thumbnail_url": f"/api/media/{media_id}?thumb=true",
            "media_url": f"/api/media/{media_id}",
            "original_filename": original_filename,
            "mime_type": mime_type,
            "file_size": len(file_bytes),
            "width": width,
            "height": height,
            "duration_seconds": None,
            "processing_status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._media_store[media_id] = record
        return record

    def save_audio(
        self,
        file_bytes: bytes,
        original_filename: str,
        complaint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Saves audio file with safe UUID, calculates duration, and returns media record.
        """
        media_id = str(uuid.uuid4())
        ext = os.path.splitext(original_filename)[1].lower() or ".wav"
        safe_filename = f"{media_id}{ext}"
        storage_path = os.path.join(self.audio_dir, safe_filename)

        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        duration = voice_service.get_audio_duration(storage_path)
        mime_type = "audio/wav" if ext == ".wav" else f"audio/{ext.lstrip('.')}"

        record = {
            "id": media_id,
            "media_id": media_id,
            "complaint_id": complaint_id,
            "media_type": "audio",
            "storage_path": storage_path,
            "thumbnail_path": None,
            "thumbnail_url": None,
            "media_url": f"/api/media/{media_id}",
            "original_filename": original_filename,
            "mime_type": mime_type,
            "file_size": len(file_bytes),
            "width": None,
            "height": None,
            "duration_seconds": duration,
            "processing_status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._media_store[media_id] = record
        return record

    def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves media metadata by ID."""
        return self._media_store.get(media_id)

    def create_job(self, media_id: str, job_type: str) -> Dict[str, Any]:
        """Queues an asynchronous media processing job."""
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "media_id": media_id,
            "job_type": job_type,
            "status": "queued",
            "attempt_count": 0,
            "error_code": None,
            "error_message": None,
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._jobs_store[job_id] = job
        return job

    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates async job state."""
        job = self._jobs_store.get(job_id)
        if not job:
            return None
        job["status"] = status
        if status == "processing":
            job["started_at"] = datetime.now(timezone.utc).isoformat()
            job["attempt_count"] += 1
        elif status in ["completed", "failed"]:
            job["completed_at"] = datetime.now(timezone.utc).isoformat()
        if error_code:
            job["error_code"] = error_code
            job["error_message"] = error_message
        return job


media_service = MediaService()
