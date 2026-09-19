// CivicMind AI — All TypeScript Types (Module 3 Enhanced)

export type Priority = "critical" | "high" | "medium" | "low";
export type Status =
  | "submitted"
  | "ai_analysis"
  | "triaged"
  | "routed"
  | "assigned"
  | "in_progress"
  | "field_verification"
  | "resolved"
  | "closed"
  | "reopened"
  | "pending"
  | "open"
  | "duplicate"
  | (string & {});
export type Script = "native" | "roman" | "mixed";
export type IncidentStatus = "open" | "in_progress" | "resolved" | "closed";
export type RoutingDecision = "AUTO_ROUTE" | "OFFICER_REVIEW" | "MANUAL_REVIEW";
export type SLAStatus = "within_sla" | "approaching_breach" | "breached" | "escalated";

export interface DepartmentTarget {
  id: string;
  code?: string;
  name: string;
  contact_email?: string;
  confidence: number;
  is_primary?: boolean;
  role?: string;
}

export interface SLAInfo {
  response_minutes?: number;
  response_window_hours?: number;
  target_sla_hours?: number;
  target_response_minutes?: number;
  created_at?: string;
  due_at?: string;
  status: SLAStatus | string;
  elapsed_minutes?: number;
  remaining_minutes?: number;
  percent_elapsed?: number;
  is_breached?: boolean;
  is_approaching?: boolean;
}

export interface PriorityFactor {
  factor: string;
  label?: string;
  value: string;
  impact: string;
  weight_contribution?: number;
  description?: string;
}

export interface ExplanationDetails {
  summary: string;
  factors?: PriorityFactor[];
  what_category_reason?: string;
  why_urgent_factors?: PriorityFactor[];
  who_department_reason?: string;
  when_sla_reason?: string;
  how_confident_reason?: string;
  human_review_reason?: string;
  reasoning_mode?: string;
}

export interface Module3DecisionDetails {
  final_priority?: Priority;
  composite_score?: number;
  neural_priority?: string;
  neural_probabilities?: Record<string, number>;
  routing?: {
    primary_department: DepartmentTarget;
    secondary_departments: DepartmentTarget[];
  };
  primary_department?: DepartmentTarget;
  secondary_departments?: DepartmentTarget[];
  routing_confidence?: number;
  routing_decision?: RoutingDecision;
  requires_human_review?: boolean;
  review?: {
    decision: RoutingDecision;
    requires_human_review: boolean;
    reason?: string;
  };
  priority?: {
    neural_prediction: string;
    neural_probability: number;
    final_priority: Priority;
    priority_score: number;
    reasoning_mode: string;
  };
  context?: {
    duration_hours?: number | null;
    affected_population?: string | null;
    safety_risk?: boolean;
    vulnerable_population?: boolean;
    critical_infrastructure?: boolean;
    emergency_indicator?: boolean;
  };
  sla?: SLAInfo;
  explanation?: ExplanationDetails;
  is_compound_multi_issue?: boolean;
  is_immediate_hazard?: boolean;
  routing_version?: string;
}

export interface Complaint {
  id: string;
  complaint_code: string;
  text: string;
  language?: string;
  script?: string;
  is_code_mixed: boolean;
  detected_languages?: string[];
  is_grievance?: boolean;
  category?: string;
  subcategory?: string;
  severity?: string;
  priority: Priority;
  confidence?: number;
  entities?: Record<string, unknown>;
  duration_mentioned?: string;
  latitude?: number;
  longitude?: number;
  location_text?: string;
  ward?: string;
  ai_explanation?: string;
  department_id?: string;
  department_name?: string;
  secondary_departments?: DepartmentTarget[];
  routing_decision?: RoutingDecision;
  requires_human_review?: boolean;
  sla_due_at?: string;
  sla_status?: SLAStatus;
  incident_id?: string;
  status: Status;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  media?: MediaItem[];
  voice_transcription?: VoiceTranscriptionItem;
  vision_evidence?: VisionAnalysisItem;
  multimodal_consistency?: MultimodalEvidenceSummary;
  assigned_officer?: string;
  resolution_info?: Record<string, any>;
  resolved_at?: string;
  reopen_eligible?: boolean;
  reopen_reason?: string;
}

export interface ComplaintListResponse {
  complaints: Complaint[];
  total: number;
  page: number;
  page_size: number;
}

export interface IncidentConfidenceSignals {
  semantic_cohesion: number;
  geographic_cohesion: number;
  temporal_cohesion: number;
  category_consistency: number;
}

export interface IncidentTimelineEvent {
  event: string;
  timestamp: string;
  description?: string;
  color?: string;
}

