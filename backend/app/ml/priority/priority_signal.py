"""
CivicMind AI — Priority Signal Contract
Clean typed dataclass providing structured signals for Module 3 intelligent routing & escalation.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ExtractedCivicEntities:
    """Entities extracted deterministically / via lightweight rules."""
    duration_days: Optional[int] = None
    affected_count: Optional[int] = None
    safety_hazard: bool = False
    vulnerable_impact: bool = False  # e.g., hospital, school, elderly
    location_mentions: List[str] = field(default_factory=list)
    hazard_types: List[str] = field(default_factory=list)


@dataclass
class PrioritySignal:
    """
    Standardized payload passed to Module 3 (SLA, Routing, and Auto-Escalation Engine).
    Combines MuRIL v1.1 calibrated neural predictions with rule-based safety flags.
    """
    # Core Classification (required fields first)
    is_grievance: bool
    grievance_type: str  # grievance, info_request, greeting, etc.
    primary_category: str
    primary_subcategory: str
    model_severity: str  # low, medium, high, critical
    model_priority: str  # low, medium, high, critical

    # Optional / defaulted fields
    secondary_issues: List[str] = field(default_factory=list)
    confidence: float = 0.0
    calibrated_confidence: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    category_distribution: Dict[str, float] = field(default_factory=dict)

    # Extracted Evidence & Context
    entities: ExtractedCivicEntities = field(default_factory=ExtractedCivicEntities)
    
    # Actionable Routing Signals for Module 3
    is_safety_critical: bool = False
    recommended_escalation: bool = False
    escalation_reasons: List[str] = field(default_factory=list)
    suggested_sla_hours: int = 48
    
    # Metadata
    model_version: str = "muril-multitask-v1.1"
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_grievance": self.is_grievance,
            "grievance_type": self.grievance_type,
            "primary_category": self.primary_category,
            "primary_subcategory": self.primary_subcategory,
            "secondary_issues": self.secondary_issues,
            "model_severity": self.model_severity,
            "model_priority": self.model_priority,
            "confidence": self.confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "confidence_breakdown": self.confidence_breakdown,
            "category_distribution": self.category_distribution,
            "entities": {
                "duration_days": self.entities.duration_days,
                "affected_count": self.entities.affected_count,
                "safety_hazard": self.entities.safety_hazard,
                "vulnerable_impact": self.entities.vulnerable_impact,
                "location_mentions": self.entities.location_mentions,
                "hazard_types": self.entities.hazard_types,
            },
            "is_safety_critical": self.is_safety_critical,
            "recommended_escalation": self.recommended_escalation,
            "escalation_reasons": self.escalation_reasons,
            "suggested_sla_hours": self.suggested_sla_hours,
            "model_version": self.model_version,
            "language": self.language,
        }
