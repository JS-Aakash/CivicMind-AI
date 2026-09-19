"""
CivicMind AI — Internal Escalation Engine
Evaluates SLA breach conditions, high-risk delays, and rejection history to generate
structured internal escalation event records for command center consumption.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class EscalationEvent:
    """Internal escalation event record."""
    complaint_id: Optional[str]
    escalation_tier: str  # "supervisory_alert", "department_head_escalation", "emergency_dispatch"
    trigger_reason: str
    severity_level: str  # "warning", "high", "critical"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged: bool = False
    action_required: str = "Immediate operational review"
    is_escalated: bool = True

    @property
    def escalation_level(self) -> str:
        if self.escalation_tier in ["emergency_dispatch", "supervisory_alert"]:
            return "LEVEL_1_SUPERVISOR"
        return self.escalation_tier.upper()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "complaint_id": self.complaint_id,
            "escalation_tier": self.escalation_tier,
            "trigger_reason": self.trigger_reason,
            "severity_level": self.severity_level,
            "created_at": self.created_at,
            "acknowledged": self.acknowledged,
            "action_required": self.action_required,
            "is_escalated": self.is_escalated,
            "escalation_level": self.escalation_level,
        }


class EscalationEngine:
    """Evaluates and emits internal escalation records."""

    @classmethod
    def evaluate_escalation(
        cls,
        complaint_id: Optional[str],
        priority: str,
        sla_status: str,
        is_immediate_hazard: bool,
        rejection_count: int = 0,
    ) -> Optional[EscalationEvent]:
        # 1. Immediate Safety Hazard Escalation
        if is_immediate_hazard:
            return EscalationEvent(
                complaint_id=complaint_id,
                escalation_tier="emergency_dispatch",
                trigger_reason="Immediate public safety hazard detected requiring rapid field team dispatch",
                severity_level="critical",
                action_required="Dispatch emergency response crew immediately within 1-2 hours",
            )

        # 2. SLA Breached Escalation
        if sla_status == "breached":
            return EscalationEvent(
                complaint_id=complaint_id,
                escalation_tier="department_head_escalation",
                trigger_reason="Resolution turnaround window has expired without completion",
                severity_level="high",
                action_required="Supervisory intervention to expedite pending ticket",
            )

        # 3. SLA Approaching Breach Warning
        if sla_status == "approaching_breach":
            return EscalationEvent(
                complaint_id=complaint_id,
                escalation_tier="supervisory_alert",
                trigger_reason="Turnaround deadline is approaching (<25% window remaining)",
                severity_level="warning",
                action_required="Expedite pending field work before breach occurs",
            )

        # 4. Repeated Officer Rejection
        if rejection_count >= 2:
            return EscalationEvent(
                complaint_id=complaint_id,
                escalation_tier="supervisory_alert",
                trigger_reason=f"Complaint has been rejected/reassigned {rejection_count} times",
                severity_level="warning",
                action_required="Senior officer manual assignment required",
            )

        return None


# Global singleton
escalation_engine = EscalationEngine()


def evaluate_escalation(
    complaint_id: Optional[str] = None,
    priority: str = "medium",
    sla_status: str = "within_sla",
    is_immediate_hazard: bool = False,
    rejection_count: int = 0,
    hours_elapsed: float = 0.0,
) -> Optional[EscalationEvent]:
    hazard = is_immediate_hazard or (priority == "critical" and hours_elapsed > 0)
    return EscalationEngine.evaluate_escalation(
        complaint_id=complaint_id,
        priority=priority,
        sla_status=sla_status,
        is_immediate_hazard=hazard,
        rejection_count=rejection_count,
    )

