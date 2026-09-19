"""
CivicMind AI — Module 4 Unit Tests (Duplicate Detection, Clustering & Incident Intelligence)
Covers all 10 required governance & algorithmic scenarios:
1. Case 1: Same Water Incident (Close coordinates + timestamps -> DUPLICATE / RELATED)
2. Case 2: Same Category, Far Away (Geographic distance prevents false clustering)
3. Case 3: Keyword Overlap with Incompatible Categories
4. Case 4: Multilingual Clustering (Tamil, Tanglish, English, Hindi, Hinglish -> One incident)
5. Case 5: Two Separate Incidents (Distinct neighborhoods / time windows)
6. Case 6: Complaints with Missing Spatial Coordinates (No fabricated geo proximity)
7. Case 7: Single Complaint Isolation (Does not form mature incident)
8. Case 8: Incident Merge & Split Audit Trail
9. Case 9: Incident Lifecycle State Machine
10. Case 10: Idempotent Reclustering
"""
import pytest
from datetime import datetime, timezone, timedelta
import uuid

from app.services.duplicate_service import duplicate_detection_service
from app.incidents.clustering import clustering_engine
from app.incidents.incident_detector import IncidentDetector
from app.services.incident_service import incident_service
from app.services.muril_classifier import muril_classifier_service


@pytest.fixture
def base_time():
    return datetime(2026, 9, 19, 10, 0, 0, tzinfo=timezone.utc)


def test_coordinate_validation():
    """Validates boundary handling and rejection of impossible coordinates."""
    assert duplicate_detection_service.validate_coordinates(13.0827, 80.2707) == (13.0827, 80.2707)
    assert duplicate_detection_service.validate_coordinates(0.0, 0.0) == (0.0, 0.0)
    assert duplicate_detection_service.validate_coordinates(-89.9, -179.9) == (-89.9, -179.9)
    assert duplicate_detection_service.validate_coordinates(95.0, 80.0) is None
    assert duplicate_detection_service.validate_coordinates(13.0, 195.0) is None
    assert duplicate_detection_service.validate_coordinates(float('nan'), 80.0) is None
    assert duplicate_detection_service.validate_coordinates(None, 80.0) is None
    assert duplicate_detection_service.validate_coordinates("invalid", 80.0) is None


def test_haversine_distance():
    """Tests great-circle distance computation between Chennai landmarks."""
    # T. Nagar (13.0418, 80.2341) to Panagal Park (13.0428, 80.2351) ~150 meters
    dist = duplicate_detection_service.haversine_distance_meters(13.0418, 80.2341, 13.0428, 80.2351)
    assert 100 < dist < 200

    # Chennai to Coimbatore (~420 km)
    dist_cbe = duplicate_detection_service.haversine_distance_meters(13.0827, 80.2707, 11.0168, 76.9558)
    assert 400000 < dist_cbe < 450000


def test_case_1_same_water_incident(base_time):
    """Case 1: Same Water Incident (Close coordinates + timestamps)."""
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

    eval_res = duplicate_detection_service.evaluate_pair(c1, c2)
    assert eval_res["relationship"] in ["DUPLICATE", "RELATED"]
    assert eval_res["similarity_score"] >= 0.70
    assert eval_res["geo_distance_meters"] < 200
    assert eval_res["category_score"] == 1.0


def test_case_2_same_category_far_away(base_time):
    """Case 2: Same Category, Far Away (Geographic distance prevents false clustering)."""
    c_chennai = {
        "id": "c_chennai",
        "text": "Water pipeline burst causing flood on road.",
        "category": "water",
        "latitude": 13.0827,
        "longitude": 80.2707,  # Chennai
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Water pipeline burst causing flood on road."),
    }
    c_madurai = {
        "id": "c_madurai",
        "text": "Water pipeline burst causing flood on road.",
        "category": "water",
        "latitude": 9.9252,
        "longitude": 78.1198,   # Madurai (~420km away)
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Water pipeline burst causing flood on road."),
    }

    eval_res = duplicate_detection_service.evaluate_pair(c_chennai, c_madurai)
    assert eval_res["geo_distance_meters"] > 400000
    assert eval_res["geographic_score"] == 0.0
    # Must NOT be classified as DUPLICATE despite identical text because of geographical separation
    assert eval_res["relationship"] != "DUPLICATE"


