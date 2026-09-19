"""
CivicMind AI — Live Civic Map Routes (Module 4)
Endpoints:
GET /api/map/complaints — Return individual geolocated complaint markers
GET /api/map/incidents  — Return incident centroid markers and polygon footprints
"""
from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timezone

from app.schemas.schemas import (
    MapDataResponse,
    MapComplaintMarker,
    MapIncidentMarker,
)
from app.services.incident_service import incident_service
from app.services.duplicate_service import duplicate_detection_service
from app.data.demo_data import DEMO_COMPLAINTS
from app.core.config import settings

router = APIRouter()


def _ensure_service_initialized():
    if not incident_service._complaints_store:
        try:
            from scripts.seed_module4_demo import generate_module4_demo_complaints
            from app.services.muril_classifier import muril_classifier_service
            complaints = generate_module4_demo_complaints()
            for c in complaints:
                if "embedding" not in c or not c["embedding"]:
                    c["embedding"] = muril_classifier_service.get_embedding(c["text"])
            incident_service.seed_complaints(complaints)
            incident_service.recompute_all_incidents(time_window_hours=720, dry_run=False)
        except Exception:
            from app.data.demo_data import DEMO_COMPLAINTS
            from app.services.muril_classifier import muril_classifier_service
            enriched = []
            for c in DEMO_COMPLAINTS:
                c_copy = dict(c)
                if "embedding" not in c_copy or not c_copy["embedding"]:
                    c_copy["embedding"] = muril_classifier_service.get_embedding(c_copy["text"])
                enriched.append(c_copy)
            incident_service.seed_complaints(enriched)
            incident_service.recompute_all_incidents(time_window_hours=720, dry_run=False)


@router.get("/map/complaints", response_model=MapDataResponse)
async def get_map_complaints(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    incident_id: Optional[str] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lng: Optional[float] = None,
    max_lng: Optional[float] = None,
):
    """
    Returns geolocated complaint markers with viewport bounding box and category/priority filters.
    """
    _ensure_service_initialized()
    all_complaints = list(incident_service._complaints_store.values())

    # Filter geolocated
    geolocated = []
    for c in all_complaints:
        coords = duplicate_detection_service.validate_coordinates(c.get("latitude"), c.get("longitude"))
        if coords is None:
            continue

        lat, lng = coords

        # Viewport bounding box filter if provided
        if min_lat is not None and lat < min_lat:
            continue
        if max_lat is not None and lat > max_lat:
            continue
        if min_lng is not None and lng < min_lng:
            continue
        if max_lng is not None and lng > max_lng:
            continue

        if category and str(c.get("category", "")).lower() != category.lower():
            continue
        if priority and str(c.get("priority", "")).lower() != priority.lower():
            continue
        if incident_id:
            assigned_inc = incident_service._complaint_to_incident.get(str(c.get("id")))
            if assigned_inc != incident_id:
                continue

        created_ts = c.get("created_at")
        if isinstance(created_ts, str):
            try:
                created_ts = datetime.fromisoformat(created_ts.replace("Z", "+00:00"))
            except Exception:
                created_ts = datetime.now(timezone.utc)

        marker = MapComplaintMarker(
            id=str(c["id"]),
            complaint_code=c["complaint_code"],
            category=c.get("category"),
            priority=c.get("priority", "medium"),
            status=c.get("status", "open"),
            language=c.get("language"),
            latitude=lat,
            longitude=lng,
            location_text=c.get("location_text"),
            ward=c.get("ward"),
            text_preview=c.get("text", "")[:100] + ("..." if len(c.get("text", "")) > 100 else ""),
            created_at=created_ts,
            incident_id=incident_service._complaint_to_incident.get(str(c["id"])),
            is_code_mixed=c.get("is_code_mixed", False),
        )
        geolocated.append(marker)

    # Get active incidents as well for overlay
    incidents_list = incident_service.get_all_incidents()
    incident_markers = []
    for inc in incidents_list:
        if inc.get("center_latitude") and inc.get("center_longitude"):
            incident_markers.append(
                MapIncidentMarker(
                    id=str(inc["id"]),
                    incident_code=inc["incident_code"],
                    title=inc["title"],
                    category=inc["category"],
                    priority=inc["priority"],
                    status=inc["status"],
                    complaint_count=inc["complaint_count"],
                    center_latitude=inc["center_latitude"],
                    center_longitude=inc["center_longitude"],
                    affected_area=inc.get("affected_area"),
                    geometry=inc.get("geometry"),
                    trend=inc.get("trend", "STABLE"),
                    is_emerging=inc.get("is_emerging", False),
                    first_reported_at=inc.get("first_reported_at"),
                    last_reported_at=inc.get("last_reported_at"),
                )
            )

    return MapDataResponse(
        markers=geolocated,
        complaints=geolocated,
        incidents=incident_markers,
        total=len(geolocated),
        total_geolocated=len(geolocated),
        center_lat=settings.DEMO_MAP_LAT,
        center_lng=settings.DEMO_MAP_LNG,
    )


@router.get("/map/incidents", response_model=List[MapIncidentMarker])
async def get_map_incidents(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    Returns incident markers, centroids, and polygon boundaries for live map visualization.
    """
    _ensure_service_initialized()
    incidents = incident_service.get_all_incidents(category=category, priority=priority, status=status)

    markers = []
    for inc in incidents:
        if inc.get("center_latitude") and inc.get("center_longitude"):
            markers.append(
                MapIncidentMarker(
                    id=str(inc["id"]),
                    incident_code=inc["incident_code"],
                    title=inc["title"],
                    category=inc["category"],
                    priority=inc["priority"],
                    status=inc["status"],
                    complaint_count=inc["complaint_count"],
                    center_latitude=inc["center_latitude"],
                    center_longitude=inc["center_longitude"],
                    affected_area=inc.get("affected_area"),
                    geometry=inc.get("geometry"),
                    trend=inc.get("trend", "STABLE"),
                    is_emerging=inc.get("is_emerging", False),
                    first_reported_at=inc.get("first_reported_at"),
                    last_reported_at=inc.get("last_reported_at"),
                )
            )
    return markers
