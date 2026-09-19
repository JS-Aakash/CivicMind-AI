"""
CivicMind AI — Department Routing Service (Module 3 Enhanced)
Wraps DepartmentRegistry, RoutingEngine, SLAEngine, and ReviewPolicy.
"""
import logging
from typing import Dict, List, Optional, Any
from app.routing.department_registry import department_registry, DepartmentConfig
from app.routing.routing_engine import routing_engine, RoutingDecisionResult
from app.routing.sla_engine import sla_engine, SLAAssessmentResult
from app.routing.review_policy import review_policy

logger = logging.getLogger(__name__)


class RoutingService:
    """
    High-level routing service coordinating departmental lookup,
    multi-issue dispatching, and SLA assignment.
    """

    def route(
        self,
        category: str,
        priority: str,
        subcategory: Optional[str] = None,
        category_confidence: float = 0.8,
        subcategory_confidence: float = 0.6,
        secondary_categories: Optional[List[Dict[str, Any]]] = None,
        is_grievance: bool = True,
        is_immediate_hazard: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes full multi-issue routing and SLA calculation.
        """
        routing_res = routing_engine.route(
            category=category,
            subcategory=subcategory,
            category_confidence=category_confidence,
            subcategory_confidence=subcategory_confidence,
            secondary_categories=secondary_categories,
            is_grievance=is_grievance,
            is_immediate_hazard=is_immediate_hazard,
        )

        sla_res = sla_engine.calculate_sla(
            priority=priority,
            department_id=routing_res.primary_department.id,
            category=category,
            is_immediate_hazard=is_immediate_hazard,
        )

        return {
            "code": routing_res.primary_department.code,
            "name": routing_res.primary_department.name,
            "contact": routing_res.primary_department.contact_email,
            "sla_hours": sla_res.target_sla_hours,
            "reason": routing_res.routing_reason,
            "routing_result": routing_res,
            "sla_result": sla_res,
        }

    def get_all_departments(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in department_registry.get_all()]


routing_service = RoutingService()
