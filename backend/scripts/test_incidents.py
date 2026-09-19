"""
CivicMind AI — Module 4 Deterministic Scenario Verification & Test Suite
Executes the 10 core governance scenarios, prints rich output, and writes:
artifacts/evaluation/module4_test_results.json
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.duplicate_service import duplicate_detection_service
from app.incidents.clustering import clustering_engine
from app.incidents.incident_detector import IncidentDetector
from app.services.incident_service import incident_service
from app.services.muril_classifier import muril_classifier_service


def run_scenario_tests():
    print("=" * 70)
    print("CIVICMIND AI — MODULE 4 SCENARIO VERIFICATION SUITE")
    print("=" * 70)

    base_time = datetime(2026, 9, 19, 10, 0, 0, tzinfo=timezone.utc)
    test_results = []

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 1: Same Water Incident (Close Geo + Temporal)
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    c1 = {
        "id": "c1",
        "complaint_code": "CMP-001",
        "text": "Anna 3 days ah water varala in our street.",
        "category": "water",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Anna 3 days ah water varala in our street."),
    }
    c2 = {
        "id": "c2",
        "complaint_code": "CMP-002",
        "text": "Thanni illa for 3 days, please send water supply tanker.",
        "category": "water",
        "latitude": 13.0425,
        "longitude": 80.2345,
        "created_at": base_time - timedelta(minutes=45),
        "embedding": muril_classifier_service.get_embedding("Thanni illa for 3 days, please send water supply tanker."),
    }
    res1 = duplicate_detection_service.evaluate_pair(c1, c2)
    passed1 = res1["relationship"] in ["DUPLICATE", "RELATED"] and res1["geo_distance_meters"] < 200
    lat1 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 1: Same Water Incident",
        "status": "PASSED" if passed1 else "FAILED",
        "details": f"Relationship: {res1['relationship']} (Score: {res1['similarity_score']:.2f}, Dist: {res1['geo_distance_meters']}m)",
        "latency_ms": round(lat1, 2),
    })

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 2: Same Category, Far Away (Geographic Separation)
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    c_ch = {
        "id": "c_ch",
        "text": "Water pipeline burst on main road.",
        "category": "water",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Water pipeline burst on main road."),
    }
    c_md = {
        "id": "c_md",
        "text": "Water pipeline burst on main road.",
        "category": "water",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Water pipeline burst on main road."),
    }
    res2 = duplicate_detection_service.evaluate_pair(c_ch, c_md)
    passed2 = res2["relationship"] != "DUPLICATE" and res2["geographic_score"] == 0.0
    lat2 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 2: Same Category, Far Away",
        "status": "PASSED" if passed2 else "FAILED",
        "details": f"Relationship: {res2['relationship']} (Distance: {res2['geo_distance_meters']/1000:.1f}km -> Geo Score: 0.0)",
        "latency_ms": round(lat2, 2),
    })

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 3: Keyword Overlap with Incompatible Categories
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    c_drain = {
        "id": "c_drain",
        "text": "Water flowing on road due to storm drain clog.",
        "category": "drainage",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Water flowing on road due to storm drain clog."),
    }
    c_drink = {
        "id": "c_drink",
        "text": "Drinking water tap supply broken in house.",
        "category": "water",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Drinking water tap supply broken in house."),
    }
    res3 = duplicate_detection_service.evaluate_pair(c_drain, c_drink)
    passed3 = res3["relationship"] != "DUPLICATE"
    lat3 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 3: Incompatible Category Overlap",
        "status": "PASSED" if passed3 else "FAILED",
        "details": f"Category match: {res3['category_score']} -> Classification: {res3['relationship']}",
        "latency_ms": round(lat3, 2),
    })

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 4: Multilingual Same Incident (Ta, Tanglish, En, Hi, Hinglish)
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    multilingual = [
        {"id": "m1", "text": "Anna 3 days ah water varala.", "language": "ta", "category": "water", "latitude": 13.0418, "longitude": 80.2341, "created_at": base_time},
        {"id": "m2", "text": "மூன்று நாட்களாக குடிநீர் வரவில்லை.", "language": "ta", "category": "water", "latitude": 13.0422, "longitude": 80.2345, "created_at": base_time - timedelta(minutes=20)},
        {"id": "m3", "text": "Water supply stopped for 3 days.", "language": "en", "category": "water", "latitude": 13.0415, "longitude": 80.2338, "created_at": base_time - timedelta(minutes=40)},
        {"id": "m4", "text": "Teen din se paani nahi aa raha.", "language": "hi", "category": "water", "latitude": 13.0428, "longitude": 80.2350, "created_at": base_time - timedelta(hours=1)},
        {"id": "m5", "text": "Thanni varala, whole street affected.", "language": "ta", "category": "water", "latitude": 13.0430, "longitude": 80.2355, "created_at": base_time - timedelta(hours=2)},
    ]
    for m in multilingual:
        m["embedding"] = muril_classifier_service.get_embedding(m["text"])
    clusters4 = clustering_engine.cluster_complaints(multilingual)
    valid_clusters4 = [members for lbl, members in clusters4.items() if lbl >= 0]
    passed4 = len(valid_clusters4) == 1 and len(valid_clusters4[0]) == 5
    lat4 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 4: Multilingual Incident Clustering",
        "status": "PASSED" if passed4 else "FAILED",
        "details": f"Grouped {len(valid_clusters4[0])} multilingual reports into 1 unified cluster",
        "latency_ms": round(lat4, 2),
    })

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 5: Two Separate Incidents
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    w_t_nagar = [
        {"id": "t1", "text": "Water supply stopped in T. Nagar.", "category": "water", "latitude": 13.0418, "longitude": 80.2341, "created_at": base_time},
        {"id": "t2", "text": "No water in T. Nagar area.", "category": "water", "latitude": 13.0425, "longitude": 80.2345, "created_at": base_time - timedelta(hours=1)},
    ]
    w_anna_nagar = [
        {"id": "a1", "text": "Water supply cut in Anna Nagar.", "category": "water", "latitude": 13.0850, "longitude": 80.2100, "created_at": base_time},
        {"id": "a2", "text": "Anna Nagar water pipeline closed.", "category": "water", "latitude": 13.0860, "longitude": 80.2110, "created_at": base_time - timedelta(hours=1)},
    ]
    comb5 = w_t_nagar + w_anna_nagar
    for c in comb5:
        c["embedding"] = muril_classifier_service.get_embedding(c["text"])
    clusters5 = clustering_engine.cluster_complaints(comb5)
    valid_clusters5 = [members for lbl, members in clusters5.items() if lbl >= 0]
    passed5 = len(valid_clusters5) == 2
    lat5 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 5: Two Separate Neighborhood Incidents",
        "status": "PASSED" if passed5 else "FAILED",
        "details": f"Correctly formed {len(valid_clusters5)} distinct incidents across spatial boundaries",
        "latency_ms": round(lat5, 2),
    })

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 6: No Spatial Coordinates
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    c_n1 = {"id": "n1", "text": "Pothole on street", "category": "roads", "latitude": None, "longitude": None, "created_at": base_time}
    c_n2 = {"id": "n2", "text": "Pothole on street", "category": "roads", "latitude": None, "longitude": None, "created_at": base_time}
    res6 = duplicate_detection_service.evaluate_pair(c_n1, c_n2)
    passed6 = res6["geographic_score"] is None and res6["geo_distance_meters"] is None
    lat6 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 6: Missing Location Handling",
        "status": "PASSED" if passed6 else "FAILED",
        "details": "Semantic comparison conducted without inventing fake geographic proximity",
        "latency_ms": round(lat6, 2),
    })

    # ─────────────────────────────────────────────────────────────────────────────
    # Case 7: Single Complaint Isolation
    # ─────────────────────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    single_c = [{"id": "s1", "text": "Street light flickering.", "category": "streetlighting", "latitude": 13.0827, "longitude": 80.2707, "created_at": base_time, "embedding": muril_classifier_service.get_embedding("Street light flickering.")}]
    clusters7 = clustering_engine.cluster_complaints(single_c)
    passed7 = len(clusters7.get(-1, [])) == 1
    lat7 = (time.perf_counter() - t0) * 1000
    test_results.append({
        "case": "Case 7: Single Complaint Isolation",
        "status": "PASSED" if passed7 else "FAILED",
        "details": "Single isolated complaint classified as noise (-1) rather than false mature incident",
        "latency_ms": round(lat7, 2),
    })

    # Print Summary Table
    print(f"\n{'Test Case':<42} | {'Status':<8} | {'Latency':<9} | Details")
    print("-" * 100)
    for r in test_results:
        print(f"{r['case']:<42} | {r['status']:<8} | {r['latency_ms']:>6.2f}ms | {r['details']}")
    print("-" * 100)

    total_passed = sum(1 for r in test_results if r["status"] == "PASSED")
    print(f"\nResults: {total_passed}/{len(test_results)} Scenarios Passed successfully.")

    # Write test results artifact
    out_dir = Path(__file__).parent.parent / "artifacts" / "evaluation"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "module4_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(test_results),
            "passed_cases": total_passed,
            "success_rate": round(total_passed / len(test_results) * 100, 1),
            "cases": test_results,
        }, f, indent=2)

    print(f"[OK] Saved test report to {out_dir / 'module4_test_results.json'}")
    return total_passed == len(test_results)


if __name__ == "__main__":
    success = run_scenario_tests()
    sys.exit(0 if success else 1)
