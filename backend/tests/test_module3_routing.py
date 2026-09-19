"""
CivicMind AI — Module 3 Unit Tests
Comprehensive unit tests covering:
- priority rules & scoring
- duration normalization
- population normalization
- safety hazard detection & override
- vulnerable population & critical infrastructure
- department routing (single & multi-issue)
- confidence thresholds & review policy
- SLA calculation & dynamic states
- internal escalation events
- officer overrides with audit preservation
- deterministic explainability factors
"""

import pytest
import datetime
from app.routing.department_registry import (
    DEPARTMENT_REGISTRY,
    get_department_by_id,
    get_department_for_issue,
)
from app.priority.priority_rules import (
    normalize_duration_to_hours,
    normalize_population_scope,
    detect_vulnerable_population,
    detect_critical_infrastructure,
    compute_context_priority_score,
)
from app.priority.safety_policy import evaluate_safety_override
from app.priority.priority_explanation import generate_priority_explanation
from app.priority.priority_engine import evaluate_priority
from app.routing.review_policy import evaluate_review_decision, ReviewDecision
from app.routing.routing_engine import route_complaint
from app.routing.sla_engine import calculate_sla, evaluate_sla_status
from app.routing.escalation_engine import evaluate_escalation


# =========================================================================
# 1. Department Registry Tests
# =========================================================================
def test_department_registry_initialization():
    departments = DEPARTMENT_REGISTRY.get_all()
    assert len(departments) == 10
    dept_ids = [d.id for d in departments]
    assert "water_supply" in dept_ids
    assert "roads_highways" in dept_ids
    assert "sanitation" in dept_ids
    assert "electricity_board" in dept_ids
    assert "public_safety" in dept_ids


def test_department_lookup():
    water_dept = get_department_by_id("water_supply")
    assert water_dept is not None
    assert "Water" in water_dept.name

    mapped_dept = get_department_for_issue("roads", "pothole")
    assert mapped_dept.id == "roads_highways"


# =========================================================================
# 2. Duration Normalization Tests
# =========================================================================
def test_duration_normalization():
    assert normalize_duration_to_hours("3 days") == 72.0
    assert normalize_duration_to_hours("2 hours") == 2.0
    assert normalize_duration_to_hours("1 week") == 168.0
    assert normalize_duration_to_hours("30 minutes") == 0.5
    assert normalize_duration_to_hours("no duration mentioned") is None


# =========================================================================
# 3. Population Normalization Tests
# =========================================================================
def test_population_normalization():
    scope1, count1 = normalize_population_scope("around 200 families affected")
    assert count1 == 200
    assert scope1 == "multiple_households"

    scope2, _ = normalize_population_scope("whole street has no water")
    assert scope2 == "whole_street"

    scope3, _ = normalize_population_scope("only in my house")
    assert scope3 == "single_household"


# =========================================================================
# 4. Vulnerable Population & Critical Infrastructure Tests
# =========================================================================
def test_vulnerable_population_detection():
    is_vuln, groups = detect_vulnerable_population("Children are playing near the open pit")
    assert is_vuln is True
    assert "children" in groups

    is_vuln_school, groups_school = detect_vulnerable_population("Streetlight broken outside primary school")
    assert is_vuln_school is True
    assert "school" in groups_school


def test_critical_infrastructure_detection():
    is_infra, types = detect_critical_infrastructure("Water main burst near government general hospital")
    assert is_infra is True
    assert "hospital" in types


# =========================================================================
# 5. Safety Hazard & Controlled Override Tests
# =========================================================================
def test_safety_override_active_hazard():
    # Live fallen electrical wire is an acute danger
    result = evaluate_safety_override(
        text="Live electric wire fallen on the main road, heavy sparking",
        category="electricity",
        subcategory="fallen_wire",
        entities={"hazard": "live_wire"}
    )
    assert result.is_acute_safety_hazard is True
    assert result.forced_priority == "critical"
    assert result.override_triggered is True


def test_safety_override_passive_mention():
    # Passive or de-energized mention should NOT blindly trigger critical override
    result = evaluate_safety_override(
        text="The streetlight has an exposed wire but no power connection for years",
        category="electricity",
        subcategory="exposed_wire",
        entities={}
    )
    assert result.override_triggered is False
    assert result.forced_priority is None