export interface Incident {
  id: string;
  incident_code: string;
  title: string;
  description?: string;
  category: string;
  subcategory?: string;
  priority: Priority;
  status: IncidentStatus | string;
  complaint_count: number;
  affected_area?: string;
  center_latitude?: number;
  center_longitude?: number;
  geometry?: {
    type: string;
    coordinates: number[][][] | number[][][][];
  };
  first_reported_at?: string;
  last_reported_at?: string;
  started_at?: string;
  resolved_at?: string;
  primary_department?: string;
  secondary_departments?: string[];
  confidence: number;
  confidence_signals?: IncidentConfidenceSignals;
  trend: "RISING" | "STABLE" | "DECLINING" | string;
  complaints_per_hour?: number;
  is_emerging?: boolean;
  languages?: string[];
  priority_distribution?: Record<string, number>;
  department_distribution?: Record<string, number>;
  detection_method?: string;
  algorithm_version?: string;
  created_at: string;
  updated_at: string;
  member_complaints?: Complaint[];
  timeline?: IncidentTimelineEvent[];
  explanation?: string;
}

export interface IncidentListResponse {
  incidents: Incident[];
  total: number;
  page?: number;
  page_size?: number;
  active_count?: number;
  emerging_count?: number;
  critical_count?: number;
  rising_count?: number;
}

export interface ComplaintRelationshipItem {
  id: string;
  target_complaint_id: string;
  target_complaint_code: string;
  target_text_preview: string;
  target_language?: string;
  target_priority: Priority;
  target_created_at: string;
  relationship_type: "DUPLICATE" | "RELATED";
  similarity_score: number;
  semantic_similarity: number;
  geographic_score?: number | null;
  temporal_score?: number | null;
  category_score: number;
  geo_distance_meters?: number | null;
  time_diff_hours?: number | null;
  explanation?: string;
}

export interface ComplaintDuplicatesResponse {
  complaint_id: string;
  complaint_code: string;
  duplicates: ComplaintRelationshipItem[];
  related: ComplaintRelationshipItem[];
  total_relationships: number;
}

export interface MapMarker {
  id: string;
  complaint_code: string;
  category?: string;
  priority: Priority;
  status: Status;
  language?: string;
  latitude: number;
  longitude: number;
  location_text?: string;
  ward?: string;
  text_preview: string;
  created_at: string;
  incident_id?: string;
  is_code_mixed?: boolean;
}

export interface MapIncidentMarker {
  id: string;
  incident_code: string;
  title: string;
  category: string;
  priority: Priority;
  status: string;
  complaint_count: number;
  center_latitude: number;
  center_longitude: number;
  affected_area?: string;
  geometry?: {
    type: string;
    coordinates: number[][][] | number[][][][];
  };
  trend?: string;
  is_emerging?: boolean;
  first_reported_at?: string;
  last_reported_at?: string;
}

export interface MapDataResponse {
  markers?: MapMarker[];
  complaints: MapMarker[];
  incidents: MapIncidentMarker[];
  total: number;
  total_geolocated?: number;
  center_lat: number;
  center_lng: number;
}

export interface LanguageDetectResponse {
  primary_language: string;
  language_name: string;
  languages: string[];
  script: string;
  is_code_mixed: boolean;
  confidence: number;
  model: string;
}

export interface AIAnalysisResult {
  primary_language: string;
  language_name: string;
  languages: string[];
  script: string;
  is_code_mixed: boolean;
  is_grievance: boolean;
  category: string;
  subcategory?: string;
  severity: string;
  priority: Priority;
  confidence: number;
  entities: Record<string, unknown>;
  duration_mentioned?: string;
  department_code: string;
  department_name: string;
  routing_reason: string;
  explanation: string;
  category_probabilities?: Record<string, number>;
  task_confidences?: Record<string, number>;
  routing_decision?: RoutingDecision;
  requires_human_review?: boolean;
  primary_department?: DepartmentTarget;
  secondary_departments?: DepartmentTarget[];
  sla?: SLAInfo;
  decision_details?: Module3DecisionDetails;
  is_mock: boolean;
  model_version: string;
}

export interface GrievanceAnalyzeResponse {
  analysis: AIAnalysisResult;
  demo_mode: boolean;
}

export interface TrainingStatusResponse {
  status: "idle" | "training" | "ready" | "completed" | "error";
  current_epoch: number;
  total_epochs: number;
  progress_percent: number;
  current_loss: number;
  validation_f1: number;
  device: string;
  model_version: string;
  stage: string;
  elapsed_seconds: number;
}

