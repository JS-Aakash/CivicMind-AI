"""
CivicMind AI — Grievances API Router (Module 3 & Module 4 Enhanced)
Endpoints:
GET /api/grievances
GET /api/grievances/{id}
GET /api/grievances/{id}/duplicates
GET /api/grievances/{id}/related
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone
from typing import Optional

from app.schemas.schemas import (
    ComplaintResponse,
    ComplaintListResponse,
    ComplaintDuplicatesResponse,
    ComplaintRelationshipItem,
    ComplaintCreate,
    MultimodalComplaintCreate,
    CitizenTrackingResponse,
    CitizenStatusTimelineEvent,
)
from app.services.duplicate_service import duplicate_detection_service
from app.services.incident_service import incident_service
from app.services.grievance_service import grievance_service
from app.services.muril_classifier import muril_classifier_service
from app.services.vision_service import vision_service
from app.services.voice_service import voice_service
from app.services.media_service import media_service
import uuid
import random

router = APIRouter()


def _ensure_service_initialized():
    if not incident_service._complaints_store:
        try:
            from scripts.seed_module4_demo import generate_module4_demo_complaints
            complaints = generate_module4_demo_complaints()
            for c in complaints:
                if "embedding" not in c or not c["embedding"]:
                    c["embedding"] = muril_classifier_service.get_embedding(c["text"])
            incident_service.seed_complaints(complaints)
            incident_service.recompute_all_incidents(time_window_hours=720, dry_run=False)
        except Exception:
            from app.data.demo_data import DEMO_COMPLAINTS
            enriched = []
            for c in DEMO_COMPLAINTS:
                c_copy = dict(c)
                if "embedding" not in c_copy or not c_copy["embedding"]:
                    c_copy["embedding"] = muril_classifier_service.get_embedding(c_copy["text"])
                enriched.append(c_copy)
            incident_service.seed_complaints(enriched)
            incident_service.recompute_all_incidents(time_window_hours=720, dry_run=False)


@router.post("/grievances", response_model=ComplaintResponse)
async def create_grievance(request: MultimodalComplaintCreate):
    """
    Submits a new citizen grievance (text, voice, image evidence, or multimodal combination):
    1. Extracts transcript from voice if audio provided
    2. Runs IndicLID language detection & MuRIL classification
    3. Gathers local Qwen3-VL structured visual evidence
    4. Evaluates visual hazard signals into Module 3 Priority & Routing engines
    5. Performs multimodal consistency & conflict checks
    6. Generates 768-dim normalized embedding
    7. Runs incremental duplicate detection and spatio-temporal incident clustering
    8. Persists into live store and returns full complaint response
    """
    _ensure_service_initialized()

    # 1. Determine grievance text from transcript or direct text input
    complaint_text = request.text or ""
    voice_record = None
    if request.edited_transcript:
        complaint_text = request.edited_transcript
    elif request.raw_transcript and not complaint_text:
        complaint_text = request.raw_transcript
    elif request.audio_id and not complaint_text:
        audio_media = media_service.get_media(request.audio_id)
        if audio_media:
            trans_res = voice_service.transcribe_audio(audio_media["storage_path"], media_id=request.audio_id)
            complaint_text = trans_res.get("raw_transcript", "")
            voice_record = trans_res

    if not complaint_text.strip():
        complaint_text = "Citizen submitted visual evidence for municipal inspection."

    # 2. Run AI analysis through MuRIL + IndicLID
    analysis = await grievance_service.analyze(
        text=complaint_text,
        location_text=request.location_text,
    )

    # 3. Process Attached Image Media with Qwen3-VL
    media_items = []
    vision_evidence_list = []
    visual_hazards = []
    for mid in request.media_ids:
        m = media_service.get_media(mid)
        if m:
            media_items.append(m)
            if m["media_type"] == "image":
                vis_res = vision_service.analyze_image(
                    image_path=m["storage_path"],
                    media_id=mid,
                    complaint_text=complaint_text,
                )
                vision_evidence_list.append(vis_res)
                for h in vis_res.get("possible_hazards", []):
                    if h and h not in visual_hazards:
                        visual_hazards.append(h)

    # 4. Integrate Visual Hazard Signals into Priority
    effective_priority = analysis.priority
    requires_review = analysis.requires_human_review or False
    conflict_detected = False
    conflict_reason = None

    if vision_evidence_list:
        primary_vis = vision_evidence_list[0]
        # Check for multimodal evidence conflict
        conflict_detected, conflict_reason = vision_service.detect_multimodal_conflict(
            text_category=analysis.category,
            vision_category=primary_vis.get("evidence_category", "OTHER"),
        )
        if conflict_detected:
            requires_review = True

        # Escalate priority if dangerous hazard visually confirmed
        vis_sev = primary_vis.get("severity_signal", "low")
        if primary_vis.get("evidence_category") == "ELECTRICAL_HAZARD" or any("wire" in h.lower() or "spark" in h.lower() for h in visual_hazards):
            effective_priority = "critical"
        elif vis_sev == "critical" and effective_priority in ["medium", "low"]:
            effective_priority = "high"

    # 5. Compute embedding
    embedding = muril_classifier_service.get_embedding(complaint_text)

    # 6. Create complaint record
    complaint_id = str(uuid.uuid4())
    complaint_code = f"GRV-{random.randint(10000, 99999)}"
    now = datetime.now(timezone.utc)

    # Validate coordinates
    coords = duplicate_detection_service.validate_coordinates(request.latitude, request.longitude)
    valid_lat = coords[0] if coords else None
    valid_lng = coords[1] if coords else None

    # Construct multimodal consistency summary
    primary_vis_data = vision_evidence_list[0] if vision_evidence_list else None
    multimodal_summary = {
        "has_voice": request.audio_id is not None or voice_record is not None,
        "has_image": len(vision_evidence_list) > 0,
        "image_count": len(vision_evidence_list),
        "visual_evidence_categories": [v.get("evidence_category") for v in vision_evidence_list],
        "visual_hazards": visual_hazards,
        "visual_confidence": primary_vis_data.get("confidence") if primary_vis_data else None,
        "conflict_detected": conflict_detected,
        "conflict_reason": conflict_reason,
        "evidence_strength": "HIGH" if (vision_evidence_list and voice_record) else ("HIGH" if vision_evidence_list else "MEDIUM"),
    }

    complaint_dict = {
        "id": complaint_id,
        "complaint_code": complaint_code,
        "text": complaint_text,
        "language": analysis.primary_language,
        "script": analysis.script,
        "is_code_mixed": analysis.is_code_mixed,
        "detected_languages": analysis.languages,
        "is_grievance": analysis.is_grievance,
        "category": analysis.category,
        "subcategory": analysis.subcategory,
        "severity": analysis.severity,
        "priority": effective_priority,
        "confidence": analysis.confidence,
        "entities": analysis.entities,
        "duration_mentioned": analysis.duration_mentioned,
        "latitude": valid_lat,
        "longitude": valid_lng,
        "location_text": request.location_text or ("GPS Location" if valid_lat else None),
        "ward": request.ward or "Ward 112",
        "ai_explanation": analysis.explanation,
        "department_id": None,
        "department_name": analysis.department_name,
        "secondary_departments": [d.model_dump() for d in (analysis.secondary_departments or [])],
        "routing_decision": "OFFICER_REVIEW" if requires_review else (analysis.routing_decision or "AUTO_ROUTE"),
        "requires_human_review": requires_review,
        "status": "open",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "embedding": embedding,
        "media": media_items,
        "voice_transcription": voice_record,
        "vision_evidence": primary_vis_data,
        "multimodal_consistency": multimodal_summary,
    }

    # 7. Save and run incremental incident clustering
    incident_service.seed_complaints([complaint_dict])
    assigned_inc = incident_service.add_complaint_incremental(complaint_dict)
    if assigned_inc:
        complaint_dict["incident_id"] = assigned_inc.get("id")

    return _to_response(complaint_dict)


def _to_response(c: dict) -> ComplaintResponse:
    inc_id = incident_service._complaint_to_incident.get(str(c.get("id"))) or c.get("incident_id")
    created_ts = c.get("created_at")
    if isinstance(created_ts, str):
        try:
            created_ts = datetime.fromisoformat(created_ts.replace("Z", "+00:00"))
        except Exception:
            created_ts = datetime.now(timezone.utc)
    elif not isinstance(created_ts, datetime):
        created_ts = datetime.now(timezone.utc)

    return ComplaintResponse(
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
        incident_id=inc_id,
        status=c.get("status", "open"),
        is_demo=c.get("is_demo", True),
        created_at=created_ts,
        updated_at=created_ts,
    )


@router.get("/grievances", response_model=ComplaintListResponse)
async def list_grievances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
):
    """List complaints with optional filtering."""
    _ensure_service_initialized()
    data = list(incident_service._complaints_store.values())

    if category:
        data = [c for c in data if str(c.get("category", "")).lower() == category.lower()]
    if priority:
        data = [c for c in data if str(c.get("priority", "")).lower() == priority.lower()]
    if status:
        data = [c for c in data if str(c.get("status", "")).lower() == status.lower()]
    if language:
        data = [c for c in data if str(c.get("language", "")).lower() == language.lower()]

    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = data[start:end]

    return ComplaintListResponse(
        complaints=[_to_response(c) for c in page_data],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/grievances/{complaint_id}", response_model=ComplaintResponse)
async def get_grievance(complaint_id: str):
    """Get a single complaint by ID or complaint_code."""
    _ensure_service_initialized()
    for c in incident_service._complaints_store.values():
        if str(c["id"]) == complaint_id or str(c.get("complaint_code")) == complaint_id:
            return _to_response(c)
    raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")


@router.get("/grievances/{complaint_id}/duplicates", response_model=ComplaintDuplicatesResponse)
async def get_complaint_duplicates(complaint_id: str):
    """
    Returns multi-factor duplicate & related grievance analysis for a specific complaint.
    """
    _ensure_service_initialized()
    target = None
    for c in incident_service._complaints_store.values():
        if str(c["id"]) == complaint_id or str(c.get("complaint_code")) == complaint_id:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    candidates = list(incident_service._complaints_store.values())
    dups_raw, rel_raw = duplicate_detection_service.find_all_relationships(target, candidates)

    def _to_rel_item(r: dict) -> ComplaintRelationshipItem:
        matched_c = incident_service._complaints_store.get(str(r["matched_complaint_id"])) or {}
        created_ts = matched_c.get("created_at")
        if isinstance(created_ts, str):
            try:
                created_ts = datetime.fromisoformat(created_ts.replace("Z", "+00:00"))
            except Exception:
                created_ts = datetime.now(timezone.utc)
        elif not isinstance(created_ts, datetime):
            created_ts = datetime.now(timezone.utc)

        return ComplaintRelationshipItem(
            id=str(r["matched_complaint_id"]),
            target_complaint_id=str(r["matched_complaint_id"]),
            target_complaint_code=r["matched_complaint_code"] or "CMP-UNK",
            target_text_preview=r["matched_text_preview"],
            target_language=matched_c.get("language", "en"),
            target_priority=matched_c.get("priority", "medium"),
            target_created_at=created_ts,
            relationship_type=r["relationship"],
            similarity_score=r["similarity_score"],
            semantic_similarity=r["semantic_similarity"],
            geographic_score=r["geographic_score"],
            temporal_score=r["temporal_score"],
            category_score=r["category_score"],
            geo_distance_meters=r["geo_distance_meters"],
            time_diff_hours=r["time_diff_hours"],
            explanation=r["explanation"],
        )

    dup_items = [_to_rel_item(d) for d in dups_raw]
    rel_items = [_to_rel_item(r) for r in rel_raw]

    return ComplaintDuplicatesResponse(
        complaint_id=str(target["id"]),
        complaint_code=target["complaint_code"],
        duplicates=dup_items,
        related=rel_items,
        total_relationships=len(dup_items) + len(rel_items),
    )


# URL Aliases for /complaints/{id}/...
@router.get("/complaints/{complaint_id}/duplicates", response_model=ComplaintDuplicatesResponse)
async def get_complaint_duplicates_alias(complaint_id: str):
    return await get_complaint_duplicates(complaint_id)


@router.get("/complaints/{complaint_id}/related", response_model=ComplaintDuplicatesResponse)
async def get_complaint_related_alias(complaint_id: str):
    return await get_complaint_duplicates(complaint_id)


# ─── Module 5: Citizen Complaint Tracking Endpoints ──────────────────────────

DEPT_TRANSLATIONS = {
    "Water Supply Department": {
        "ta": "குடிநீர் வழங்கல் துறை",
        "hi": "जल आपूर्ति विभाग",
    },
    "Roads & Highways Department": {
        "ta": "நெடுஞ்சாலைகள் மற்றும் சாலைகள் துறை",
        "hi": "सड़क एवं राजमार्ग विभाग",
    },
    "Electricity & Power Board": {
        "ta": "மின்சார வாரியம்",
        "hi": "बिजली एवं ऊर्जा बोर्ड",
    },
    "Sanitation & Solid Waste Management": {
        "ta": "துப்புரவு மற்றும் திடக்கழிவு மேலாண்மை துறை",
        "hi": "स्वच्छता एवं ठोस अपशिष्ट प्रबंधन विभाग",
    },
    "Stormwater & Drainage Department": {
        "ta": "மழைநீர் வடிகால் துறை",
        "hi": "जल निकासी एवं सीवरेज विभाग",
    },
}

SLA_MAP = {
    "critical": 2,
    "high": 24,
    "medium": 72,
    "low": 168,
}


@router.get("/citizen/complaints/{complaint_code}", response_model=CitizenTrackingResponse)
async def track_citizen_complaint(complaint_code: str):
    """
    Returns citizen-safe complaint detail view with status timeline, SLA, and multilingual responses.
    """
    _ensure_service_initialized()
    target = None
    for c in incident_service._complaints_store.values():
        if str(c.get("complaint_code")) == complaint_code or str(c["id"]) == complaint_code:
            target = c
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Complaint with code '{complaint_code}' not found")

    created_ts = target.get("created_at")
    if isinstance(created_ts, str):
        try:
            created_ts = datetime.fromisoformat(created_ts.replace("Z", "+00:00"))
        except Exception:
            created_ts = datetime.now(timezone.utc)
    elif not isinstance(created_ts, datetime):
        created_ts = datetime.now(timezone.utc)

    dept_name = target.get("department_name") or "Municipal Grievance Cell"
    prio = str(target.get("priority", "medium")).lower()
    sla_hours = SLA_MAP.get(prio, 72)
    dept_ta = DEPT_TRANSLATIONS.get(dept_name, {}).get("ta", dept_name)
    dept_hi = DEPT_TRANSLATIONS.get(dept_name, {}).get("hi", dept_name)

    # Multilingual deterministic citizen response templates
    response_messages = {
        "en": f"Your grievance has been validated and routed to {dept_name}. Target resolution: within {sla_hours} hours.",
        "ta": f"உங்கள் புகார் சரிபார்க்கப்பட்டு {dept_ta}க்கு அனுப்பப்பட்டுள்ளது. தீர்வுக்கான கால வரம்பு: {sla_hours} மணி நேரத்திற்குள்.",
        "hi": f"आपकी शिकायत सत्यापित कर {dept_hi} को भेज दी गई है। लक्षित समाधान समय: {sla_hours} घंटे के भीतर।",
    }

    # Timeline construction
    timeline = [
        CitizenStatusTimelineEvent(
            title="Complaint Lodged",
            timestamp=created_ts,
            description="Citizen submission received with evidence and location verification.",
            status="completed",
            actor="Citizen Portal",
        ),
        CitizenStatusTimelineEvent(
            title="AI Intelligence & Multimodal Triaged",
            timestamp=created_ts,
            description=f"MuRIL v1.1 identified category as {str(target.get('category', 'General')).upper()} with {prio.upper()} priority.",
            status="completed",
            actor="CivicMind AI Engine",
        ),
        CitizenStatusTimelineEvent(
            title=f"Dispatched to {dept_name}",
            timestamp=created_ts,
            description=f"Automated smart routing with {sla_hours}h SLA commitment.",
            status="completed" if target.get("status") in ["in_progress", "resolved", "closed"] else "current",
            actor="Smart Routing Dispatcher",
        ),
        CitizenStatusTimelineEvent(
            title="Municipal Field Action & Inspection",
            timestamp=created_ts,
            description="Field maintenance crew assigned to inspect and resolve on-site.",
            status="current" if target.get("status") == "in_progress" else ("completed" if target.get("status") in ["resolved", "closed"] else "upcoming"),
            actor=dept_name,
        ),
        CitizenStatusTimelineEvent(
            title="Resolution & Verification",
            timestamp=created_ts,
            description="Issue resolved and validated by citizen verification.",
            status="completed" if target.get("status") in ["resolved", "closed"] else "upcoming",
            actor="Ward Engineer",
        ),
    ]

    # Associated Incident
    assigned_inc_id = incident_service._complaint_to_incident.get(str(target["id"]))
    inc_title = None
    if assigned_inc_id:
        inc_data = incident_service._incidents_store.get(assigned_inc_id)
        if inc_data:
            inc_title = inc_data.get("title")

    return CitizenTrackingResponse(
        complaint_code=target["complaint_code"],
        submitted_at=created_ts,
        category=target.get("category") or "general",
        category_display=str(target.get("category", "General")).title(),
        priority=prio,
        status=target.get("status", "open"),
        status_display=str(target.get("status", "open")).replace("_", " ").title(),
        department_name=dept_name,
        expected_sla_hours=sla_hours,
        sla_due_at=created_ts,
        timeline=timeline,
        media=target.get("media") or [],
        ai_summary=target.get("ai_explanation") or "Grievance validated and routed to municipal authority.",
        incident_title=inc_title,
        citizen_response_message=response_messages,
    )


@router.get("/citizen/my-complaints")
async def list_citizen_complaints(limit: int = Query(20, ge=1, le=100)):
    """
    Returns list of submitted citizen complaints for tracking.
    """
    _ensure_service_initialized()
    all_complaints = list(incident_service._complaints_store.values())
    all_complaints.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

    results = []
    for c in all_complaints[:limit]:
        prio = str(c.get("priority", "medium")).lower()
        dept = c.get("department_name") or "Municipal Grievance Cell"
        sla = SLA_MAP.get(prio, 72)
        results.append({
            "id": str(c["id"]),
            "complaint_code": c["complaint_code"],
            "text": c.get("text", "")[:120] + ("..." if len(c.get("text", "")) > 120 else ""),
            "category": c.get("category") or "general",
            "priority": prio,
            "status": c.get("status", "open"),
            "department_name": dept,
            "expected_sla_hours": sla,
            "has_media": len(c.get("media") or []) > 0 or c.get("voice_transcription") is not None,
            "media_count": len(c.get("media") or []),
            "created_at": c.get("created_at"),
            "location_text": c.get("location_text"),
        })

    return {"complaints": results, "total": len(results)}
