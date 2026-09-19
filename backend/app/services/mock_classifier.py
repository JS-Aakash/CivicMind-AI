"""
CivicMind AI — Mock Classifier
Implements all AI service interfaces with rule-based demo logic.
Module 2 will replace these with real fine-tuned MuRIL classifiers.

IMPORTANT: These are clearly labeled as MOCK/DEMO.
Do NOT treat these as real ML predictions.
"""
import re
import logging
from typing import Optional

from app.services.interfaces import (
    GrievanceClassifier, CategoryClassifier, PriorityClassifier,
    EntityExtractor, ClassificationResult, EntityExtractionResult, LanguageInfo
)

logger = logging.getLogger(__name__)

# ─── Category keywords (multilingual) ───────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "water": [
        "water", "thanni", "jal", "paani", "pani", "supply", "varala",
        "குடிநீர்", "தண்ணீர்", "पानी", "जल", "நீர்",
    ],
    "roads": [
        "road", "pothole", "street", "pavement", "tarmac", "சாலை",
        "रोड", "गड्ढा", "saalai", "road",
    ],
    "electricity": [
        "electricity", "power", "light", "current", "மின்சாரம்", "விளக்கு",
        "बिजली", "करंट", "current", "power cut", "blackout",
    ],
    "sanitation": [
        "garbage", "waste", "dustbin", "clean", "dirt", "smell", "குப்பை",
        "कचरा", "swachh", "sewage",
    ],
    "drainage": [
        "drain", "flood", "waterlogging", "sewage", "overflow", "வடிகால்",
        "नाला", "naala", "sewer",
    ],
    "transport": [
        "bus", "auto", "metro", "train", "route", "பஸ்", "बस", "metro",
    ],
    "healthcare": [
        "hospital", "medicine", "doctor", "health", "disease", "மருத்துவமனை",
        "अस्पताल", "दवाई",
    ],
    "public_safety": [
        "safety", "danger", "crime", "police", "accident", "பாதுகாப்பு",
        "सुरक्षा", "police",
    ],
}

PRIORITY_SIGNALS: dict[str, list[str]] = {
    "critical": [
        "emergency", "urgent", "immediate", "danger", "fire", "flood",
        "accident", "death", "life", "days", "week",
    ],
    "high": [
        "no water", "no electricity", "power cut", "broken", "days", "naala",
        "thanni varala", "3 days", "pani nahi",
    ],
    "medium": [
        "problem", "issue", "repair", "fix", "improve",
    ],
    "low": [
        "request", "suggest", "inform", "kindly",
    ],
}

ENTITY_PATTERNS = {
    "duration": [
        r"(\d+)\s*(day|days|week|weeks|month|months|hour|hours|naala|naal|din|ghante)",
        r"(three|two|four|five|oru|randu|moonu|naalu)\s*(day|days|naal|naala|din)",
    ],
    "ward": [
        r"ward\s*(\d+)",
        r"block\s*(\w+)",
    ],
    "location": [
        r"(street|road|nagar|colony|layout|cross|main)\s+\w+",
    ],
}


class MockGrievanceClassifier(GrievanceClassifier):
    """
    DEMO-ONLY: Rule-based grievance classifier.
    Returns structured predictions based on keyword matching.
    Will be replaced by fine-tuned MuRIL in Module 2.
    """

    async def classify(self, text: str, language_info: LanguageInfo) -> ClassificationResult:
        text_lower = text.lower()

        # Determine category
        category, confidence_boost = self._get_category(text_lower)
        priority = self._get_priority(text_lower, category)
        severity = self._priority_to_severity(priority)

        # Base confidence — mock values
        confidence = 0.72 + confidence_boost + (0.05 if language_info.is_code_mixed else 0.0)
        confidence = min(confidence, 0.97)

        explanation = self._build_explanation(text, category, priority, language_info)

        return ClassificationResult(
            is_grievance=True,
            category=category,
            subcategory=self._get_subcategory(category, text_lower),
            severity=severity,
            priority=priority,
            confidence=round(confidence, 3),
            explanation=explanation,
        )

    def _get_category(self, text: str) -> tuple[str, float]:
        best_cat = "general"
        best_score = 0
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > best_score:
                best_score = score
                best_cat = cat
        return best_cat, min(best_score * 0.03, 0.15)

    def _get_priority(self, text: str, category: str) -> str:
        for priority, signals in PRIORITY_SIGNALS.items():
            if any(sig.lower() in text for sig in signals):
                return priority
        # Category-based defaults
        defaults = {"water": "high", "electricity": "high", "public_safety": "critical"}
        return defaults.get(category, "medium")

    def _priority_to_severity(self, priority: str) -> str:
        return {"critical": "severe", "high": "major", "medium": "moderate", "low": "minor"}.get(priority, "moderate")

    def _get_subcategory(self, category: str, text: str) -> Optional[str]:
        subcats = {
            "water": {"supply": "supply_disruption", "quality": "quality_issue", "leak": "pipe_leak"},
            "electricity": {"cut": "power_outage", "fault": "equipment_fault"},
            "roads": {"pothole": "pothole", "light": "street_lighting"},
        }
        if category in subcats:
            for kw, sub in subcats[category].items():
                if kw in text:
                    return sub
        return None

    def _build_explanation(self, text: str, category: str, priority: str, lang: LanguageInfo) -> str:
        lang_desc = f"{lang.language_name} ({'code-mixed' if lang.is_code_mixed else 'monolingual'})"
        cat_display = category.replace("_", " ").title()
        return (
            f"[DEMO MODE] Complaint analyzed in {lang_desc}. "
            f"{cat_display} issue detected with {priority.upper()} priority. "
            f"This is a rule-based demonstration — Module 2 will provide real MuRIL predictions."
        )

    async def is_ready(self) -> bool:
        return True


class MockEntityExtractor(EntityExtractor):
    """
    DEMO-ONLY: Regex-based entity extraction.
    Module 2 will use MuRIL NER.
    """

    async def extract(self, text: str, language: str) -> EntityExtractionResult:
        text_lower = text.lower()
        entities: dict = {}
        duration = None
        locations = []
        wards = []

        for entity_type, patterns in ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    if entity_type == "duration":
                        duration = " ".join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
                        entities["duration"] = duration
                    elif entity_type == "ward":
                        wards = [" ".join(m) if isinstance(m, tuple) else m for m in matches]
                        entities["wards"] = wards
                    elif entity_type == "location":
                        locations = [" ".join(m) if isinstance(m, tuple) else m for m in matches]
                        entities["locations"] = locations

        return EntityExtractionResult(
            entities=entities,
            duration_mentioned=duration,
            location_mentions=locations,
            ward_mentions=wards,
        )


# Singleton instances
mock_classifier = MockGrievanceClassifier()
mock_entity_extractor = MockEntityExtractor()