def test_case_3_same_words_different_category(base_time):
    """Case 3: Ensure keyword overlap across incompatible categories does not merge."""
    c_rain = {
        "id": "c_rain",
        "text": "Rain water accumulating on road causing huge waterlogging.",
        "category": "drainage",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Rain water accumulating on road causing huge waterlogging."),
    }
    c_drinking = {
        "id": "c_drinking",
        "text": "Drinking water supply not received for past week.",
        "category": "water",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Drinking water supply not received for past week."),
    }

    eval_res = duplicate_detection_service.evaluate_pair(c_rain, c_drinking)
    assert eval_res["relationship"] != "DUPLICATE"


def test_case_4_multilingual_incident_clustering(base_time):
    """Case 4: Multi-Language Same Incident (Tamil, Tanglish, English, Hindi, Hinglish -> One incident)."""
    multilingual_batch = [
        {"id": "m1", "text": "Anna 3 days ah water varala.", "language": "ta", "category": "water", "latitude": 13.0418, "longitude": 80.2341, "created_at": base_time},
        {"id": "m2", "text": "மூன்று நாட்களாக குடிநீர் வரவில்லை.", "language": "ta", "category": "water", "latitude": 13.0422, "longitude": 80.2345, "created_at": base_time - timedelta(minutes=20)},
        {"id": "m3", "text": "Water supply stopped for 3 days.", "language": "en", "category": "water", "latitude": 13.0415, "longitude": 80.2338, "created_at": base_time - timedelta(minutes=40)},
        {"id": "m4", "text": "Teen din se paani nahi aa raha.", "language": "hi", "category": "water", "latitude": 13.0428, "longitude": 80.2350, "created_at": base_time - timedelta(hours=1)},
        {"id": "m5", "text": "Thanni varala, whole street affected.", "language": "ta", "category": "water", "latitude": 13.0430, "longitude": 80.2355, "created_at": base_time - timedelta(hours=2)},
    ]

    for m in multilingual_batch:
        m["embedding"] = muril_classifier_service.get_embedding(m["text"])

    clusters = clustering_engine.cluster_complaints(multilingual_batch)
    # Filter non-noise clusters
    valid_clusters = [members for lbl, members in clusters.items() if lbl >= 0]
    assert len(valid_clusters) == 1
    assert len(valid_clusters[0]) == 5

    incident = IncidentDetector.form_incident_from_cluster(valid_clusters[0])
    assert incident["category"] == "water"
    assert incident["complaint_count"] == 5
    assert len(incident["languages"]) >= 2
    assert incident["center_latitude"] is not None
    assert incident["confidence"] >= 0.80


def test_case_5_two_separate_incidents(base_time):
    """Case 5: Two Separate Incidents (Distinct neighborhoods / times -> 2 clusters)."""
    water_t_nagar = [
        {"id": "t1", "text": "Water supply stopped in T. Nagar.", "category": "water", "latitude": 13.0418, "longitude": 80.2341, "created_at": base_time},
        {"id": "t2", "text": "No water in T. Nagar area.", "category": "water", "latitude": 13.0425, "longitude": 80.2345, "created_at": base_time - timedelta(hours=1)},
    ]
    water_anna_nagar = [
        {"id": "a1", "text": "Water supply cut in Anna Nagar.", "category": "water", "latitude": 13.0850, "longitude": 80.2100, "created_at": base_time},
        {"id": "a2", "text": "Anna Nagar water pipeline closed.", "category": "water", "latitude": 13.0860, "longitude": 80.2110, "created_at": base_time - timedelta(hours=1)},
    ]

    combined = water_t_nagar + water_anna_nagar
    for c in combined:
        c["embedding"] = muril_classifier_service.get_embedding(c["text"])

    clusters = clustering_engine.cluster_complaints(combined)
    valid_clusters = [members for lbl, members in clusters.items() if lbl >= 0]
    assert len(valid_clusters) == 2


def test_case_6_no_location_handling(base_time):
    """Case 6: Complaints with Missing Spatial Coordinates (Graceful semantic handling without fake geo match)."""
    c_nocoord1 = {
        "id": "nc1",
        "text": "Water supply not coming in house.",
        "category": "water",
        "latitude": None,
        "longitude": None,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Water supply not coming in house."),
    }
    c_nocoord2 = {
        "id": "nc2",
        "text": "Water supply not coming in house.",
        "category": "water",
        "latitude": None,
        "longitude": None,
        "created_at": base_time - timedelta(hours=2),
        "embedding": muril_classifier_service.get_embedding("Water supply not coming in house."),
    }

    eval_res = duplicate_detection_service.evaluate_pair(c_nocoord1, c_nocoord2)
    assert eval_res["geographic_score"] is None
    assert eval_res["geo_distance_meters"] is None
    assert "no spatial coordinates" in eval_res["explanation"]


