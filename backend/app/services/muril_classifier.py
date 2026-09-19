"""
CivicMind AI — Production MuRIL Multi-Task Classifier Service (v1.1 Hardened)
Loads and serves the fine-tuned multi-task MuRIL model (v1.1) for real-time inference.
"""
import asyncio
import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
import torch
from transformers import AutoTokenizer

from app.core.config import settings
from app.services.interfaces import GrievanceClassifier, ClassificationResult, LanguageInfo
from app.ml.model import MuRILMultiTaskForCivic
from app.ml.taxonomy import CATEGORIES

logger = logging.getLogger(__name__)


class MuRILClassifierService(GrievanceClassifier):
    """
    Production service hosting the fine-tuned multi-task MuRIL neural model.
    Cached in memory, non-blocking asynchronous inference with batching support.
    """

    def __init__(self, model_dir: Optional[str] = None):
        self._custom_model_dir = Path(model_dir) if model_dir else None
        self.model: Optional[MuRILMultiTaskForCivic] = None
        self.tokenizer = None
        self.device = None
        self._initialized = False
        self._lock = asyncio.Lock()

    @property
    def model_dir(self) -> Path:
        if self._custom_model_dir:
            return self._custom_model_dir
        return settings.trained_model_dir

    @property
    def is_trained_model_available(self) -> bool:
        """Check if model checkpoint exists on disk."""
        md = self.model_dir
        return (
            md.exists()
            and (md / "config.json").exists()
            and (md / "heads.pt").exists()
        )

    async def initialize(self) -> None:
        """Load trained model into memory (cached)."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            if not self.is_trained_model_available:
                logger.warning(f"Trained model not found at {self.model_dir}. Please run training script first.")
                return

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_sync)
            self._initialized = True

    def _load_sync(self) -> None:
        """Synchronous model loading into GPU or CPU."""
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            logger.info("Loading trained MuRIL model onto CUDA GPU")
        else:
            self.device = torch.device("cpu")
            logger.info("Loading trained MuRIL model onto CPU")

        logger.info(f"Loading MuRIL classifier from {self.model_dir}...")
        self.model = MuRILMultiTaskForCivic.from_pretrained(self.model_dir)
        self.model.to(self.device)
        self.model.eval()

        tok_dir = self.model_dir / "encoder"
        if tok_dir.exists():
            self.tokenizer = AutoTokenizer.from_pretrained(str(tok_dir))
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(settings.MURIL_LOCAL_PATH)

        logger.info(f"MuRIL trained classifier loaded successfully from {self.model_dir}")

    async def is_ready(self) -> bool:
        return self._initialized and self.model is not None

    async def classify(self, text: str, language_info: LanguageInfo) -> ClassificationResult:
        """Classify a single grievance text with real model prediction."""
        if not self._initialized:
            await self.initialize()

        if not self.model:
            raise RuntimeError(
                f"Trained MuRIL model is not ready. Ensure model exists in {self.model_dir} "
                "or switch AI_MODE=demo in configuration."
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._classify_sync, text, language_info)

    def _classify_sync(self, text: str, language_info: LanguageInfo) -> ClassificationResult:
        enc = self.tokenizer(
            text,
            max_length=128,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc["attention_mask"].to(self.device)

        preds = self.model.predict(input_ids, attention_mask, top_k=4)
        pred = preds[0]

        # Guardrail: Check for conversational greetings
        if self._is_conversational_greeting(text):
            pred["is_grievance"] = False
            pred["category"] = "other"
            pred["subcategory"] = "general_inquiry"
            pred["priority"] = "low"
            pred["severity"] = "low"
            pred["category_probabilities"] = {"other": 0.85, **{k: v for k, v in pred.get("category_probabilities", {}).items() if k != "other"}}

        elif not pred["is_grievance"]:
            # Procedural inquiry under a department (e.g. "What is water helpline?")
            pred["priority"] = "low"
            pred["severity"] = "low"

        # Construct explainable evidence based on linguistic signals & probabilities
        explanation = self._build_evidence_explanation(text, pred, language_info)

        return ClassificationResult(
            is_grievance=pred["is_grievance"],
            category=pred["category"],
            subcategory=pred["subcategory"],
            severity=pred["severity"],
            priority=pred["priority"],
            confidence=pred["confidence"],
            explanation=explanation,
        )

    def _is_conversational_greeting(self, text: str) -> bool:
        """Detects single-word greetings, salutations, or pleasantries without civic fault claims."""
        if not text or not text.strip():
            return False
        t = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE).strip().lower()
        collapsed = re.sub(r"(.)\1{2,}", r"\1", t)
        common_greetings = {
            "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
            "namaste", "vanakkam", "kaise ho", "eppadi irukkeenga", "thanks", "thank you",
            "ok", "okay", "test", "testing"
        }
        words = collapsed.split()
        if not words or len(words) > 3:
            return False
        if collapsed in common_greetings or all(w in common_greetings for w in words):
            return True
        return False

    def _build_evidence_explanation(self, text: str, pred: Dict[str, Any], lang: LanguageInfo) -> str:
        """Builds factual, transparent evidence reasoning without generative hallucinations."""
        cat = pred["category"]
        prio = pred["priority"].upper()
        top_cats = ", ".join(f"{k} ({v*100:.1f}%)" for k, v in pred.get("category_probabilities", {}).items())
        script_info = f"{lang.language_name} ({lang.script} script, code-mixed)" if lang.is_code_mixed else f"{lang.language_name} ({lang.script} script)"

        if not pred["is_grievance"]:
            if cat == "other":
                return (
                    f"Classified as non-actionable greeting / inquiry ({pred['grievance_confidence']*100:.1f}% non-grievance confidence). "
                    f"Linguistic context: {script_info}. No physical civic breakdown reported. "
                    f"Evaluated by MuRIL multi-task neural model (v1.1)."
                )
            else:
                return (
                    f"Classified as informational inquiry related to {cat.upper()} ({pred['category_confidence']*100:.1f}% category confidence). "
                    f"Priority set to LOW for administrative triage. Linguistic context: {script_info}. "
                    f"Evaluated by MuRIL multi-task neural model (v1.1)."
                )

        if cat == "other":
            return (
                f"Low classification confidence ({pred['category_confidence']*100:.1f}%) across civic categories. "
                f"Linguistic context: {script_info}. Routed to General Grievance Cell for manual triage. "
                f"Evaluated by MuRIL multi-task neural model (v1.1)."
            )

        return (
            f"Classified under {cat.upper()} with {pred['category_confidence']*100:.1f}% confidence and {prio} priority. "
            f"Language profile: {script_info}. Category probability distribution: {top_cats}. "
            f"Evaluated by MuRIL multi-task neural model (v1.1)."
        )

    def predict_detailed(self, text: str, language_info: LanguageInfo) -> Dict[str, Any]:
        """Provides full structured probabilities and task-specific confidences."""
        if not self._initialized:
            self._load_sync()
            self._initialized = True

        enc = self.tokenizer(
            text,
            max_length=128,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc["attention_mask"].to(self.device)

        preds = self.model.predict(input_ids, attention_mask, top_k=4)
        pred = preds[0]

        # Guardrail: Check for conversational greetings
        if self._is_conversational_greeting(text):
            pred["is_grievance"] = False
            pred["category"] = "other"
            pred["subcategory"] = "general_inquiry"
            pred["priority"] = "low"
            pred["severity"] = "low"
            pred["category_probabilities"] = {"other": 0.85, **{k: v for k, v in pred.get("category_probabilities", {}).items() if k != "other"}}

        elif not pred["is_grievance"]:
            pred["priority"] = "low"
            pred["severity"] = "low"

        pred["explanation"] = self._build_evidence_explanation(text, pred, language_info)
        return pred

    def get_embedding(self, text: str) -> list[float]:
        """
        Extract 768-dimensional normalized L2 semantic embedding vector.
        Uses shared MuRIL encoder [CLS] representation.
        """
        return self.get_embeddings_batch([text])[0]

    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Batch extraction of 768-dimensional normalized semantic embeddings.
        """
        if not texts:
            return []

        if not self._initialized:
            self._load_sync()
            self._initialized = True

        if self.model and self.tokenizer and self.device:
            import torch.nn.functional as F
            enc = self.tokenizer(
                texts,
                max_length=128,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            input_ids = enc["input_ids"].to(self.device)
            attention_mask = enc["attention_mask"].to(self.device)

            with torch.no_grad():
                out = self.model(input_ids, attention_mask)
                cls_rep = out["cls_embedding"]
                # L2 normalize
                normed = F.normalize(cls_rep, p=2, dim=1)
                return normed.cpu().numpy().tolist()

        # Fallback deterministic pseudo-embedding (768-dim) if weights not loaded
        import hashlib
        import numpy as np
        embeddings = []
        for t in texts:
            clean = t.strip().lower()
            vec = np.zeros(768, dtype=np.float32)
            # Hash character n-grams and tokens into the 768-dim space
            words = clean.split()
            for w in words:
                idx = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % 768
                vec[idx] += 1.0
            for i in range(len(clean) - 2):
                tri = clean[i:i+3]
                idx = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16) % 768
                vec[idx] += 0.5
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        return embeddings


# Singleton instance
muril_classifier_service = MuRILClassifierService()
