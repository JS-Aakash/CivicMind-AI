"""
CivicMind AI — Context-Aware Priority Engine
Orchestrates neural probability signals, deterministic context signals, safety policies,
and configurable weights into explainable civic priority decisions.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from app.priority.priority_policy import priority_policy, PriorityPolicy
from app.priority.safety_policy import SafetyPolicy, SafetyAssessment
from app.priority.priority_rules import PriorityRulesEngine, ContextualCivicSignals
from app.priority.priority_explanation import PriorityFactorItem, PriorityExplanationGenerator, StructuredCivicExplanation


@dataclass
class FinalPriorityResult:
    """Output of the Context-Aware Priority Engine."""
    final_priority: str  # "low", "medium", "high", "critical"
    composite_score: float  # [0.0 to 10.0]
    neural_priority: str
    neural_probabilities: Dict[str, float]
    context_signals: ContextualCivicSignals
    safety_assessment: SafetyAssessment
    factors: List[PriorityFactorItem]
    reasoning_mode: str  # "safety_override", "hybrid_neural_context", "neural_only"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_priority": self.final_priority,
            "composite_score": round(self.composite_score, 2),
            "neural_priority": self.neural_priority,
            "neural_probabilities": {k: round(v, 4) for k, v in self.neural_probabilities.items()},
            "context_signals": {
                "duration_hours": self.context_signals.duration.normalized_hours,
                "is_prolonged": self.context_signals.duration.is_prolonged,
                "population_scope": self.context_signals.population.scope,
                "estimated_population": self.context_signals.population.estimated_count,
                "is_vulnerable_impact": self.context_signals.is_vulnerable_impact,
                "vulnerable_groups": self.context_signals.vulnerable_groups,
                "is_critical_infrastructure": self.context_signals.is_critical_infrastructure,
                "is_night_time": self.context_signals.is_night_time,
                "location_category": self.context_signals.location_category,
            },
            "safety_assessment": {
                "is_immediate_hazard": self.safety_assessment.is_immediate_hazard,
                "hazard_types": self.safety_assessment.hazard_types,
                "risk_level": self.safety_assessment.risk_level,
                "justification": self.safety_assessment.justification,
            },
            "factors": [f.to_dict() for f in self.factors],
            "reasoning_mode": self.reasoning_mode,
        }


class PriorityEngine:
    """Main priority engine uniting neural signals and civic rules."""

    def __init__(self, policy: PriorityPolicy = priority_policy):
        self.policy = policy

    def evaluate(
        self,
        text: str,
        category: str,
        subcategory: Optional[str],
        neural_priority: str,
        neural_probabilities: Optional[Dict[str, float]] = None,
        extracted_hazards: Optional[List[str]] = None,
    ) -> FinalPriorityResult:
        if neural_probabilities is None:
            neural_probabilities = {
                "low": 0.1,
                "medium": 0.4,
                "high": 0.4,
                "critical": 0.1,
            }
            if neural_priority in neural_probabilities:
                neural_probabilities[neural_priority] = 0.7

        # 1. Extract context
        context = PriorityRulesEngine.extract_context(text)

        # 2. Safety evaluation
        safety = SafetyPolicy.evaluate_safety(
            text=text,
            category=category,
            subcategory=subcategory,
            extracted_hazards=extracted_hazards or [],
            vulnerable_impact=context.is_vulnerable_impact,
        )

        factors: List[PriorityFactorItem] = []
        w = self.policy.weights

        # 3. Base Neural Contribution [0 to 4.0 points]
        neural_score_map = {"low": 1.0, "medium": 2.5, "high": 4.5, "critical": 6.5}
        base_neural_score = neural_score_map.get(neural_priority, 2.5) * w.neural_signal
        factors.append(PriorityFactorItem(
            factor="neural_signal",
            label="MuRIL Neural Baseline",
            value=neural_priority.upper(),
            impact="neutral" if neural_priority == "medium" else ("increases_urgency" if neural_priority in ["high", "critical"] else "reduces_urgency"),
            weight_contribution=base_neural_score,
            description=f"Neural multi-task classifier predicted {neural_priority.upper()} priority ({neural_probabilities.get(neural_priority, 0.5)*100:.1f}% confidence)",
        ))

        score = base_neural_score

        # 4. Safety Override Check (Instant critical if life-threatening)
        if safety.requires_safety_override:
            factors.append(PriorityFactorItem(
                factor="safety_hazard",
                label="Immediate Public Safety Hazard",
                value=", ".join(safety.hazard_types) if safety.hazard_types else "Hazard detected",
                impact="critical_escalation",
                weight_contribution=4.5 * w.safety_hazard,
                description=safety.justification or "Immediate safety hazard threatening life or public infrastructure",
            ))
            return FinalPriorityResult(
                final_priority="critical",
                composite_score=9.5,
                neural_priority=neural_priority,
                neural_probabilities=neural_probabilities,
                context_signals=context,
                safety_assessment=safety,
                factors=factors,
                reasoning_mode="safety_override",
            )

        # 5. Duration Contribution
        if context.duration.normalized_hours is not None:
            d_hours = context.duration.normalized_hours
            if d_hours >= 168.0:  # >= 1 week
                d_contrib = 2.2 * w.duration
                d_impact = "increases_urgency"
                d_desc = f"Prolonged chronic disruption lasting {int(d_hours)} hours ({int(d_hours/24)} days)"
            elif d_hours >= 72.0:  # >= 3 days
                d_contrib = 1.5 * w.duration
                d_impact = "increases_urgency"
                d_desc = f"Unresolved civic breakdown lasting {int(d_hours)} hours ({int(d_hours/24)} days)"
            elif d_hours >= 24.0:  # >= 1 day
                d_contrib = 0.8 * w.duration
                d_impact = "increases_urgency"
                d_desc = f"Issue ongoing for {int(d_hours)} hours"
            else:
                d_contrib = 0.0
                d_impact = "neutral"
                d_desc = f"Reported within standard operational timeframe ({d_hours}h)"

            if d_contrib > 0:
                score += d_contrib
                factors.append(PriorityFactorItem(
                    factor="duration",
                    label=f"{int(d_hours)}h Unresolved Duration",
                    value=f"{int(d_hours)} hours",
                    impact=d_impact,
                    weight_contribution=d_contrib,
                    description=d_desc,
                ))

        # 6. Population Scope Contribution
        if context.population.scope in ["whole_street", "neighborhood", "critical_community"] or (context.population.estimated_count and context.population.estimated_count >= 20):
            if context.population.scope == "neighborhood" or (context.population.estimated_count and context.population.estimated_count >= 100):
                pop_contrib = 2.0 * w.population_scope
                pop_label = f"Widespread Community Impact (~{context.population.estimated_count or 100}+ citizens)"
            else:
                pop_contrib = 1.3 * w.population_scope
                pop_label = f"Entire Street Affected (~{context.population.estimated_count or 40} citizens)"

            score += pop_contrib
            factors.append(PriorityFactorItem(
                factor="affected_population",
                label=pop_label,
                value=context.population.scope.replace("_", " ").title(),
                impact="increases_urgency",
                weight_contribution=pop_contrib,
                description=f"Issue impacts multiple citizens across {context.population.scope.replace('_', ' ')}",
            ))

        # 7. Vulnerable Population & Facilities Contribution
        if context.is_vulnerable_impact:
            v_contrib = 1.6 * w.vulnerable_population
            score += v_contrib
            factors.append(PriorityFactorItem(
                factor="vulnerable_population",
                label="Sensitive Institution Proximity",
                value=", ".join(context.vulnerable_groups),
                impact="increases_urgency",
                weight_contribution=v_contrib,
                description=f"Directly impacts sensitive public institutions or vulnerable citizens ({', '.join(context.vulnerable_groups)})",
            ))

        # 8. Critical Infrastructure Contribution
        if context.is_critical_infrastructure:
            infra_contrib = 1.2 * w.critical_infrastructure
            score += infra_contrib
            factors.append(PriorityFactorItem(
                factor="critical_infrastructure",
                label="Arterial Infrastructure Link",
                value=", ".join(context.infrastructure_types),
                impact="increases_urgency",
                weight_contribution=infra_contrib,
                description=f"Directly affects key municipal infrastructure ({', '.join(context.infrastructure_types)})",
            ))

        # 9. Night time darkness without streetlight
        if context.is_night_time and (category in ["street_infrastructure", "electricity"] or subcategory in ["street_light_failure", "pothole"]):
            night_contrib = 1.0 * w.location_vulnerability
            score += night_contrib
            factors.append(PriorityFactorItem(
                factor="night_context",
                label="Nighttime Darkness Vulnerability",
                value="Night context",
                impact="increases_urgency",
                weight_contribution=night_contrib,
                description="Lack of lighting at night poses active pedestrian accident and safety risks",
            ))

        # Non-grievance inquiries dampening
        if category in ["other", "general"] or not bool(text.strip()):
            score = min(score, 1.8)

        # 10. Map to discrete priority
        final_prio = self.policy.thresholds.score_to_priority(score)

        return FinalPriorityResult(
            final_priority=final_prio,
            composite_score=score,
            neural_priority=neural_priority,
            neural_probabilities=neural_probabilities,
            context_signals=context,
            safety_assessment=safety,
            factors=factors,
            reasoning_mode="hybrid_neural_context",
        )


# Global singleton
priority_engine = PriorityEngine()


def evaluate_priority(
    neural_pred: str = "medium",
    neural_prob: float = 0.5,
    neural_probs: Optional[Dict[str, float]] = None,
    severity: str = "moderate",
    text: str = "",
    category: str = "general",
    subcategory: Optional[str] = None,
    entities: Optional[Dict[str, Any]] = None,
) -> FinalPriorityResult:
    hazards = []
    if entities and "hazard" in entities:
        hazards.append(str(entities["hazard"]))

    probs = neural_probs or {
        "low": 0.1,
        "medium": 0.3,
        "high": 0.5 if neural_pred == "high" else 0.2,
        "critical": 0.5 if neural_pred == "critical" else 0.05,
    }
    if neural_pred in probs:
        probs[neural_pred] = max(probs[neural_pred], neural_prob)

    return priority_engine.evaluate(
        text=text,
        category=category,
        subcategory=subcategory,
        neural_priority=neural_pred,
        neural_probabilities=probs,
        extracted_hazards=hazards,
    )