export interface ModelMetricsResponse {
  model_version: string;
  comparison?: any;
  overall: any;
  by_language: any;
  evaluation_available: boolean;
}

export interface DatasetStatsResponse {
  dataset_version: string;
  total_records: number;
  splits: { train: number; validation: number; test: number; challenge: number };
  overall_distribution: {
    total: number;
    languages: Record<string, number>;
    scripts: Record<string, number>;
    code_mixed: Record<string, number>;
    categories: Record<string, number>;
    priorities: Record<string, number>;
    severities: Record<string, number>;
    grievance_distribution: Record<string, number>;
  };
  quality_audit: {
    total_submitted: number;
    valid_records: number;
    exact_duplicates_removed: number;
    invalid_records_removed: number;
    validation_pass_rate: number;
  };
}

export interface ModelInfo {
  name: string;
  display_name: string;
  type: string;
  status: "ready" | "downloading" | "not_downloaded" | "error" | "loading" | "training";
  local_path?: string;
  size_mb?: number;
  description: string;
  module: string;
}

export interface ModelStatusResponse {
  models: ModelInfo[];
  all_ready: boolean;
}

export interface HealthResponse {
  status: string;
  version: string;
  demo_mode: boolean;
  services: Record<string, string>;
}

export interface RoutingKPIsResponse {
  total_analyzed: number;
  auto_routed_count: number;
  auto_routed_percent: number;
  officer_review_count: number;
  officer_review_percent: number;
  manual_review_count: number;
  manual_review_percent: number;
  sla_within_count: number;
  sla_at_risk_count: number;
  sla_breached_count: number;
  critical_cases_count: number;
  timestamp: string;
}

// ─── Module 5: Media & Multimodal Types ─────────────────────────────────────

export interface MediaItem {
  id: string;
  media_id: string;
  media_type: "image" | "audio";
  storage_path: string;
  thumbnail_url?: string;
  media_url: string;
  original_filename?: string;
  mime_type: string;
  file_size: number;
  width?: number;
  height?: number;
  duration_seconds?: number;
  processing_status: string;
  created_at: string;
}

export interface VoiceTranscriptionItem {
  transcription_id: string;
  media_id: string;
  raw_transcript: string;
  edited_transcript?: string;
  language: string;
  language_name: string;
  confidence: number;
  duration_seconds?: number;
  model_name?: string;
  model_version?: string;
  created_at: string;
}

export interface VisionAnalysisItem {
  analysis_id: string;
  media_id: string;
  observations: string[];
  objects: string[];
  possible_hazards: string[];
  evidence_category: string;
  severity_signal: "critical" | "high" | "medium" | "low" | string;
  confidence: number;
  model_name?: string;
  model_version?: string;
  prompt_version?: string;
  created_at: string;
}

export interface MultimodalEvidenceSummary {
  has_voice: boolean;
  has_image: boolean;
  image_count: number;
  voice_transcript_preview?: string;
  voice_confidence?: number;
  visual_evidence_categories: string[];
  visual_hazards: string[];
  visual_confidence?: number;
  conflict_detected: boolean;
  conflict_reason?: string;
  evidence_strength: "HIGH" | "MEDIUM" | "LOW" | string;
}

export interface CitizenStatusTimelineEvent {
  title: string;
  timestamp: string;
  description: string;
  status: "completed" | "current" | "upcoming";
  actor: string;
}

export interface CitizenTrackingResponse {
  complaint_code: string;
  submitted_at: string;
  category: string;
  category_display: string;
  priority: Priority;
  status: Status;
  status_display: string;
  department_name: string;
  expected_sla_hours: number;
  sla_due_at?: string;
  timeline: CitizenStatusTimelineEvent[];
  media: MediaItem[];
  ai_summary: string;
  incident_title?: string;
  citizen_response_message: {
    en: string;
    ta: string;
    hi: string;
  };
  assigned_officer?: string;
  resolution_info?: Record<string, any>;
  resolved_at?: string;
  reopen_eligible?: boolean;
  reopen_reason?: string;
  lifecycle_stage?: string;
  stages?: string[];
}

export interface MultimodalModelStatus {
  whisper: {
    available: boolean;
    model_size: string;
    device: string;
    model_version: string;
    local: boolean;
  };
  vision: {
    available: boolean;
    model: string;
    ollama_reachable: boolean;
    local: boolean;
  };
  ollama_endpoint: string;
  local: boolean;
}

// ─── Module 6: Command Center & Analytics Types ─────────────────────────────

