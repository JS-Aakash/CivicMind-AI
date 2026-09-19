"""
CivicMind AI — Explainable Civic Decision & Priority Generator
Produces deterministic, traceable explanations for civic prioritization without generative LLMs.
Answers: WHAT, WHY URGENT, WHO, WHEN, HOW CONFIDENT, and HUMAN REVIEW.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from app.priority.priority_rules import ContextualCivicSignals
from app.priority.safety_policy import SafetyAssessment


@dataclass
class PriorityFactorItem:
    """Individual transparent factor influencing the priority calculation."""
    factor: str  # "safety_hazard", "duration", "affected_population", "vulnerable_population", "neural_baseline", etc.
    label: str   # Display title e.g. "3-Day Duration"
    value: str   # Formatted value e.g. "72 hours"
    impact: str  # "increases_urgency", "critical_escalation", "neutral", "reduces_urgency"
    weight_contribution: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor,
            "label": self.label,
            "value": self.value,
            "impact": self.impact,
            "weight_contribution": round(self.weight_contribution, 2),
            "description": self.description,
        }


@dataclass
class StructuredCivicExplanation:
    """Complete transparent explanation answering all 6 governance questions."""
    summary: str
    what_category_reason: str
    why_urgent_factors: List[PriorityFactorItem] = field(default_factory=list)
    who_department_reason: str = ""
    when_sla_reason: str = ""
    how_confident_reason: str = ""
    human_review_reason: str = ""
    reasoning_mode: str = "hybrid_neural_context"  # "neural_only", "safety_override", "hybrid_neural_context"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "what_category_reason": self.what_category_reason,
            "why_urgent_factors": [f.to_dict() for f in self.why_urgent_factors],
            "who_department_reason": self.who_department_reason,
            "when_sla_reason": self.when_sla_reason,
            "how_confident_reason": self.how_confident_reason,
            "human_review_reason": self.human_review_reason,
            "reasoning_mode": self.reasoning_mode,
        }


class PriorityExplanationGenerator:
    """Deterministic explanation builder."""

    @classmethod
    def generate(
        cls,
        text: str,
        category: str,
        subcategory: Optional[str],
        neural_priority: str,
        neural_prob: float,
        final_priority: str,
        context: ContextualCivicSignals,
        safety: SafetyAssessment,
        department_name: str,
        sla_hours: int,
        routing_confidence: float,
        review_decision: str,
        factors: List[PriorityFactorItem],
    ) -> StructuredCivicExplanation:
        cat_title = category.replace("_", " ").title()
        prio_title = final_priority.upper()

        # 1. Summary statement
        if safety.is_immediate_hazard:
            summary = f"CRITICAL emergency priority due to immediate public safety hazard ({', '.join(safety.hazard_types)})."
            mode = "safety_override"
        elif context.duration.is_prolonged and context.population.is_widespread:
            summary = f"{prio_title} priority due to prolonged disruption ({int(context.duration.normalized_hours)}h) affecting {context.population.scope.replace('_', ' ')}."
            mode = "hybrid_neural_context"
        elif context.is_vulnerable_impact:
            summary = f"{prio_title} priority due to proximity to sensitive community facility ({', '.join(context.vulnerable_groups)})."
            mode = "hybrid_neural_context"
        elif not (category == "other" or final_priority == "low"):
            summary = f"Classified as {prio_title} priority based on MuRIL neural assessment and {cat_title} operational policy."
            mode = "hybrid_neural_context"
        else:
            summary = f"Classified as {prio_title} priority for routine administrative handling."
            mode = "neural_baseline"

        # 2. WHAT Reason
        sub_str = f" ({subcategory.replace('_', ' ')})" if subcategory and subcategory != "other" else ""
        what_reason = f"Classified under {cat_title}{sub_str} based on linguistic keywords and MuRIL v1.1 classification."

        # 3. WHO Reason
        who_reason = f"Routed to {department_name} as the primary authority with jurisdiction over {cat_title.lower()} infrastructure."

        # 4. WHEN Reason
        when_reason = f"Assigned {sla_hours}-hour turnaround SLA based on {prio_title} urgency level and {cat_title} department guidelines."

        # 5. HOW CONFIDENT Reason
        conf_pct = round(routing_confidence * 100, 1)
        how_confident = f"Routing confidence is {conf_pct}% based on category logits and subcategory taxonomy alignment."

        # 6. HUMAN REVIEW Reason
        if review_decision == "AUTO_ROUTE":
            human_reason = "High confidence (≥85%) allows autonomous direct dispatch to field operations."
        elif review_decision == "OFFICER_REVIEW":
            human_reason = "Moderate confidence (60-84%) or multi-issue compound requires triage officer confirmation."
        else:
            human_reason = "Low confidence (<60%) or ambiguous complaint requires manual classification by municipal supervisor."

        return StructuredCivicExplanation(
            summary=summary,
            what_category_reason=what_reason,
            why_urgent_factors=factors,
            who_department_reason=who_reason,
            when_sla_reason=when_reason,
            how_confident_reason=how_confident,
            human_review_reason=human_reason,
            reasoning_mode=mode,
        )


def generate_priority_explanation(
    category: str,
    subcategory: Optional[str] = None,
    final_priority: str = "medium",
    neural_priority: str = "medium",
    context_signals: Optional[Dict[str, Any]] = None,
    department_name: str = "Municipal Department",
    sla_window_hours: int = 24,
    is_safety_override: bool = False,
    requires_human_review: bool = False,
    text: str = "",
    factors: Optional[List[PriorityFactorItem]] = None,
) -> StructuredCivicExplanation:
    ctx = ContextualCivicSignals()
    safety = SafetyAssessment(is_immediate_hazard=is_safety_override)
    factor_list = factors or []

    review_dec = "OFFICER_REVIEW" if requires_human_review else "AUTO_ROUTE"

    return PriorityExplanationGenerator.generate(
        text=text,
        category=category,
        subcategory=subcategory,
        neural_priority=neural_priority,
        neural_prob=0.85,
        final_priority=final_priority,
        context=ctx,
        safety=safety,
        department_name=department_name,
        sla_hours=sla_window_hours,
        routing_confidence=0.90,
        review_decision=review_dec,
        factors=factor_list,
    )

