"""
CivicMind AI — Language Detection Service
Wraps AI4Bharat IndicLID for multilingual language identification.

IndicLID capabilities:
- Identifies 47 Indian languages
- Detects native script vs Romanized script
- Handles code-mixed text

Architecture:
    Input → IndicLID → LanguageInfo → MuRIL
"""
import asyncio
import logging
from typing import Optional

from app.services.interfaces import LanguageDetector, LanguageInfo

logger = logging.getLogger(__name__)

# Language code → human-readable name
LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "bn": "Bengali",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "sa": "Sanskrit",
    "unknown": "Unknown",
}

# IndicLID returns labels like "ta_Taml" (lang_Script)
def _parse_indiclid_label(label: str) -> tuple[str, str]:
    """Parse 'ta_Taml' → ('ta', 'native') or 'en_Latn' → ('en', 'roman')."""
    parts = label.split("_")
    if len(parts) >= 2:
        lang = parts[0].lower()
        script_code = parts[1].lower() if len(parts) > 1 else "latn"
        script = "roman" if "latn" in script_code else "native"
        return lang, script
    return label.lower(), "roman"


class LanguageDetectionService(LanguageDetector):
    """
    Wraps AI4Bharat IndicLID for language + script identification.
    Falls back to a simple heuristic if IndicLID is not installed.
    """

    def __init__(self):
        self._model = None
        self._initialized = False
        self._indiclid_available = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._initialize_sync)

    def _initialize_sync(self) -> None:
        try:
            from IndicLID import IndicLID
            logger.info("Loading IndicLID model...")
            self._model = IndicLID(input_iso="iso")
            self._indiclid_available = True
            logger.info("IndicLID initialized successfully")
        except ImportError:
            logger.warning(
                "ai4bharat-indiclid not installed. Using fallback heuristic language detection. "
                "Install with: pip install ai4bharat-indiclid"
            )
            self._indiclid_available = False
        except Exception as e:
            logger.error(f"IndicLID initialization error: {e}")
            self._indiclid_available = False
        finally:
            self._initialized = True

    async def detect(self, text: str) -> LanguageInfo:
        if not self._initialized:
            await self.initialize()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._detect_sync, text)

    def _detect_sync(self, text: str) -> LanguageInfo:
        if self._indiclid_available and self._model is not None:
            return self._detect_with_indiclid(text)
        return self._detect_with_heuristic(text)

    def _detect_with_indiclid(self, text: str) -> LanguageInfo:
        """Use real IndicLID model."""
        try:
            result = self._model.batch_predict([text], 32)
            # result is list of (text, label, confidence)
            if result and len(result) > 0:
                _, label, confidence = result[0]
                primary_lang, script = _parse_indiclid_label(label)

                # For code-mixed text, IndicLID may identify multiple languages
                # Simple code-mix detection: if roman script with non-latin characters
                is_code_mixed = self._check_code_mixed(text, primary_lang, script)

                languages = [primary_lang]
                if is_code_mixed:
                    # Add English as secondary if primary is non-English roman
                    if primary_lang != "en":
                        languages.append("en")
                    elif primary_lang == "en":
                        languages.append("ta")  # heuristic for Tanglish

                return LanguageInfo(
                    primary_language=primary_lang,
                    language_name=LANGUAGE_NAMES.get(primary_lang, primary_lang.upper()),
                    languages=languages,
                    script=script,
                    is_code_mixed=is_code_mixed,
                    confidence=float(confidence) if confidence else 0.85,
                )
        except Exception as e:
            logger.error(f"IndicLID inference error: {e}")
            return self._detect_with_heuristic(text)

    def _detect_with_heuristic(self, text: str) -> LanguageInfo:
        """
        Lightweight heuristic fallback when IndicLID is unavailable.
        Checks Unicode character ranges to identify script.
        """
        import unicodedata

        tamil_chars = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
        devanagari_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_alpha = tamil_chars + devanagari_chars + latin_chars

        if total_alpha == 0:
            return LanguageInfo("en", "English", ["en"], "roman", False, 0.5)

        if tamil_chars > 0 and latin_chars > 0:
            # Tamil + Latin = code-mixed Tamil-English
            return LanguageInfo("ta", "Tamil", ["ta", "en"], "roman", True, 0.75)
        elif tamil_chars > total_alpha * 0.5:
            return LanguageInfo("ta", "Tamil", ["ta"], "native", False, 0.85)
        elif devanagari_chars > 0 and latin_chars > 0:
            return LanguageInfo("hi", "Hindi", ["hi", "en"], "roman", True, 0.75)
        elif devanagari_chars > total_alpha * 0.5:
            return LanguageInfo("hi", "Hindi", ["hi"], "native", False, 0.85)
        else:
            # All Roman — could be English, Tanglish, or Hinglish
            # Simple keyword heuristic
            tanglish_words = {"varala", "vanthu", "pora", "naala", "thanni", "anna"}
            hinglish_words = {"nahi", "karke", "wala", "hain", "karo", "bohot"}
            lower_text = text.lower()
            has_tanglish = any(w in lower_text for w in tanglish_words)
            has_hinglish = any(w in lower_text for w in hinglish_words)

            if has_tanglish:
                return LanguageInfo("ta", "Tamil", ["ta", "en"], "roman", True, 0.7)
            elif has_hinglish:
                return LanguageInfo("hi", "Hindi", ["hi", "en"], "roman", True, 0.7)
            else:
                return LanguageInfo("en", "English", ["en"], "roman", False, 0.8)

    def _check_code_mixed(self, text: str, primary_lang: str, script: str) -> bool:
        """Detect code-mixing by checking for multiple scripts in text."""
        tamil_chars = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
        devanagari_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())

        non_zero = sum([tamil_chars > 0, devanagari_chars > 0, latin_chars > 0])
        return non_zero >= 2

    async def is_ready(self) -> bool:
        return self._initialized

    def get_status(self) -> dict:
        return {
            "initialized": self._initialized,
            "indiclid_available": self._indiclid_available,
            "backend": "IndicLID" if self._indiclid_available else "heuristic_fallback",
        }


# Singleton
language_detection_service = LanguageDetectionService()
