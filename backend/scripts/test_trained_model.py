#!/usr/bin/env python3
"""
CivicMind AI — Model Regression & Verification Test Suite (v1.1 Hardened)
Tests 14 comprehensive test cases across English, Tamil, Tanglish, Hindi, Hinglish,
short phrases, conversational greetings, safety-critical hazards, and multi-issue compounds.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.services.language_service import language_detection_service
from app.services.grievance_service import grievance_service
from app.ml.extraction.lightweight_extractor import LightweightCivicExtractor
from app.core.config import settings

TEST_CASES = [
    {
        "id": "TC_01",
        "description": "English Standard Grievance",
        "text": "There has been no water supply for three days.",
        "expected_category": "water",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_02",
        "description": "Tamil Native Script",
        "text": "மூன்று நாட்களாக குடிநீர் வரவில்லை.",
        "expected_category": "water",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_03",
        "description": "Tanglish (Romanized Tamil)",
        "text": "Moonu naala thanni varala.",
        "expected_category": "water",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_04",
        "description": "Short Tanglish Phrase",
        "text": "thanni varala",
        "expected_category": "water",
        "expected_grievance": True,
    },
    {
        "id": "TC_05",
        "description": "Short Tanglish Electricity",
        "text": "current cut",
        "expected_category": "electricity",
        "expected_grievance": True,
    },
    {
        "id": "TC_06",
        "description": "Tamil-English Code-Mixed",
        "text": "Anna water supply 3 days ah varala.",
        "expected_category": "water",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_07",
        "description": "Hindi Native Script",
        "text": "तीन दिन से पानी नहीं आ रहा है।",
        "expected_category": "water",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_08",
        "description": "Hinglish (Romanized Hindi)",
        "text": "Teen din se water supply nahi aa rahi.",
        "expected_category": "water",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_09",
        "description": "Short Hinglish Phrase",
        "text": "bijli chali gayi",
        "expected_category": "electricity",
        "expected_grievance": True,
    },
    {
        "id": "TC_10",
        "description": "Conversational Greeting",
        "text": "Helloooo",
        "expected_grievance": False,
        "expected_category": "other",
        "expected_priority": "low",
    },
    {
        "id": "TC_11",
        "description": "Non-Grievance Procedural Inquiry",
        "text": "What is the water department helpline number?",
        "expected_categories": ["water", "other"],
        "expected_grievance": False,
        "expected_priority": "low",
    },
    {
        "id": "TC_12",
        "description": "Safety-Critical Hazard (Live Wire)",
        "text": "Live electric wire fallen near school, children passing.",
        "expected_category": "electricity",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_13",
        "description": "Safety-Critical Hazard (Transformer Sparking)",
        "text": "Transformer sparking with smoke opposite to government hospital.",
        "expected_category": "electricity",
        "expected_grievance": True,
        "min_priority": "high",
    },
    {
        "id": "TC_14",
        "description": "Compound Multi-Issue Complaint",
        "text": "Water pipeline burst causing huge road flooding and potholes near bus stand.",
        "expected_categories": ["water", "roads"],
        "expected_grievance": True,
    },
]


async def run_regression_tests():
    print("=" * 70)
    print("  CivicMind AI — MuRIL v1.1 Model Regression Test Suite")
    print(f"  AI_MODE: {settings.AI_MODE} | Trained Model Path: {settings.trained_model_dir}")
    print("=" * 70)

    passed = 0
    failed = 0
    results = []

    for tc in TEST_CASES:
        text = tc["text"]
        print(f"\n[{tc['id']}] {tc['description']}")
        print(f"  Input Text: \"{text}\"")

        # Run pipeline
        res = await grievance_service.analyze(text)
        entities = LightweightCivicExtractor.extract_entities(text)
        is_esc, esc_reasons, sla = LightweightCivicExtractor.determine_escalation_rules(
            text, entities, res.priority, res.severity, res.category
        )

        # Check conditions
        if "expected_categories" in tc:
            cat_match = (res.category in tc["expected_categories"])
        else:
            cat_match = (res.category == tc.get("expected_category"))
        griev_match = (res.is_grievance == tc["expected_grievance"])
        
        prio_match = True
        if "expected_priority" in tc:
            prio_match = (res.priority == tc["expected_priority"])
        elif "min_priority" in tc and tc["min_priority"] == "high":
            prio_match = res.priority in ["high", "critical"]

        test_passed = cat_match and griev_match and prio_match

        if test_passed:
            passed += 1
            status_str = "✅ PASS"
        else:
            failed += 1
            status_str = "❌ FAIL"

        print(f"  Result: {status_str}")
        print(f"  Predicted Category: {res.category} (Expected: {tc.get('expected_category') or tc.get('expected_categories')})")
        print(f"  Grievance Status:   {res.is_grievance} (Expected: {tc['expected_grievance']})")
        print(f"  Priority / Severity: {res.priority} / {res.severity} (Confidence: {res.confidence*100:.1f}%)")
        print(f"  Language Profile:   {res.language_name} ({res.script}, code-mixed={res.is_code_mixed})")
        if entities.safety_hazard:
            print(f"  ⚡ Hazard Flag:       {entities.hazard_types} (SLA: {sla}h | Escalated: {is_esc})")

        results.append({
            "id": tc["id"],
            "description": tc["description"],
            "passed": test_passed,
            "text": text,
            "predicted_category": res.category,
            "expected_category": tc.get("expected_category") or str(tc.get("expected_categories")),
            "predicted_grievance": res.is_grievance,
            "expected_grievance": tc["expected_grievance"],
            "priority": res.priority,
            "confidence": res.confidence,
        })

    print("\n" + "=" * 70)
    print(f"  Summary: {passed}/{len(TEST_CASES)} Passed ({passed/len(TEST_CASES)*100:.1f}%) | {failed} Failed")
    print("=" * 70)

    # Save results to artifacts
    out_dir = Path("artifacts/evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "regression_test_results.json", "w", encoding="utf-8") as f:
        json.dump({"total": len(TEST_CASES), "passed": passed, "failed": failed, "tests": results}, f, indent=2)

    return passed == len(TEST_CASES)


if __name__ == "__main__":
    success = asyncio.run(run_regression_tests())
    sys.exit(0 if success else 1)
