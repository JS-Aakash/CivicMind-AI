"""
CivicMind AI — Smart Multi-Issue Department Routing Engine
Determines primary and secondary departmental routing from MuRIL v1.1 multi-issue predictions,
computes transparent routing confidence, and assigns human-in-the-loop review policy.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from app.routing.department_registry import department_registry, DepartmentConfig
from app.routing.review_policy import review_policy, ReviewPolicyConfig


@dataclass
class DepartmentTarget:
    """Target department dispatch record."""
    id: str
    code: str
    name: str
    contact_email: str
    confidence: float
    is_primary: bool = True
    role: str = "primary_lead"  # "primary_lead", "secondary_support"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "contact_email": self.contact_email,
            "confidence": round(self.confidence, 4),
            "is_primary": self.is_primary,
            "role": self.role,
        }


@dataclass
class RoutingDecisionResult:
    """Canonical routing output of Module 3."""
    primary_department: DepartmentTarget
    secondary_departments: List[DepartmentTarget] = field(default_factory=list)
    routing_confidence: float = 0.0
    routing_decision: str = "AUTO_ROUTE"  # "AUTO_ROUTE", "OFFICER_REVIEW", "MANUAL_REVIEW"
    requires_human_review: bool = False
    routing_reason: str = ""
    is_compound_multi_issue: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_department": self.primary_department.to_dict(),
            "secondary_departments": [d.to_dict() for d in self.secondary_departments],
            "routing_confidence": round(self.routing_confidence, 4),
            "routing_decision": self.routing_decision,
            "requires_human_review": self.requires_human_review,
            "routing_reason": self.routing_reason,
            "is_compound_multi_issue": self.is_compound_multi_issue,
        }


class RoutingEngine:
    """Smart routing engine handling primary and compound multi-issue dispatches."""

    def __init__(self, registry=department_registry, review_pol: ReviewPolicyConfig = review_policy):
        self.registry = registry
        self.review_policy = review_pol

    def route(
        self,
        category: str,
        subcategory: Optional[str] = None,
        category_confidence: float = 0.8,
        subcategory_confidence: float = 0.6,
        secondary_categories: Optional[List[Dict[str, Any]]] = None,
        is_grievance: bool = True,
        is_immediate_hazard: bool = False,
    ) -> RoutingDecisionResult:
        # Non-grievance inquiry routing
        if not is_grievance or category in ["other", "general"]:
            helpdesk = self.registry.get_by_id("citizen_helpdesk")
            primary_target = DepartmentTarget(
                id=helpdesk.id,
                code=helpdesk.code,
                name=helpdesk.name,
                contact_email=helpdesk.contact_email,
                confidence=0.95,
                is_primary=True,
                role="primary_lead",
            )
            return RoutingDecisionResult(
                primary_department=primary_target,
                secondary_departments=[],
                routing_confidence=0.95,
                routing_decision="AUTO_ROUTE",
                requires_human_review=False,
                routing_reason="Informational or procedural inquiry routed to Citizen Helpdesk for administrative response.",
                is_compound_multi_issue=False,
            )

        # 1. Primary Department Resolution
        primary_dept = self.registry.get_primary_department(category, subcategory)

        # 2. Secondary Multi-Issue Departments Resolution
        secondary_targets: List[DepartmentTarget] = []
        is_compound = False

        if secondary_categories:
            for sec in secondary_categories:
                sec_cat = sec.get("category")
                sec_prob = sec.get("probability", 0.5)
                if sec_cat and sec_cat != category:
                    sec_dept = self.registry.get_primary_department(sec_cat)
                    if sec_dept.id != primary_dept.id and not any(t.id == sec_dept.id for t in secondary_targets):
                        secondary_targets.append(DepartmentTarget(
                            id=sec_dept.id,
                            code=sec_dept.code,
                            name=sec_dept.name,
                            contact_email=sec_dept.contact_email,
                            confidence=sec_prob,
                            is_primary=False,
                            role="secondary_support",
                        ))
                        is_compound = True

        # 3. Calculate Overall Routing Confidence
        # Harmonize category confidence (60%) + subcategory confidence (40%)
        composite_routing_conf = float(category_confidence * 0.65 + subcategory_confidence * 0.35)
        # Scale to [0.5, 0.98]
        routing_confidence = min(max(composite_routing_conf * 1.5, 0.50), 0.98)

        primary_target = DepartmentTarget(
            id=primary_dept.id,
            code=primary_dept.code,
            name=primary_dept.name,
            contact_email=primary_dept.contact_email,
            confidence=routing_confidence,
            is_primary=True,
            role="primary_lead",
        )

        # 4. Human-in-the-Loop Review Policy
        decision, req_review = self.review_policy.evaluate_decision(
            routing_confidence=routing_confidence,
            is_compound_multi_issue=is_compound,
            is_immediate_hazard=is_immediate_hazard,
        )

        # 5. Routing Reason
        cat_disp = category.replace("_", " ").title()
        if is_compound:
            sec_names = ", ".join(t.name for t in secondary_targets)
            reason = f"Compound complaint with primary issue in {cat_disp} and secondary impact on {sec_names}. Routed to {primary_dept.name} as lead department."
        else:
            reason = f"{cat_disp} complaint routed to {primary_dept.name} based on category classification and department jurisdiction."

        return RoutingDecisionResult(
            primary_department=primary_target,
            secondary_departments=secondary_targets,
            routing_confidence=routing_confidence,
            routing_decision=decision,
            requires_human_review=req_review,
            routing_reason=reason,
            is_compound_multi_issue=is_compound,
        )


# Global singleton
routing_engine = RoutingEngine()


def route_complaint(
    primary_category: str,
    primary_subcategory: Optional[str] = None,
    category_confidence: float = 0.85,
    subcategory_confidence: float = 0.70,
    multi_issues: Optional[List[Dict[str, Any]]] = None,
    is_grievance: bool = True,
    is_immediate_hazard: bool = False,
) -> RoutingDecisionResult:
    return routing_engine.route(
        category=primary_category,
        subcategory=primary_subcategory,
        category_confidence=category_confidence,
        subcategory_confidence=subcategory_confidence,
        secondary_categories=multi_issues,
        is_grievance=is_grievance,
        is_immediate_hazard=is_immediate_hazard,
    )

