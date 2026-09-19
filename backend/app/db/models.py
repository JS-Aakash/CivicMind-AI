"""
CivicMind AI — Database ORM Models (Module 3 Enhanced)
Schema designed for PostGIS (geospatial) and pgvector (semantic similarity)
with full support for Module 3 Smart Routing, Priority Engine, and SLAs.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Float, Boolean, Integer, DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complaints: Mapped[list["Complaint"]] = relationship(back_populates="department")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    priority: Mapped[str] = mapped_column(
        SAEnum("critical", "high", "medium", "low", name="priority_enum"),
        default="medium"
    )
    status: Mapped[str] = mapped_column(
        SAEnum("detected", "investigating", "acknowledged", "in_progress", "resolved", "closed", "false_positive", name="incident_status_enum_v4"),
        default="detected"
    )
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    affected_area: Mapped[Optional[str]] = mapped_column(String(500))
    # Centroid of affected complaints
    center_latitude: Mapped[Optional[float]] = mapped_column(Float)
    center_longitude: Mapped[Optional[float]] = mapped_column(Float)
    # GeoJSON geometry representing convex hull or bounding polygon
    geometry: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Temporal tracking
    first_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Routing & Governance
    primary_department: Mapped[Optional[str]] = mapped_column(String(100))
    secondary_departments: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # Incident Intelligence Signals
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=0.85)
    confidence_signals: Mapped[Optional[dict]] = mapped_column(JSON)
    trend: Mapped[str] = mapped_column(String(50), default="STABLE")  # RISING, STABLE, DECLINING
    complaints_per_hour: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    is_emerging: Mapped[bool] = mapped_column(Boolean, default=False)
    languages: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    priority_distribution: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    department_distribution: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Audit & Versioning
    detection_method: Mapped[str] = mapped_column(String(100), default="SEMANTIC_GEO_TEMPORAL_CLUSTER")
    algorithm_version: Mapped[str] = mapped_column(String(50), default="incident-v1.0")
    merged_from_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    split_from_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    complaints: Mapped[list["Complaint"]] = relationship(back_populates="incident")
    memberships: Mapped[list["IncidentComplaint"]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Original citizen input
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Language analysis (from IndicLID)
    language: Mapped[Optional[str]] = mapped_column(String(10))           # ISO 639-1: en, ta, hi
    script: Mapped[Optional[str]] = mapped_column(String(20))             # devanagari, tamil, roman
    is_code_mixed: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_languages: Mapped[Optional[list]] = mapped_column(JSON)      # ["ta", "en"]

    # AI Classification
    is_grievance: Mapped[Optional[bool]] = mapped_column(Boolean)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    severity: Mapped[Optional[str]] = mapped_column(String(50))
    priority: Mapped[str] = mapped_column(
        SAEnum("critical", "high", "medium", "low", name="priority_enum2"),
        default="medium"
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Module 3 Priority & Context Extensions
    final_priority: Mapped[Optional[str]] = mapped_column(String(50), default="medium")
    priority_score: Mapped[Optional[float]] = mapped_column(Float)
    priority_factors: Mapped[Optional[list]] = mapped_column(JSON)

    # Extracted entities (JSON blob)
    entities: Mapped[Optional[dict]] = mapped_column(JSON)
    duration_mentioned: Mapped[Optional[str]] = mapped_column(String(100))

    # Geospatial (PostGIS-ready lat/lng)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    location_text: Mapped[Optional[str]] = mapped_column(String(500))
    ward: Mapped[Optional[str]] = mapped_column(String(100))

    # AI explanation
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text)

    # Module 3 Smart Routing & Multi-Issue Dispatches
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    secondary_departments: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    routing_confidence: Mapped[Optional[float]] = mapped_column(Float)
    routing_decision: Mapped[Optional[str]] = mapped_column(String(50), default="AUTO_ROUTE")
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)

    # Module 3 SLA & Escalation
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sla_status: Mapped[Optional[str]] = mapped_column(String(50), default="within_sla")
    escalation_status: Mapped[Optional[str]] = mapped_column(String(50), default="normal")

    # Module 3 Officer Override Audit Trail
    officer_overrides: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    routing_version: Mapped[str] = mapped_column(String(50), default="routing-v1.0")

    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True
    )

    # Module 4 Geo + Embedding Fields
    embedding: Mapped[Optional[list]] = mapped_column(JSON)  # 768-dim normalized vector representation
    embedding_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, ready, failed

    # Status
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "open", "in_progress", "resolved", "closed", "duplicate", name="complaint_status_enum"),
        default="pending"
    )

    # Metadata
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)  # flag demo seed records
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(back_populates="complaints")
    incident: Mapped[Optional["Incident"]] = relationship(back_populates="complaints")
    ai_analysis: Mapped[Optional["AIAnalysis"]] = relationship(back_populates="complaint", uselist=False)
    similarities_as_source: Mapped[list["ComplaintSimilarity"]] = relationship(
        foreign_keys="ComplaintSimilarity.source_complaint_id", back_populates="source_complaint"
    )
    relationships_as_source: Mapped[list["ComplaintRelationship"]] = relationship(
        foreign_keys="ComplaintRelationship.source_complaint_id", back_populates="source_complaint"
    )
    relationships_as_target: Mapped[list["ComplaintRelationship"]] = relationship(
        foreign_keys="ComplaintRelationship.target_complaint_id", back_populates="target_complaint"
    )
    incident_memberships: Mapped[list["IncidentComplaint"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    media: Mapped[list["ComplaintMedia"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    voice_transcriptions: Mapped[list["VoiceTranscription"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    vision_analyses: Mapped[list["VisionAnalysis"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="complaint")


class AIAnalysis(Base):
    """Stores the complete AI analysis result for each complaint."""
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id"), unique=True
    )

    # Language analysis
    primary_language: Mapped[Optional[str]] = mapped_column(String(10))
    languages: Mapped[Optional[list]] = mapped_column(JSON)
    script: Mapped[Optional[str]] = mapped_column(String(20))
    is_code_mixed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Classification results
    category: Mapped[Optional[str]] = mapped_column(String(100))
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))
    priority: Mapped[Optional[str]] = mapped_column(String(50))
    severity: Mapped[Optional[str]] = mapped_column(String(50))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    is_grievance: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Module 3 Priority Details
    final_priority: Mapped[Optional[str]] = mapped_column(String(50))
    priority_score: Mapped[Optional[float]] = mapped_column(Float)
    priority_factors: Mapped[Optional[list]] = mapped_column(JSON)

    # Routing
    department_code: Mapped[Optional[str]] = mapped_column(String(50))
    routing_reason: Mapped[Optional[str]] = mapped_column(Text)
    secondary_departments: Mapped[Optional[list]] = mapped_column(JSON)
    routing_confidence: Mapped[Optional[float]] = mapped_column(Float)
    routing_decision: Mapped[Optional[str]] = mapped_column(String(50))
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)

    # SLA
    sla_target_hours: Mapped[Optional[int]] = mapped_column(Integer)
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Explainability & Full Decision Payload
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    entities: Mapped[Optional[dict]] = mapped_column(JSON)
    decision_details: Mapped[Optional[dict]] = mapped_column(JSON)

    # Model info
    model_version: Mapped[str] = mapped_column(String(100), default="muril-multitask-v1.1")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complaint: Mapped["Complaint"] = relationship(back_populates="ai_analysis")


class ComplaintRelationship(Base):
    """
    Module 4: Non-destructive duplicate and related complaint relationships.
    Tracks pairwise multi-factor scoring (semantic, geo, temporal, category).
    """
    __tablename__ = "complaint_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id"), index=True
    )
    target_complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id"), index=True
    )
    
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "DUPLICATE", "RELATED"
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)      # Composite relationship score
    semantic_similarity: Mapped[float] = mapped_column(Float, nullable=False)   # Cosine similarity (0-1)
    geographic_score: Mapped[Optional[float]] = mapped_column(Float)            # Geographic proximity score (0-1)
    temporal_score: Mapped[Optional[float]] = mapped_column(Float)              # Temporal proximity score (0-1)
    category_score: Mapped[float] = mapped_column(Float, default=1.0)           # Category compatibility score (0-1)
    
    geo_distance_meters: Mapped[Optional[float]] = mapped_column(Float)
    time_diff_hours: Mapped[Optional[float]] = mapped_column(Float)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    algorithm_version: Mapped[str] = mapped_column(String(50), default="duplicate-v1.0")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_complaint: Mapped["Complaint"] = relationship(
        foreign_keys=[source_complaint_id], back_populates="relationships_as_source"
    )
    target_complaint: Mapped["Complaint"] = relationship(
        foreign_keys=[target_complaint_id], back_populates="relationships_as_target"
    )


class IncidentComplaint(Base):
    """
    Module 4: Many-to-one/many membership linking complaints to incidents with membership scores.
    """
    __tablename__ = "incident_complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), index=True
    )
    membership_score: Mapped[float] = mapped_column(Float, default=1.0)
    membership_type: Mapped[str] = mapped_column(String(50), default="RELATED")  # "CORE", "RELATED", "DUPLICATE"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    incident: Mapped["Incident"] = relationship(back_populates="memberships")
    complaint: Mapped["Complaint"] = relationship(back_populates="incident_memberships")


class ComplaintSimilarity(Base):
    """Stores pairwise similarity scores between complaints (legacy compatibility)."""
    __tablename__ = "complaint_similarities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id")
    )
    target_complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id")
    )
    similarity_score: Mapped[float] = mapped_column(Float)
    geo_distance_km: Mapped[Optional[float]] = mapped_column(Float)
    temporal_gap_hours: Mapped[Optional[float]] = mapped_column(Float)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_complaint: Mapped["Complaint"] = relationship(
        foreign_keys=[source_complaint_id], back_populates="similarities_as_source"
    )


class Feedback(Base):
    """Citizen or officer feedback on AI analysis quality."""
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"))
    feedback_type: Mapped[str] = mapped_column(String(50))  # "priority", "category", "routing"
    is_correct: Mapped[bool] = mapped_column(Boolean)
    corrected_value: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complaint: Mapped["Complaint"] = relationship(back_populates="feedback")


# ─── Module 5: Multimodal Intelligence Models ─────────────────────────────────

class ComplaintMedia(Base):
    """
    Stores metadata for citizen-uploaded media (photos and voice notes).
    """
    __tablename__ = "complaint_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True
    )
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "image" or "audio"
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1000))
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    processing_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # "pending", "processing", "completed", "failed"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complaint: Mapped[Optional["Complaint"]] = relationship(back_populates="media")
    voice_transcription: Mapped[Optional["VoiceTranscription"]] = relationship(
        back_populates="media", uselist=False, cascade="all, delete-orphan"
    )
    vision_analysis: Mapped[Optional["VisionAnalysis"]] = relationship(
        back_populates="media", uselist=False, cascade="all, delete-orphan"
    )
    jobs: Mapped[list["MediaProcessingJob"]] = relationship(
        back_populates="media", cascade="all, delete-orphan"
    )


class VoiceTranscription(Base):
    """
    Module 5: Local Whisper speech-to-text transcriptions with raw vs edited tracking.
    """
    __tablename__ = "voice_transcriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaint_media.id", ondelete="CASCADE"), unique=True, index=True
    )
    raw_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    edited_transcript: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(50), default="en")  # detected language
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(100), default="whisper-tiny")
    model_version: Mapped[str] = mapped_column(String(50), default="whisper-v1.0")
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complaint: Mapped[Optional["Complaint"]] = relationship(back_populates="voice_transcriptions")
    media: Mapped["ComplaintMedia"] = relationship(back_populates="voice_transcription")


class VisionAnalysis(Base):
    """
    Module 5: Local Qwen3-VL 4B structured visual evidence analysis.
    """
    __tablename__ = "vision_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaint_media.id", ondelete="CASCADE"), unique=True, index=True
    )
    observations: Mapped[list] = mapped_column(JSON, default=list)
    objects: Mapped[list] = mapped_column(JSON, default=list)
    possible_hazards: Mapped[list] = mapped_column(JSON, default=list)
    evidence_category: Mapped[str] = mapped_column(String(100), default="OTHER")
    severity_signal: Mapped[str] = mapped_column(String(50), default="low")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(100), default="qwen3-vl:4b")
    model_version: Mapped[str] = mapped_column(String(50), default="qwen3-vl-v1.0")
    prompt_version: Mapped[str] = mapped_column(String(50), default="vision_prompt_v1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    complaint: Mapped[Optional["Complaint"]] = relationship(back_populates="vision_analyses")
    media: Mapped["ComplaintMedia"] = relationship(back_populates="vision_analysis")


class MediaProcessingJob(Base):
    """
    Module 5: Asynchronous processing queue and retry ledger for multimodal media tasks.
    """
    __tablename__ = "media_processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaint_media.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "voice_transcription", "vision_analysis"
    status: Mapped[str] = mapped_column(
        String(50), default="queued"
    )  # "queued", "processing", "completed", "failed", "retrying"
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    error_code: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    media: Mapped["ComplaintMedia"] = relationship(back_populates="jobs")


class OfficerFeedback(Base):
    """
    Module 6: Officer corrections & Human-in-the-Loop continuous improvement feedback loop.
    """
    __tablename__ = "officer_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True, index=True
    )
    complaint_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    officer_id: Mapped[str] = mapped_column(String(100), default="officer-admin")
    officer_name: Mapped[str] = mapped_column(String(255), default="Command Center Officer")
    action: Mapped[str] = mapped_column(String(50), default="modify")  # "accept", "modify", "reject"
    field_changed: Mapped[Optional[str]] = mapped_column(String(100))  # "category", "priority", "department", "sla"
    original_ai_prediction: Mapped[Optional[dict]] = mapped_column(JSON)
    corrected_value: Mapped[Optional[dict]] = mapped_column(JSON)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(50), default="muril-multitask-v1.1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLogEvent(Base):
    """
    Module 6: Governance audit trail for AI actions, officer overrides, and SLA escalations.
    """
    __tablename__ = "audit_log_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), default="complaint")
    target_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(100), default="system")
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

