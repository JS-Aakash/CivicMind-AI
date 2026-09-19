"""
CivicMind AI — Configurable Priority Policy & Weight Configuration
Defines configurable weights, contribution functions, and score thresholds for civic triage.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class PriorityWeightsConfig:
    """Configurable weights for the multi-signal priority scoring engine."""
    neural_signal: float = 1.0
    safety_hazard: float = 1.6
    duration: float = 0.9
    population_scope: float = 1.0
    vulnerable_population: float = 1.2
    critical_infrastructure: float = 1.1
    emergency_indicator: float = 1.5
    location_vulnerability: float = 0.8

    def to_dict(self) -> Dict[str, float]:
        return {
            "neural_signal": self.neural_signal,
            "safety_hazard": self.safety_hazard,
            "duration": self.duration,
            "population_scope": self.population_scope,
            "vulnerable_population": self.vulnerable_population,
            "critical_infrastructure": self.critical_infrastructure,
            "emergency_indicator": self.emergency_indicator,
            "location_vulnerability": self.location_vulnerability,
        }


@dataclass
class PriorityThresholdsConfig:
    """Threshold boundaries for mapping composite scores into discrete priority levels."""
    # Composite score ranges: [0.0 to 10.0]
    critical_threshold: float = 7.0
    high_threshold: float = 4.5
    medium_threshold: float = 2.2
    # < medium_threshold -> low

    def score_to_priority(self, score: float) -> str:
        if score >= self.critical_threshold:
            return "critical"
        elif score >= self.high_threshold:
            return "high"
        elif score >= self.medium_threshold:
            return "medium"
        return "low"


class PriorityPolicy:
    """Singleton priority policy manager."""
    def __init__(
        self,
        weights: PriorityWeightsConfig = PriorityWeightsConfig(),
        thresholds: PriorityThresholdsConfig = PriorityThresholdsConfig(),
        version: str = "priority-v1.0",
    ):
        self.weights = weights
        self.thresholds = thresholds
        self.version = version

    def get_config(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "weights": self.weights.to_dict(),
            "thresholds": {
                "critical": self.thresholds.critical_threshold,
                "high": self.thresholds.high_threshold,
                "medium": self.thresholds.medium_threshold,
            },
        }


# Global singleton policy instance
priority_policy = PriorityPolicy()
