"""
CivicMind AI — Human-in-the-Loop Review Policy
Configures operational routing triage thresholds:
- AUTO_ROUTE: high confidence direct dispatch
- OFFICER_REVIEW: moderate confidence or multi-issue triage
- MANUAL_REVIEW: low confidence or ambiguous complaints
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ReviewPolicyConfig:
    """Configurable confidence thresholds for automated dispatch."""
    auto_route_threshold: float = 0.80      # >= 0.80 -> AUTO_ROUTE
    officer_review_threshold: float = 0.55  # >= 0.55 and < 0.80 -> OFFICER_REVIEW
    # < 0.55 -> MANUAL_REVIEW

    version: str = "review-policy-v1.0"

    def evaluate_decision(
        self,
        routing_confidence: float,
        is_compound_multi_issue: bool = False,
        is_immediate_hazard: bool = False,
    ) -> tuple[str, bool]:
        """
        Returns: (decision_string, requires_human_review_bool)
        Decisions: "AUTO_ROUTE", "OFFICER_REVIEW", "MANUAL_REVIEW"
        """
        # Life-safety hazards are fast-tracked directly to emergency field operations
        if is_immediate_hazard:
            return "AUTO_ROUTE", False

        # Multi-issue complaints need triage officer verification if confidence isn't exceptionally high
        if is_compound_multi_issue and routing_confidence < 0.90:
            return "OFFICER_REVIEW", True

        if routing_confidence >= self.auto_route_threshold:
            return "AUTO_ROUTE", False
        elif routing_confidence >= self.officer_review_threshold:
            return "OFFICER_REVIEW", True
        else:
            return "MANUAL_REVIEW", True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "auto_route_threshold": self.auto_route_threshold,
            "officer_review_threshold": self.officer_review_threshold,
        }


from enum import Enum


class ReviewDecision(str, Enum):
    AUTO_ROUTE = "AUTO_ROUTE"
    OFFICER_REVIEW = "OFFICER_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"


@dataclass
class ReviewDecisionResult:
    decision: ReviewDecision
    requires_human_review: bool
    reason: str = ""


# Global singleton
review_policy = ReviewPolicyConfig()


def evaluate_review_decision(
    routing_confidence: float,
    priority: str = "medium",
    is_safety_hazard: bool = False,
    is_compound_multi_issue: bool = False,
) -> ReviewDecisionResult:
    dec_str, req_review = review_policy.evaluate_decision(
        routing_confidence=routing_confidence,
        is_compound_multi_issue=is_compound_multi_issue,
        is_immediate_hazard=is_safety_hazard,
    )
    return ReviewDecisionResult(
        decision=ReviewDecision(dec_str),
        requires_human_review=req_review,
        reason=f"Routing confidence {routing_confidence*100:.1f}% maps to {dec_str}",
    )