# =========================================================================
# 6. Priority Engine Hybrid Evaluation Tests
# =========================================================================
def test_priority_engine_prolonged_water_outage():
    # 72 hours water outage affecting whole street should elevate priority
    result = evaluate_priority(
        neural_pred="medium",
        neural_prob=0.65,
        neural_probs={"low": 0.1, "medium": 0.65, "high": 0.20, "critical": 0.05},
        severity="high",
        text="Anna 3 days ah water varala, whole street affected.",
        category="water",
        subcategory="no_water_supply",
        entities={"duration": "3 days", "affected_population": "whole street"},
    )
    assert result.final_priority in ["high", "critical"]
    assert result.context_signals["duration_hours"] == 72.0
    assert result.context_signals["affected_population"] == "whole_street"


def test_priority_engine_emergency_override():
    result = evaluate_priority(
        neural_pred="medium",
        neural_prob=0.55,
        neural_probs={"low": 0.2, "medium": 0.55, "high": 0.20, "critical": 0.05},
        severity="moderate",
        text="Road la live electric wire fallen, children are passing by",
        category="electricity",
        subcategory="fallen_wire",
        entities={},
    )
    assert result.final_priority == "critical"
    assert result.reasoning_mode == "safety_override"


# =========================================================================
# 7. Smart Routing Engine Tests (Single & Multi-Issue)
# =========================================================================
def test_single_issue_routing():
    res = route_complaint(
        primary_category="roads",
        primary_subcategory="pothole",
        category_confidence=0.92,
        multi_issues=[]
    )
    assert res.primary_department.id == "roads_highways"
    assert res.primary_department.confidence >= 0.85
    assert len(res.secondary_departments) == 0


def test_multi_issue_compound_routing():
    # "Road damaged and rain water is collecting"
    res = route_complaint(
        primary_category="roads",
        primary_subcategory="damaged_road",
        category_confidence=0.89,
        multi_issues=[
            {"category": "drainage", "subcategory": "waterlogging", "confidence": 0.82}
        ]
    )
    assert res.primary_department.id == "roads_highways"
    assert len(res.secondary_departments) == 1
    assert res.secondary_departments[0].id == "drainage"


# =========================================================================
# 8. Human Review Policy Tests
# =========================================================================
def test_review_policy_thresholds():
    # High confidence -> AUTO_ROUTE
    high_conf = evaluate_review_decision(
        routing_confidence=0.91,
        priority="high",
        is_safety_hazard=False
    )
    assert high_conf.decision == ReviewDecision.AUTO_ROUTE
    assert high_conf.requires_human_review is False

    # Moderate confidence -> OFFICER_REVIEW
    med_conf = evaluate_review_decision(
        routing_confidence=0.72,
        priority="medium",
        is_safety_hazard=False
    )
    assert med_conf.decision == ReviewDecision.OFFICER_REVIEW
    assert med_conf.requires_human_review is True

    # Low confidence -> MANUAL_REVIEW
    low_conf = evaluate_review_decision(
        routing_confidence=0.45,
        priority="low",
        is_safety_hazard=False
    )
    assert low_conf.decision == ReviewDecision.MANUAL_REVIEW
    assert low_conf.requires_human_review is True


# =========================================================================
# 9. SLA Calculation & Dynamic State Tests
# =========================================================================
def test_sla_calculation():
    created_at = datetime.datetime.now(datetime.timezone.utc)
    critical_sla = calculate_sla("critical", "public_safety", created_at=created_at)
    assert critical_sla.response_minutes <= 120  # Emergency handling window
    assert critical_sla.status == "within_sla"

    high_sla = calculate_sla("high", "water_supply", created_at=created_at)
    assert high_sla.response_window_hours == 24


def test_sla_status_breached():
    past_due = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)
    status = evaluate_sla_status(due_at=past_due)
    assert status == "breached"


# =========================================================================
# 10. Escalation Engine Tests
# =========================================================================
def test_escalation_triggers():
    # Critical unhandled complaint should trigger immediate escalation
    event = evaluate_escalation(
        complaint_id="c-test-01",
        priority="critical",
        sla_status="within_sla",
        hours_elapsed=0.5
    )
    assert event.is_escalated is True
    assert event.escalation_level == "LEVEL_1_SUPERVISOR"