def test_case_7_single_complaint_isolation(base_time):
    """Case 7: Single Complaint Isolation (Does not form mature cluster)."""
    single = [{
        "id": "s1",
        "text": "Single complaint about a tree branch.",
        "category": "roads",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "created_at": base_time,
        "embedding": muril_classifier_service.get_embedding("Single complaint about a tree branch."),
    }]

    clusters = clustering_engine.cluster_complaints(single)
    # Single sample marked as noise (-1)
    assert len(clusters.get(-1, [])) == 1


def test_case_8_incident_merge_and_split(base_time):
    """Case 8: Incident Merging & Splitting Audit Trail."""
    svc = incident_service
    c_a1 = {"id": "ca1", "text": "Water cut North", "category": "water", "latitude": 13.0418, "longitude": 80.2341, "created_at": base_time}
    c_a2 = {"id": "ca2", "text": "Water cut North", "category": "water", "latitude": 13.0422, "longitude": 80.2345, "created_at": base_time}
    c_b1 = {"id": "cb1", "text": "Water cut South", "category": "water", "latitude": 13.0430, "longitude": 80.2350, "created_at": base_time}
    c_b2 = {"id": "cb2", "text": "Water cut South", "category": "water", "latitude": 13.0435, "longitude": 80.2355, "created_at": base_time}

    all_c = [c_a1, c_a2, c_b1, c_b2]
    for c in all_c:
        c["embedding"] = muril_classifier_service.get_embedding(c["text"])
    svc.seed_complaints(all_c)

    inc1 = IncidentDetector.form_incident_from_cluster([c_a1, c_a2])
    inc2 = IncidentDetector.form_incident_from_cluster([c_b1, c_b2])

    svc._incidents_store[inc1["id"]] = inc1
    svc._incident_memberships[inc1["id"]] = ["ca1", "ca2"]
    svc._incidents_store[inc2["id"]] = inc2
    svc._incident_memberships[inc2["id"]] = ["cb1", "cb2"]

    # Merge inc2 into inc1
    merged = svc.merge_incidents(source_incident_id=inc2["id"], target_incident_id=inc1["id"], reason="Officer area merge")
    assert merged["complaint_count"] == 4
    assert inc2["id"] in merged.get("merged_from_ids", [])
    assert inc2["id"] not in svc._incidents_store

    # Split ca1, ca2 out into new incident
    orig, split_inc = svc.split_incident(incident_id=inc1["id"], complaint_ids_for_new=["ca1", "ca2"], reason="Sub-area division")
    assert orig["complaint_count"] == 2
    assert split_inc["complaint_count"] == 2
    assert split_inc.get("split_from_id") == inc1["id"]


def test_case_9_incident_lifecycle():
    """Case 9: Incident Lifecycle State Machine."""
    svc = incident_service
    dummy_inc = {
        "id": "lifecycle-test-id",
        "incident_code": "INC-TEST-01",
        "title": "Test Incident",
        "category": "roads",
        "priority": "high",
        "status": "detected",
        "complaint_count": 5,
        "created_at": datetime.now(timezone.utc),
    }
    svc._incidents_store["lifecycle-test-id"] = dummy_inc

    for st in ["investigating", "acknowledged", "in_progress", "resolved", "closed"]:
        updated = svc.update_status("lifecycle-test-id", st)
        assert updated["status"] == st


def test_case_10_idempotency(base_time):
    """Case 10: Idempotent Reclustering produces identical state."""
    svc = incident_service
    batch = [
        {"id": "idemp-1", "text": "Pothole on 1st avenue", "category": "roads", "latitude": 13.0850, "longitude": 80.2100, "created_at": base_time},
        {"id": "idemp-2", "text": "Pothole on 2nd avenue", "category": "roads", "latitude": 13.0855, "longitude": 80.2105, "created_at": base_time},
    ]
    for c in batch:
        c["embedding"] = muril_classifier_service.get_embedding(c["text"])
    svc.seed_complaints(batch)

    res1 = svc.recompute_all_incidents(time_window_hours=72, dry_run=False)
    res2 = svc.recompute_all_incidents(time_window_hours=72, dry_run=False)

    assert res1["formed_incidents_count"] == res2["formed_incidents_count"]
    assert len(svc._incidents_store) == res1["formed_incidents_count"]
