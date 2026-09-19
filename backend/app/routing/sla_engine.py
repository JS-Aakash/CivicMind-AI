"""
CivicMind AI — Configurable SLA Engine
Computes resolution deadlines, response countdowns, and dynamic SLA status
across priorities, categories, and municipal departments.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from app.routing.department_registry import department_registry


@dataclass
class SLAPolicyConfig:
    """Configurable default SLA turnaround windows in hours."""
    critical_sla_hours: int = 4
    high_sla_hours: int = 24
    medium_sla_hours: int = 48
    low_sla_hours: int = 120
    approaching_breach_ratio: float = 0.75  # Breached or warning if >= 75% elapsed
    version: str = "sla-policy-v1.0"


@dataclass
class SLAAssessmentResult:
    """Computed SLA metrics for a grievance."""
    target_sla_hours: int
    target_response_minutes: int
    created_at: str
    due_at: str
    status: str  # "within_sla", "approaching_breach", "breached", "escalated"
    elapsed_minutes: int
    remaining_minutes: int
    percent_elapsed: float
    is_breached: bool
    is_approaching: bool

    @property
    def response_minutes(self) -> int:
        return self.target_response_minutes

    @property
    def response_window_hours(self) -> int:
        return self.target_sla_hours

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_sla_hours": self.target_sla_hours,
            "target_response_minutes": self.target_response_minutes,
            "response_minutes": self.target_response_minutes,
            "response_window_hours": self.target_sla_hours,
            "created_at": self.created_at,
            "due_at": self.due_at,
            "status": self.status,
            "elapsed_minutes": self.elapsed_minutes,
            "remaining_minutes": self.remaining_minutes,
            "percent_elapsed": round(self.percent_elapsed, 1),
            "is_breached": self.is_breached,
            "is_approaching": self.is_approaching,
        }


class SLAEngine:
    """Computes exact SLA deadlines and lifecycle status."""

    def __init__(self, policy: SLAPolicyConfig = SLAPolicyConfig()):
        self.policy = policy

    def calculate_sla(
        self,
        priority: str,
        department_id: str,
        category: str = "general",
        created_at: Optional[datetime] = None,
        is_immediate_hazard: bool = False,
    ) -> SLAAssessmentResult:
        created_dt = created_at or datetime.now(timezone.utc)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)

        # 1. Lookup Department Default
        dept = department_registry.get_by_id(department_id)
        if dept and priority in dept.default_sla_hours:
            target_hours = dept.default_sla_hours[priority]
        else:
            prio_map = {
                "critical": self.policy.critical_sla_hours,
                "high": self.policy.high_sla_hours,
                "medium": self.policy.medium_sla_hours,
                "low": self.policy.low_sla_hours,
            }
            target_hours = prio_map.get(priority, 48)

        # Emergency override for immediate hazards (e.g. 2 hours max)
        if is_immediate_hazard:
            target_hours = min(target_hours, 2)

        target_minutes = target_hours * 60
        due_dt = created_dt + timedelta(hours=target_hours)

        # 2. Elapsed & Remaining Time
        now = datetime.now(timezone.utc)
        elapsed_delta = now - created_dt
        elapsed_minutes = max(int(elapsed_delta.total_seconds() / 60), 0)
        remaining_minutes = max(target_minutes - elapsed_minutes, 0)
        percent_elapsed = min(max((elapsed_minutes / max(target_minutes, 1)) * 100.0, 0.0), 100.0)

        # 3. Determine SLA Status
        if elapsed_minutes >= target_minutes:
            status = "breached"
            is_breached = True
            is_approaching = False
        elif percent_elapsed >= (self.policy.approaching_breach_ratio * 100.0):
            status = "approaching_breach"
            is_breached = False
            is_approaching = True
        else:
            status = "within_sla"
            is_breached = False
            is_approaching = False

        return SLAAssessmentResult(
            target_sla_hours=target_hours,
            target_response_minutes=target_minutes,
            created_at=created_dt.isoformat(),
            due_at=due_dt.isoformat(),
            status=status,
            elapsed_minutes=elapsed_minutes,
            remaining_minutes=remaining_minutes,
            percent_elapsed=percent_elapsed,
            is_breached=is_breached,
            is_approaching=is_approaching,
        )


# Global singleton
sla_engine = SLAEngine()


def calculate_sla(
    priority: str,
    department_id: str = "general",
    category: str = "general",
    created_at: Optional[datetime] = None,
    is_immediate_hazard: bool = False,
) -> SLAAssessmentResult:
    return sla_engine.calculate_sla(
        priority=priority,
        department_id=department_id,
        category=category,
        created_at=created_at,
        is_immediate_hazard=is_immediate_hazard,
    )


def evaluate_sla_status(due_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    if now > due_at:
        return "breached"
    return "within_sla"

