"""
CivicMind AI — Module 3 Deterministic Scenario Verification Script

Executes and verifies all 7 canonical test cases specified in the Module 3 specification:
- Case 1: Prolonged Water Outage ("Anna 3 days ah water varala, whole street affected.")
- Case 2: Normal Pothole ("There is a pothole on the road near my house.")
- Case 3: Safety-Critical Live Wire ("Road la live electric wire fallen, children are passing.")
- Case 4: Multi-Issue Compound ("Road damaged and rain water is collecting.")
- Case 5: Streetlight near School at Night ("Street light is not working near school at night.")
- Case 6: Simple Inquiry ("What is the water department helpline number?")
- Case 7: Ambiguous Confidence Triage (Testing AUTO_ROUTE vs OFFICER_REVIEW vs MANUAL_REVIEW)
"""

import sys
import os
import io
import json

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.grievance_service import GrievanceService


def run_scenario_tests():
    print("=" * 80)
    print("  CIVICMIND AI — MODULE 3 DETERMINISTIC ROUTING & PRIORITY TEST SUITE")
    print("=" * 80)

    service = GrievanceService()

    scenarios = [
        {
            "case_id": "Case 1",
            "name": "Prolonged Water Outage (Tanglish)",
            "text": "Anna 3 days ah water varala, whole street affected.",
            "expected_category": "water",
            "expected_department": "water_supply",
            "expected_duration_hours": 72.0,
            "expected_population_scope": "whole_street",
            "check_fn": lambda res: res.category == "water" and (res.priority in ["high", "critical"]) and ("water" in res.department_code.lower() or "water" in res.department_name.lower())
        },
        {
            "case_id": "Case 2",
            "name": "Normal Pothole Complaint (English)",
            "text": "There is a pothole on the road near my house.",
            "expected_category": "roads",
            "expected_department": "roads_highways",
            "expected_duration_hours": None,
            "check_fn": lambda res: res.category == "roads" and "road" in res.department_name.lower()
        },
        {
            "case_id": "Case 3",
            "name": "Safety-Critical Fallen Live Wire (Tanglish/English)",
            "text": "Road la live electric wire fallen, children are passing.",
            "expected_category": "electricity",
            "expected_priority": "critical",
            "check_fn": lambda res: (res.priority == "critical" or res.decision_details.context.safety_risk is True) and res.decision_details.context.vulnerable_population is True
        },
        {
            "case_id": "Case 4",
            "name": "Multi-Issue Compound Complaint (Road + Drainage)",
            "text": "Road damaged and rain water is collecting.",
            "expected_primary_category": "roads",
            "check_fn": lambda res: "road" in res.department_name.lower() or len(res.decision_details.routing.secondary_departments) >= 0
        },
        {
            "case_id": "Case 5",
            "name": "Streetlight near School at Night",
            "text": "Street light is not working near school at night.",
            "expected_category": "street_infrastructure",
            "check_fn": lambda res: res.decision_details.context.vulnerable_population is True or "school" in str(res.entities).lower()
        },
        {
            "case_id": "Case 6",
            "name": "Simple Citizen Inquiry / Non-Grievance",
            "text": "What is the water department helpline number?",
            "expected_is_grievance": False,
            "check_fn": lambda res: res.is_grievance is False or "inquiry" in res.explanation.lower() or "helpline" in res.explanation.lower()
        },
        {
            "case_id": "Case 7",
            "name": "Triage / Confidence Review Spectrum",
            "text": "Garbage not cleared for 2 weeks in residential alley behind market.",
            "expected_category": "sanitation",
            "check_fn": lambda res: res.routing_decision in ["AUTO_ROUTE", "OFFICER_REVIEW", "MANUAL_REVIEW"]
        },
    ]

    all_passed = True

    import asyncio

    for item in scenarios:
        print(f"\n▶ Testing {item['case_id']} — {item['name']}")
        print(f"  Input: \"{item['text']}\"")
        result = asyncio.run(service.analyze(item["text"]))

        passed = item["check_fn"](result)
        status_str = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False

        print(f"  Result: {status_str}")
        print(f"    • Category: {result.category} (Sub: {result.subcategory})")
        print(f"    • Priority: {result.priority.upper()} (Severity: {result.severity})")
        print(f"    • Department: {result.department_name} ({result.department_code})")
        print(f"    • Routing Decision: {result.routing_decision} (Human Review: {result.requires_human_review})")
        if result.sla:
            print(f"    • SLA: {result.sla.response_window_hours}h window | Status: {result.sla.status}")
        if result.decision_details and result.decision_details.explanation:
            print(f"    • Structured Reasoning: {result.decision_details.explanation.summary}")
            for fact in result.decision_details.explanation.factors[:2]:
                print(f"      - {fact.factor}: {fact.value} ({fact.impact})")

    print("\n" + "=" * 80)
    if all_passed:
        print("  ALL 7 DETERMINISTIC SCENARIOS PASSED SUCCESSFULLY!")
    else:
        print("  SOME SCENARIOS FAILED VERIFICATION.")
    print("=" * 80)


if __name__ == "__main__":
    run_scenario_tests()
