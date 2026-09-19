"""
CivicMind AI — Incidents API Router (Module 4)
Endpoints:
GET  /api/incidents
GET  /api/incidents/{id}
POST /api/incidents/recompute
POST /api/incidents/{id}/merge
POST /api/incidents/{id}/split
POST /api/incidents/{id}/status
GET  /api/incidents/{id}/complaints
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
from typing import Optional

from app.schemas.schemas import (
    IncidentResponse,
    IncidentDetailResponse,
    IncidentListResponse,
    ComplaintResponse,
    ComplaintListResponse,
    RecomputeIncidentsRequest,
    RecomputeIncidentsResponse,
    MergeIncidentsRequest,
    SplitIncidentRequest,
    IncidentStatusUpdateRequest,
)
from app.services.incident_service import incident_service
from app.data.demo_data import DEMO_COMPLAINTS

router = APIRouter()


def _ensure_service_initialized():
    """Ensures incident service has seeded complaints if empty."""
    if not incident_service._complaints_store:
        # Pre-populate embeddings for demo complaints
        from app.services.muril_classifier import muril_classifier_service
        enriched = []
        for c in DEMO_COMPLAINTS:
            c_copy = dict(c)
            if "embedding" not in c_copy or not c_copy["embedding"]:
                c_copy["embedding"] = muril_classifier_service.get_embedding(c_copy["text"])
            enriched.append(c_copy)
        incident_service.seed_complaints(enriched)
        incident_service.recompute_all_incidents(time_window_hours=720)


def _to_incident_response(inc: dict) -> IncidentResponse:
    signals = inc.get("confidence_signals")
    return IncidentResponse(
        id=str(inc["id"]),
        incident_code=inc["incident_code"],
        title=inc["title"],
        description=inc.get("description"),
        category=inc["category"],
        subcategory=inc.get("subcategory"),
        priority=inc.get("priority", "medium"),
        status=inc.get("status", "detected"),
        complaint_count=inc.get("complaint_count", 0),
        affected_area=inc.get("affected_area"),
        center_latitude=inc.get("center_latitude"),
        center_longitude=inc.get("center_longitude"),
        geometry=inc.get("geometry"),
        first_reported_at=inc.get("first_reported_at"),
        last_reported_at=inc.get("last_reported_at"),
        started_at=inc.get("started_at"),
        resolved_at=inc.get("resolved_at"),
        primary_department=inc.get("primary_department"),
        secondary_departments=inc.get("secondary_departments") or [],
        confidence=inc.get("confidence", 0.85),
        confidence_signals=signals,
        trend=inc.get("trend", "STABLE"),
        complaints_per_hour=inc.get("complaints_per_hour", 0.0),
        is_emerging=inc.get("is_emerging", False),
        languages=inc.get("languages") or [],
        priority_distribution=inc.get("priority_distribution") or {},
        department_distribution=inc.get("department_distribution") or {},
        detection_method=inc.get("detection_method", "SEMANTIC_GEO_TEMPORAL_CLUSTER"),
        algorithm_version=inc.get("algorithm_version", "incident-v1.0"),
        created_at=inc.get("created_at") or datetime.now(timezone.utc),
        updated_at=inc.get("updated_at") or datetime.now(timezone.utc),
    )


@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    trend: Optional[str] = None,
):
    """
    Returns active civic incidents with filtering, sorting, and KPI summary counters.
    """
    _ensure_service_initialized()

    all_incs = incident_service.get_all_incidents()
    active_count = sum(1 for inc in all_incs if inc.get("status") not in ["resolved", "closed", "false_positive"])
    emerging_count = sum(1 for inc in all_incs if inc.get("is_emerging"))
    critical_count = sum(1 for inc in all_incs if str(inc.get("priority")).lower() == "critical")
    rising_count = sum(1 for inc in all_incs if str(inc.get("trend")).upper() == "RISING")

    filtered = incident_service.get_all_incidents(
        status=status,
        priority=priority,
        category=category,
        trend=trend,
    )

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = filtered[start:end]

    return IncidentListResponse(
        incidents=[_to_incident_response(inc) for inc in page_data],
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        emerging_count=emerging_count,
        critical_count=critical_count,
        rising_count=rising_count,
    )


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident_detail(incident_id: str):
    """
    Retrieves complete incident details including member complaints, timeline, and cohesion evidence.
    """
    _ensure_service_initialized()

    inc = incident_service.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    base_resp = _to_incident_response(inc)

    # Format member complaints
    members = []
    for c in inc.get("member_complaints", []):
        members.append(
            ComplaintResponse(
                id=c["id"],
                complaint_code=c["complaint_code"],
                text=c["text"],
                language=c.get("language"),
                script=c.get("script"),
                is_code_mixed=c.get("is_code_mixed", False),
                detected_languages=c.get("detected_languages"),
                is_grievance=c.get("is_grievance"),
                category=c.get("category"),
                subcategory=c.get("subcategory"),
                severity=c.get("severity"),
                priority=c.get("priority", "medium"),
                confidence=c.get("confidence"),
                entities=c.get("entities"),
                duration_mentioned=c.get("duration_mentioned"),
                latitude=c.get("latitude"),
                longitude=c.get("longitude"),
                location_text=c.get("location_text"),
                ward=c.get("ward"),
                ai_explanation=c.get("ai_explanation"),
                department_id=c.get("department_id"),
                department_name=c.get("department_name"),
                incident_id=inc["id"],
                status=c.get("status", "open"),
                is_demo=c.get("is_demo", True),
                created_at=c.get("created_at") or datetime.now(timezone.utc),
                updated_at=c.get("updated_at") or datetime.now(timezone.utc),
            )
        )

    explanation = (
        f"Detected via {inc.get('detection_method', 'DBSCAN')} clustering. "
        f"Grouped {len(members)} complaints with {base_resp.confidence*100:.0f}% cohesion "
        f"across {len(base_resp.languages)} linguistic profiles in {base_resp.affected_area}."
    )

    return IncidentDetailResponse(
        **base_resp.model_dump(),
        member_complaints=members,
        timeline=inc.get("timeline") or [],
        explanation=explanation,
    )


@router.post("/incidents/recompute", response_model=RecomputeIncidentsResponse)
async def recompute_incidents(req: RecomputeIncidentsRequest):
    """
    Admin endpoint: Triggers full spatio-temporal DBSCAN recomputation across the time window.
    """
    _ensure_service_initialized()

    res = incident_service.recompute_all_incidents(
        time_window_hours=req.hours,
        category=req.category,
        dry_run=req.dry_run,
    )

    incidents_resp = [_to_incident_response(i) for i in res["incidents"]]
    return RecomputeIncidentsResponse(
        status=res["status"],
        dry_run=res["dry_run"],
        time_window_hours=res["time_window_hours"],
        analyzed_complaints_count=res["analyzed_complaints_count"],
        formed_incidents_count=res["formed_incidents_count"],
        merged_incidents_count=res["merged_incidents_count"],
        incidents=incidents_resp,
        runtime_ms=res["runtime_ms"],
        timestamp=res["timestamp"],
    )


@router.post("/incidents/{incident_id}/merge", response_model=IncidentResponse)
async def merge_incident(incident_id: str, req: MergeIncidentsRequest):
    """
    Officer operation: Merges target incident into this incident.
    """
    _ensure_service_initialized()
    try:
        merged = incident_service.merge_incidents(
            source_incident_id=req.target_incident_id,
            target_incident_id=incident_id,
            reason=req.reason or "Officer command merge",
        )
        return _to_incident_response(merged)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/split")
async def split_incident(incident_id: str, req: SplitIncidentRequest):
    """
    Officer operation: Splits specified complaints from an incident into a new child cluster.
    """
    _ensure_service_initialized()
    try:
        orig, new_inc = incident_service.split_incident(
            incident_id=incident_id,
            complaint_ids_for_new=req.complaint_ids_for_new_incident,
            reason=req.reason or "Officer command split",
        )
        return {
            "original_incident": _to_incident_response(orig),
            "new_incident": _to_incident_response(new_inc),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/incidents/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(incident_id: str, req: IncidentStatusUpdateRequest):
    """
    Updates incident status across the lifecycle.
    """
    _ensure_service_initialized()
    try:
        updated = incident_service.update_status(
            incident_id=incident_id,
            new_status=req.status,
            notes=req.notes,
        )
        try:
            from app.api.routes.command_center import record_audit_event
            record_audit_event(
                event_type="INCIDENT_STATUS_CHANGE",
                target_type="incident",
                target_id=incident_id,
                actor="Command Center Officer",
                summary=f"Incident {incident_id} status updated to {req.status.upper()}",
                details={"status": req.status, "notes": req.notes},
            )
        except Exception:
            pass

        return _to_incident_response(updated)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/incidents/{incident_id}/complaints", response_model=ComplaintListResponse)
async def get_incident_complaints(
    incident_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Paginated member complaints for an incident.
    """
    _ensure_service_initialized()
    inc = incident_service.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    members = inc.get("member_complaints", [])
    total = len(members)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = members[start:end]

    from app.api.routes.grievances import _to_response
    return ComplaintListResponse(
        complaints=[_to_response(c) for c in page_data],
        total=total,
        page=page,
        page_size=page_size,
    )
