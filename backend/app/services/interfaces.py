"""
CivicMind AI — AI Service Abstract Interfaces
Module 2 will provide real implementations replacing the mock ones.
These interfaces must NOT change between modules — the frontend depends on them.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class LanguageInfo:
    primary_language: str
    language_name: str
    languages: list[str]
    script: str
    is_code_mixed: bool
    confidence: float


@dataclass
class ClassificationResult:
    is_grievance: bool
    category: str
    subcategory: Optional[str]
    severity: str
    priority: str
    confidence: float
    explanation: str


@dataclass
class EntityExtractionResult:
    entities: dict[str, Any]
    duration_mentioned: Optional[str]
    location_mentions: list[str]
    ward_mentions: list[str]


@dataclass
class RoutingResult:
    department_code: str
    department_name: str
    reason: str


@dataclass
class EmbeddingResult:
    embedding: list[float]
    model: str
    dimensions: int


class LanguageDetector(ABC):
    """Detect language and script of input text."""

    @abstractmethod
    async def detect(self, text: str) -> LanguageInfo:
        """Detect language metadata from input text."""
        ...

    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if the service is initialized and ready."""
        ...


class GrievanceClassifier(ABC):
    """Classify whether text is a grievance and determine its category/priority."""

    @abstractmethod
    async def classify(self, text: str, language_info: LanguageInfo) -> ClassificationResult:
        """Classify the grievance text."""
        ...

    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if classifier is ready."""
        ...


class CategoryClassifier(ABC):
    """Specialized category classifier (may be separate model in Module 2)."""

    @abstractmethod
    async def classify_category(self, text: str, language: str) -> tuple[str, str]:
        """Returns (category, subcategory)."""
        ...


class PriorityClassifier(ABC):
    """Priority level classifier."""

    @abstractmethod
    async def classify_priority(self, text: str, category: str, duration: Optional[str]) -> tuple[str, float]:
        """Returns (priority_level, confidence)."""
        ...


class EntityExtractor(ABC):
    """Extract named entities from grievance text."""

    @abstractmethod
    async def extract(self, text: str, language: str) -> EntityExtractionResult:
        """Extract entities from text."""
        ...


class EmbeddingService(ABC):
    """Generate multilingual semantic embeddings using MuRIL."""

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for the given text."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        ...

    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if embedding model is loaded."""
        ...