export interface CriticalAlertItem {
  id: string;
  type: string;
  severity: string;
  title: string;
  locality: string;
  complaint_count: number;
  evidence_signals: string[];
  sla_remaining: string;
  routing_action: string;
  timestamp: string;
}

export interface EmergingIncidentItem {
  id: string;
  category: string;
  title: string;
  locality: string;
  growth_rate: string;
  complaints_count: number;
  radius_km: number;
  primary_department: string;
  confidence: number;
}

export interface CommandCenterKPIs {
  total_complaints: number;
  complaints_growth_pct: number;
  critical_count: number;
  immediate_attention_count: number;
  active_incidents: number;
  emerging_incidents: number;
  in_progress_count: number;
  resolved_count: number;
  resolution_rate_pct: number;
  human_review_queue_count: number;
  sla_at_risk_count: number;
  sla_breached_count: number;
}

export interface CommandCenterOverviewResponse {
  kpis: CommandCenterKPIs;
  critical_alerts: CriticalAlertItem[];
  emerging_incidents: EmergingIncidentItem[];
  system_status: {
    overall: string;
    muril_v11: string;
    whisper_stt: string;
    qwen3_vl: string;
    incident_engine: string;
    database: string;
    active_models: number;
  };
  recent_audit_events: AuditLogItem[];
  timestamp: string;
}

export interface AnalyticsSummaryResponse {
  timeframe: string;
  total_volume: number;
  resolved_volume: number;
  average_resolution_hours: number;
  first_response_time_minutes: number;
  sla_compliance_rate: number;
  citizen_satisfaction_score: number;
  top_category: string;
  top_department: string;
  ai_auto_routing_rate: number;
  officer_override_rate: number;
}

export interface AnalyticsTrendItem {
  date: string;
  complaints: number;
  resolved: number;
  critical: number;
  sla_breached: number;
}

export interface AnalyticsTrendsResponse {
  trends: AnalyticsTrendItem[];
}

export interface CategoryDistributionItem {
  category: string;
  label: string;
  count: number;
  percentage: number;
  color: string;
}

export interface AnalyticsCategoriesResponse {
  categories: CategoryDistributionItem[];
}

export interface DepartmentMetricItem {
  name: string;
  code: string;
  active_cases: number;
  resolved_cases: number;
  sla_compliance_pct: number;
  avg_response_hours: number;
}

export interface AnalyticsDepartmentsResponse {
  departments: DepartmentMetricItem[];
}

export interface LanguageDistributionItem {
  language: string;
  code: string;
  count: number;
  percentage: number;
  script: string;
}

export interface AnalyticsLanguagesResponse {
  languages: LanguageDistributionItem[];
}

export interface AnalyticsSLAResponse {
  within_sla_count: number;
  within_sla_pct: number;
  at_risk_count: number;
  at_risk_pct: number;
  breached_count: number;
  breached_pct: number;
  escalation_count: number;
}

export interface ReviewQueueItem {
  id: string;
  complaint_code: string;
  text: string;
  language?: string;
  language_name?: string;
  category: string;
  priority: Priority;
  department_name: string;
  confidence: number;
  review_reason: string;
  evidence_conflict?: boolean;
  sla_hours?: number;
  created_at: string;
}

export interface ReviewQueueResponse {
  count: number;
  items: ReviewQueueItem[];
}

export interface OfficerDecisionPayload {
  action: "accept" | "modify" | "reject";
  category?: string;
  subcategory?: string;
  priority?: string;
  department_name?: string;
  sla_hours?: number;
  officer_name?: string;
  reason?: string;
}

export interface FeedbackItem {
  id: string;
  complaint_code: string;
  officer_name: string;
  action: string;
  field_changed?: string;
  original_ai_prediction: Record<string, unknown>;
  corrected_value: Record<string, unknown>;
  reason: string;
  model_version: string;
  created_at: string;
}

export interface FeedbackRecordsResponse {
  total_feedbacks: number;
  accept_count: number;
  modify_count: number;
  reject_count: number;
  items: FeedbackItem[];
}

export interface AuditLogItem {
  id: string;
  event_type: string;
  target_type: string;
  target_id: string;
  actor: string;
  summary: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface AuditTrailResponse {
  total_events: number;
  events: AuditLogItem[];
}

export interface SystemComponentHealth {
  id: string;
  name: string;
  type: string;
  status: "ONLINE" | "DEGRADED" | "OFFLINE" | string;
  latency_ms: number;
  version: string;
  details: string;
}

export interface SystemHealthDetailsResponse {
  status: string;
  environment: string;
  components: SystemComponentHealth[];
  timestamp: string;
}

