"""
CivicMind AI — MuRIL Service
Downloads, caches, and loads google/muril-base-cased locally.
Provides multilingual embeddings and inference interface.

Module 2 will fine-tune MuRIL and replace the inference logic.
This module only proves MuRIL can be loaded and used locally.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
import time

from app.core.config import settings
from app.services.interfaces import EmbeddingService, EmbeddingResult

logger = logging.getLogger(__name__)

# Lazy imports — don't fail on startup if torch is not installed
_torch = None
_transformers = None


def _ensure_torch():
    global _torch, _transformers
    if _torch is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            _torch = torch
            _transformers = (AutoTokenizer, AutoModel)
        except ImportError as e:
            raise RuntimeError(f"PyTorch/Transformers not installed: {e}")
    return _torch, _transformers


class MuRILService(EmbeddingService):
    """
    Manages the local MuRIL model lifecycle:
    1. Check if model exists locally
    2. Download from HuggingFace Hub if missing
    3. Load tokenizer + model
    4. Expose embedding interface
    """

    def __init__(self):
        self._tokenizer = None
        self._model = None
        self._device = None
        self._initialized = False
        self._model_path = settings.muril_path
        self._model_name = settings.MURIL_MODEL_NAME

    @property
    def is_downloaded(self) -> bool:
        """Check if MuRIL exists on disk."""
        return (
            self._model_path.exists()
            and (self._model_path / "config.json").exists()
            and (self._model_path / "tokenizer_config.json").exists()
        )

    @property
    def model_size_mb(self) -> Optional[float]:
        """Approximate size of cached model in MB."""
        if not self._model_path.exists():
            return None
        total_bytes = sum(
            f.stat().st_size for f in self._model_path.rglob("*") if f.is_file()
        )
        return round(total_bytes / (1024 * 1024), 1)

    async def initialize(self) -> None:
        """Initialize MuRIL — download if needed, then load."""
        if self._initialized:
            return

        logger.info(f"Initializing MuRIL service | local path: {self._model_path}")

        # Run blocking I/O in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._initialize_sync)

    def _initialize_sync(self) -> None:
        """Synchronous initialization — download + load model."""
        torch, (AutoTokenizer, AutoModel) = _ensure_torch()

        # Select device
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
            logger.info("MuRIL using GPU (CUDA)")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self._device = torch.device("mps")
            logger.info("MuRIL using Apple Silicon (MPS)")
        else:
            self._device = torch.device("cpu")
            logger.info("MuRIL using CPU")

        # Download if not cached locally
        if not self.is_downloaded:
            logger.info(f"MuRIL not found locally — downloading {self._model_name} to {self._model_path}")
            self._download_model(AutoTokenizer, AutoModel)
        else:
            logger.info(f"MuRIL found locally at {self._model_path} ({self.model_size_mb} MB)")

        # Load from local path
        logger.info("Loading MuRIL tokenizer...")
        self._tokenizer = AutoTokenizer.from_pretrained(
            str(self._model_path), local_files_only=True
        )

        logger.info("Loading MuRIL model...")
        t0 = time.time()
        self._model = AutoModel.from_pretrained(
            str(self._model_path), local_files_only=True
        )
        self._model.to(self._device)
        self._model.eval()
        elapsed = time.time() - t0
        logger.info(f"MuRIL model loaded in {elapsed:.2f}s")

        self._initialized = True

    def _download_model(self, AutoTokenizer, AutoModel) -> None:
        """Download MuRIL from HuggingFace Hub."""
        self._model_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading tokenizer: {self._model_name}")
        tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        tokenizer.save_pretrained(str(self._model_path))

        logger.info(f"Downloading model: {self._model_name} (~900MB, please wait...)")
        model = AutoModel.from_pretrained(self._model_name)
        model.save_pretrained(str(self._model_path))
        logger.info(f"MuRIL downloaded and saved to {self._model_path}")

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate [CLS] token embedding for input text."""
        if not self._initialized:
            await self.initialize()

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self._embed_sync, text)
        return EmbeddingResult(
            embedding=embedding,
            model=self._model_name,
            dimensions=len(embedding),
        )

    def _embed_sync(self, text: str) -> list[float]:
        """Synchronous embedding generation."""
        torch, _ = _ensure_torch()
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True,
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            # Use [CLS] token representation
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            embedding = cls_embedding.squeeze().cpu().numpy().tolist()

        return embedding

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        results = []
        for text in texts:
            result = await self.embed(text)
            results.append(result)
        return results

    async def is_ready(self) -> bool:
        return self._initialized and self._model is not None

    def get_status(self) -> dict:
        """Return current model status for the API."""
        return {
            "downloaded": self.is_downloaded,
            "loaded": self._initialized,
            "device": str(self._device) if self._device else "not loaded",
            "local_path": str(self._model_path),
            "size_mb": self.model_size_mb,
            "model_name": self._model_name,
        }


# Singleton instance
muril_service = MuRILService()
