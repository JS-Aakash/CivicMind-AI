"""
CivicMind AI — Pydantic Schemas (Module 3 Comprehensive)
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any, List, Dict
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    demo_mode: bool
    services: dict[str, str]


# ─── Language Detection ──────────────────────────────────────────────────────

class LanguageDetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class LanguageDetectResponse(BaseModel):
    primary_language: str
    language_name: str
    languages: list[str]
    script: str
    is_code_mixed: bool
    confidence: float
    model: str = "IndicLID"


# ─── Models ──────────────────────────────────────────────────────────────────

class ModelInfo(BaseModel):
    name: str
    display_name: str
    type: str
    status: str
    local_path: Optional[str] = None
    size_mb: Optional[float] = None
    description: str
    module: str


class ModelStatusResponse(BaseModel):
    models: list[ModelInfo]
    all_ready: bool


# ─── Module 3 Routing & Priority Schemas ─────────────────────────────────────

class DepartmentTargetSchema(BaseModel):
    id: str
    code: str
    name: str
    contact_email: str
    confidence: float
    is_primary: bool = True
    role: str = "primary_lead"


class SLASchema(BaseModel):
    target_sla_hours: int
    target_response_minutes: int
    response_window_hours: Optional[int] = None
    response_minutes: Optional[int] = None
    created_at: str
    due_at: str
    status: str  # "within_sla", "approaching_breach", "breached", "escalated"
    elapsed_minutes: int
    remaining_minutes: int
    percent_elapsed: float
    is_breached: bool
    is_approaching: bool

    def model_post_init(self, __context: Any) -> None:
        if self.response_window_hours is None:
            self.response_window_hours = self.target_sla_hours
        if self.response_minutes is None:
            self.response_minutes = self.target_response_minutes



class PriorityFactorSchema(BaseModel):
    factor: str
    label: str
    value: str
    impact: str  # "increases_urgency", "critical_escalation", "neutral", "reduces_urgency"
    weight_contribution: float
    description: str


class ExplanationSchema(BaseModel):
    summary: str
    what_category_reason: str
    why_urgent_factors: List[PriorityFactorSchema] = []
    factors: List[PriorityFactorSchema] = []
    who_department_reason: str = ""
    when_sla_reason: str = ""
    how_confident_reason: str = ""
    human_review_reason: str = ""
    reasoning_mode: str = "hybrid_neural_context"

    def model_post_init(self, __context: Any) -> None:
        if not self.factors and self.why_urgent_factors:
            self.factors = self.why_urgent_factors
        elif not self.why_urgent_factors and self.factors:
            self.why_urgent_factors = self.factors



class ContextSignalsSchema(BaseModel):
    duration_hours: Optional[float] = None
    is_prolonged: bool = False
    affected_population: Optional[str] = None
    estimated_population: Optional[int] = None
    safety_risk: bool = False
    vulnerable_population: bool = False
    vulnerable_groups: List[str] = []
    critical_infrastructure: bool = False
    infrastructure_types: List[str] = []
    is_night_time: bool = False
    location_category: str = "general"


class Module3DecisionSchema(BaseModel):
    final_priority: str
    composite_score: float
    neural_priority: str
    neural_probabilities: Dict[str, float] = {}
    primary_department: DepartmentTargetSchema
    secondary_departments: List[DepartmentTargetSchema] = []
    routing_confidence: float
    routing_decision: str  # "AUTO_ROUTE", "OFFICER_REVIEW", "MANUAL_REVIEW"
    requires_human_review: bool
    sla: SLASchema
    explanation: ExplanationSchema
    context: Optional[ContextSignalsSchema] = None
    routing: Optional[Dict[str, Any]] = None
    priority: Optional[Dict[str, Any]] = None
    review: Optional[Dict[str, Any]] = None
    is_compound_multi_issue: bool = False
    is_immediate_hazard: bool = False
    routing_version: str = "routing-v1.0"
    priority_policy_version: str = "priority-v1.0"
    sla_policy_version: str = "sla-policy-v1.0"



# ─── Grievance Analysis ──────────────────────────────────────────────────────

class GrievanceAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AIAnalysisResult(BaseModel):
    # Language
    primary_language: str
    language_name: str
    languages: list[str]
    script: str
    is_code_mixed: bool

    # Classification
    is_grievance: bool
    category: str
    subcategory: Optional[str] = None
    severity: str
    priority: str
    confidence: float

    # Entities
    entities: dict[str, Any] = {}
    duration_mentioned: Optional[str] = None

    # Routing
    department_code: str
    department_name: str
    routing_reason: str

    # Explainability & Evidence
    explanation: str
    category_probabilities: Optional[dict[str, float]] = None
    task_confidences: Optional[dict[str, float]] = None

    # Module 3 Advanced Decision
    routing_decision: Optional[str] = "AUTO_ROUTE"
    requires_human_review: Optional[bool] = False
    primary_department: Optional[DepartmentTargetSchema] = None
    secondary_departments: Optional[List[DepartmentTargetSchema]] = []
    sla: Optional[SLASchema] = None
    decision_details: Optional[Module3DecisionSchema] = None

    # Metadata
    is_mock: bool = False
    model_version: str = "muril-multitask-v1.1"


class GrievanceAnalyzeResponse(BaseModel):
    analysis: AIAnalysisResult
    demo_mode: bool = True


# ─── Embedding ───────────────────────────────────────────────────────────────

class EmbeddingRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class EmbeddingResponse(BaseModel):
    embedding: list[float]
    model: str
    dimensions: int


# ─── Complaint ───────────────────────────────────────────────────────────────

class ComplaintBase(BaseModel):
    text: str
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    pass


class ComplaintResponse(BaseModel):
    id: str | UUID
    complaint_code: str
    text: str
    language: Optional[str] = None
    script: Optional[str] = None
    is_code_mixed: bool = False
    detected_languages: Optional[list[str]] = None
    is_grievance: Optional[bool] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    severity: Optional[str] = None
    priority: str = "medium"
    confidence: Optional[float] = None
    entities: Optional[dict] = None
    duration_mentioned: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_text: Optional[str] = None
    ward: Optional[str] = None
    ai_explanation: Optional[str] = None
    department_id: Optional[UUID | str] = None
    department_name: Optional[str] = None
    secondary_departments: Optional[List[Dict[str, Any]]] = []
    routing_decision: Optional[str] = "AUTO_ROUTE"
    requires_human_review: Optional[bool] = False
    sla_due_at: Optional[datetime] = None
    sla_status: Optional[str] = "within_sla"
    incident_id: Optional[UUID | str] = None
    status: str = "pending"
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime
    media: Optional[List[Dict[str, Any]]] = []
    voice_transcription: Optional[Dict[str, Any]] = None
    vision_evidence: Optional[Dict[str, Any]] = None
    multimodal_consistency: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ComplaintListResponse(BaseModel):
    complaints: list[ComplaintResponse]
    total: int
    page: int
    page_size: int


# ─── Incidents ───────────────────────────────────────────────────────────────

# ─── Incidents ───────────────────────────────────────────────────────────────

class IncidentConfidenceSignals(BaseModel):
    semantic_cohesion: float = 0.0
    geographic_cohesion: float = 0.0
    temporal_cohesion: float = 0.0
    category_consistency: float = 1.0


class IncidentTimelineEvent(BaseModel):
    event: str
    timestamp: datetime
    description: Optional[str] = None
    color: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str | UUID
    incident_code: str
    title: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    priority: str
    status: str
    complaint_count: int
    affected_area: Optional[str] = None
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None
    geometry: Optional[dict] = None
    first_reported_at: Optional[datetime] = None
    last_reported_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    primary_department: Optional[str] = None
    secondary_departments: Optional[list[str]] = []
    confidence: float = 0.85
    confidence_signals: Optional[IncidentConfidenceSignals | dict] = None
    trend: str = "STABLE"  # RISING, STABLE, DECLINING
    complaints_per_hour: float = 0.0
    is_emerging: bool = False
    languages: list[str] = []
    priority_distribution: Optional[dict[str, int]] = {}
    department_distribution: Optional[dict[str, int]] = {}
    detection_method: str = "SEMANTIC_GEO_TEMPORAL_CLUSTER"
    algorithm_version: str = "incident-v1.0"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentDetailResponse(IncidentResponse):
    member_complaints: list[ComplaintResponse] = []
    timeline: list[IncidentTimelineEvent] = []
    explanation: Optional[str] = None


class IncidentListResponse(BaseModel):
    incidents: list[IncidentResponse]
    total: int
    page: int = 1
    page_size: int = 20
    active_count: int = 0
    emerging_count: int = 0
    critical_count: int = 0
    rising_count: int = 0


# ─── Module 4 Duplicate & Relationship Schemas ───────────────────────────────

class DuplicateDecisionResponse(BaseModel):
    relationship: str  # "DUPLICATE", "RELATED", "NEW"
    similarity_score: float
    semantic_similarity: float
    geographic_score: Optional[float] = None
    temporal_score: Optional[float] = None
    category_score: float = 1.0
    geo_distance_meters: Optional[float] = None
    time_diff_hours: Optional[float] = None
    matched_complaint_id: Optional[str] = None
    matched_complaint_code: Optional[str] = None
    matched_text_preview: Optional[str] = None
    explanation: str
    algorithm_version: str = "duplicate-v1.0"


class ComplaintRelationshipItem(BaseModel):
    id: str | UUID
    target_complaint_id: str | UUID
    target_complaint_code: str
    target_text_preview: str
    target_language: Optional[str] = None
    target_priority: str
    target_created_at: datetime
    relationship_type: str  # "DUPLICATE", "RELATED"
    similarity_score: float
    semantic_similarity: float
    geographic_score: Optional[float] = None
    temporal_score: Optional[float] = None
    category_score: float
    geo_distance_meters: Optional[float] = None
    time_diff_hours: Optional[float] = None
    explanation: Optional[str] = None


class ComplaintDuplicatesResponse(BaseModel):
    complaint_id: str
    complaint_code: str
    duplicates: list[ComplaintRelationshipItem]
    related: list[ComplaintRelationshipItem]
    total_relationships: int


# ─── Module 4 Incident Admin Actions ─────────────────────────────────────────

class RecomputeIncidentsRequest(BaseModel):
    hours: int = Field(72, ge=1, le=720)
    category: Optional[str] = None
    dry_run: bool = False


class RecomputeIncidentsResponse(BaseModel):
    status: str
    dry_run: bool
    time_window_hours: int
    analyzed_complaints_count: int
    formed_incidents_count: int
    merged_incidents_count: int
    incidents: list[IncidentResponse] = []
    runtime_ms: float
    timestamp: str


class MergeIncidentsRequest(BaseModel):
    target_incident_id: str
    reason: Optional[str] = "Manual officer merge"


class SplitIncidentRequest(BaseModel):
    complaint_ids_for_new_incident: list[str] = Field(..., min_length=1)
    reason: Optional[str] = "Manual officer split"


class IncidentStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(detected|investigating|acknowledged|in_progress|resolved|closed|false_positive)$")
    notes: Optional[str] = None
    officer_name: Optional[str] = "Command Officer"


# ─── Map ─────────────────────────────────────────────────────────────────────

class MapComplaintMarker(BaseModel):
    id: str
    complaint_code: str
    category: Optional[str] = None
    priority: str
    status: str
    language: Optional[str] = None
    latitude: float
    longitude: float
    location_text: Optional[str] = None
    ward: Optional[str] = None
    text_preview: str = ""
    created_at: Optional[datetime] = None
    incident_id: Optional[str] = None
    is_code_mixed: bool = False


class MapIncidentMarker(BaseModel):
    id: str
    incident_code: str
    title: str
    category: str
    priority: str
    status: str
    complaint_count: int
    center_latitude: Optional[float] = None
    center_longitude: Optional[float] = None
    affected_area: Optional[str] = None
    geometry: Optional[dict] = None
    trend: str = "STABLE"
    is_emerging: bool = False
    first_reported_at: Optional[datetime] = None
    last_reported_at: Optional[datetime] = None


class MapDataResponse(BaseModel):
    markers: list[MapComplaintMarker] = []
    complaints: list[MapComplaintMarker] = []
    incidents: list[MapIncidentMarker] = []
    total: int = 0
    total_geolocated: int = 0
    center_lat: float = 13.0827
    center_lng: float = 80.2707


# ─── Officer Override & Human-in-the-Loop ────────────────────────────────────

class OfficerOverrideRequest(BaseModel):
    field: str  # "category", "subcategory", "priority", "department"
    original_value: str
    new_value: str
    reason: str = Field(..., min_length=3, max_length=500)
    actor: str = "triage_officer"


class OfficerOverrideResponse(BaseModel):
    status: str
    complaint_id: str
    override: Dict[str, Any]
    updated_complaint: Optional[ComplaintResponse] = None


# ─── Module 3 Routing KPIs ───────────────────────────────────────────────────

class RoutingKPIsResponse(BaseModel):
    total_analyzed: int
    auto_routed_count: int
    auto_routed_percent: float
    officer_review_count: int
    officer_review_percent: float
    manual_review_count: int
    manual_review_percent: float
    sla_within_count: int
    sla_at_risk_count: int
    sla_breached_count: int
    critical_cases_count: int
    timestamp: str


# ─── Module 5: Multimodal Intelligence & Media Schemas ───────────────────────

class MediaUploadResponse(BaseModel):
    media_id: str
    media_type: str  # "image" or "audio"
    storage_path: str
    thumbnail_url: Optional[str] = None
    file_size: int
    mime_type: str
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    processing_status: str = "completed"
    created_at: datetime


class VoiceTranscribeRequest(BaseModel):
    audio_id: str
    language_hint: Optional[str] = None


class VoiceTranscribeResponse(BaseModel):
    transcription_id: str
    media_id: str
    raw_transcript: str
    edited_transcript: Optional[str] = None
    language: str
    language_name: str
    confidence: float
    duration_seconds: Optional[float] = None
    model_name: str = "whisper"
    model_version: str = "whisper-v1.0"
    created_at: datetime


class VisionAnalysisResult(BaseModel):
    analysis_id: str
    media_id: str
    observations: List[str] = []
    objects: List[str] = []
    possible_hazards: List[str] = []
    evidence_category: str  # "ROAD_DAMAGE", "WATERLOGGING", "GARBAGE_ACCUMULATION", "ELECTRICAL_HAZARD", "STREETLIGHT_DAMAGE", "DRAINAGE_BLOCKAGE", "OTHER"
    severity_signal: str  # "critical", "high", "medium", "low"
    confidence: float
    model_name: str = "qwen3-vl:4b"
    model_version: str = "qwen3-vl-v1.0"
    prompt_version: str = "vision_prompt_v1"
    created_at: datetime


class MultimodalEvidenceSummary(BaseModel):
    has_voice: bool = False
    has_image: bool = False
    image_count: int = 0
    voice_transcript_preview: Optional[str] = None
    voice_confidence: Optional[float] = None
    visual_evidence_categories: List[str] = []
    visual_hazards: List[str] = []
    visual_confidence: Optional[float] = None
    conflict_detected: bool = False
    conflict_reason: Optional[str] = None
    evidence_strength: str = "HIGH"  # "HIGH", "MEDIUM", "LOW"


class MultimodalComplaintCreate(BaseModel):
    text: Optional[str] = None
    media_ids: List[str] = []
    audio_id: Optional[str] = None
    raw_transcript: Optional[str] = None
    edited_transcript: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ward: Optional[str] = None


class CitizenStatusTimelineEvent(BaseModel):
    title: str
    timestamp: datetime
    description: str
    status: str  # "completed", "current", "upcoming"
    actor: str


class CitizenTrackingResponse(BaseModel):
    complaint_code: str
    submitted_at: datetime
    category: str
    category_display: str
    priority: str
    status: str
    status_display: str
    department_name: str
    expected_sla_hours: int
    sla_due_at: Optional[datetime] = None
    timeline: List[CitizenStatusTimelineEvent] = []
    media: List[Dict[str, Any]] = []
    ai_summary: str
    incident_title: Optional[str] = None
    citizen_response_message: Dict[str, str]  # {"en": "...", "ta": "...", "hi": "..."}


class MultimodalModelStatus(BaseModel):
    whisper: Dict[str, Any]
    vision: Dict[str, Any]
    ollama_endpoint: str
    local: bool = True

