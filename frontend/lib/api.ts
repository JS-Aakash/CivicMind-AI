// CivicMind AI — API Client

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

import type {
  ComplaintListResponse,
  Complaint,
  IncidentListResponse,
  Incident,
  MapDataResponse,
  LanguageDetectResponse,
  GrievanceAnalyzeResponse,
  ModelStatusResponse,
  HealthResponse,
} from "./types";

// Health
export const getHealth = () => fetchAPI<HealthResponse>("/api/health");

// Models
export const getModelStatus = () => fetchAPI<ModelStatusResponse>("/api/model/status");

// Language
export const detectLanguage = (text: string) =>
  fetchAPI<LanguageDetectResponse>("/api/language/detect", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

// Grievances
export const listGrievances = (params?: {
  page?: number;
  page_size?: number;
  category?: string;
  priority?: string;
  status?: string;
}) => {
  const qs = new URLSearchParams(
    Object.entries(params || {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  ).toString();
  return fetchAPI<ComplaintListResponse>(`/api/grievances${qs ? "?" + qs : ""}`);
};

export const getGrievance = (id: string) =>
  fetchAPI<Complaint>(`/api/grievances/${id}`);

export const analyzeGrievance = (data: {
  text: string;
  location_text?: string;
  latitude?: number;
  longitude?: number;
}) =>
  fetchAPI<GrievanceAnalyzeResponse>("/api/grievances/analyze", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const createGrievance = (data: {
  text?: string;
  media_ids?: string[];
  audio_id?: string;
  raw_transcript?: string;
  edited_transcript?: string;
  location_text?: string;
  latitude?: number;
  longitude?: number;
  ward?: string;
}) =>
  fetchAPI<Complaint>("/api/grievances", {
    method: "POST",
    body: JSON.stringify(data),
  });

// Map
export const getMapComplaints = (params?: {
  category?: string;
  priority?: string;
  incident_id?: string;
  min_lat?: number;
  max_lat?: number;
  min_lng?: number;
  max_lng?: number;
}) => {
  const qs = new URLSearchParams(
    Object.entries(params || {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  ).toString();
  return fetchAPI<MapDataResponse>(`/api/map/complaints${qs ? "?" + qs : ""}`);
};

export const getMapIncidents = (params?: { category?: string; priority?: string; status?: string }) => {
  const qs = new URLSearchParams(
    Object.entries(params || {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  ).toString();
  return fetchAPI<MapIncidentMarker[]>(`/api/map/incidents${qs ? "?" + qs : ""}`);
};

// Incidents
export const listIncidents = (params?: {
  category?: string;
  priority?: string;
  status?: string;
  trend?: string;
  page?: number;
  page_size?: number;
}) => {
  const qs = new URLSearchParams(
    Object.entries(params || {})
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)])
  ).toString();
  return fetchAPI<IncidentListResponse>(`/api/incidents${qs ? "?" + qs : ""}`);
};

export const getIncident = (id: string) => fetchAPI<Incident>(`/api/incidents/${id}`);

export const recomputeIncidents = (params?: { hours?: number; category?: string; dry_run?: boolean }) =>
  fetchAPI<any>("/api/incidents/recompute", {
    method: "POST",
    body: JSON.stringify(params || { hours: 72, dry_run: false }),
  });

export const updateIncidentStatus = (id: string, status: string, notes?: string) =>
  fetchAPI<Incident>(`/api/incidents/${id}/status`, {
    method: "POST",
    body: JSON.stringify({ status, notes }),
  });

export const mergeIncidents = (id: string, target_incident_id: string, reason?: string) =>
  fetchAPI<Incident>(`/api/incidents/${id}/merge`, {
    method: "POST",
    body: JSON.stringify({ target_incident_id, reason }),
  });

export const splitIncident = (id: string, complaint_ids_for_new_incident: string[], reason?: string) =>
  fetchAPI<any>(`/api/incidents/${id}/split`, {
    method: "POST",
    body: JSON.stringify({ complaint_ids_for_new_incident, reason }),
  });

// Duplicate Detection & Relationships
import type { ComplaintDuplicatesResponse, MapIncidentMarker } from "./types";

export const getComplaintDuplicates = (id: string) =>
  fetchAPI<ComplaintDuplicatesResponse>(`/api/grievances/${id}/duplicates`);

// Module 2 — Training, Metrics & Dataset Management
import type {
  TrainingStatusResponse,
  ModelMetricsResponse,
  DatasetStatsResponse,
  RoutingKPIsResponse,
  DepartmentTarget,
} from "./types";

export const getTrainingStatus = () =>
  fetchAPI<TrainingStatusResponse>("/api/model/training-status");

export const triggerTraining = (epochs: number = 3, batch_size: number = 32) =>
  fetchAPI<{ status: string; message: string }>("/api/model/train", {
    method: "POST",
    body: JSON.stringify({ epochs, batch_size }),
  });

export const getModelMetrics = () =>
  fetchAPI<ModelMetricsResponse>("/api/model/metrics");

export const getModelComparison = () =>
  fetchAPI<any>("/api/model/comparison");

export const getInferenceBenchmark = () =>
  fetchAPI<any>("/api/model/benchmark");

export const getDatasetStats = () =>
  fetchAPI<DatasetStatsResponse>("/api/dataset/stats");

// Module 3 — Routing, Policies, KPIs & Officer Review
export const getDepartments = () =>
  fetchAPI<{ count: number; departments: any[] }>("/api/routing/departments");

export const getRoutingPolicies = () =>
  fetchAPI<any>("/api/routing/policies");

export const getRoutingKPIs = () =>
  fetchAPI<RoutingKPIsResponse>("/api/routing/kpis");

export const reviewComplaint = (id: string, decision: "APPROVE" | "REJECT" | "REASSIGN", notes?: string) =>
  fetchAPI<any>(`/api/grievances/${id}/review`, {
    method: "POST",
    body: JSON.stringify({ action: decision, notes }),
  });

export const overrideComplaintDecision = (
  id: string,
  override: {
    category?: string;
    subcategory?: string;
    priority?: string;
    department_id?: string;
    reason: string;
    officer_name?: string;
  }
) =>
  fetchAPI<any>(`/api/grievances/${id}/override`, {
    method: "POST",
    body: JSON.stringify(override),
  });

export const getComplaintRouting = (id: string) =>
  fetchAPI<any>(`/api/grievances/${id}/routing`);

export const getComplaintSLA = (id: string) =>
  fetchAPI<any>(`/api/grievances/${id}/sla`);

// ─── Module 5: Media & Multimodal Intelligence ──────────────────────────────
import type {
  VoiceTranscriptionItem,
  VisionAnalysisItem,
  CitizenTrackingResponse,
  MultimodalModelStatus,
} from "./types";

export const uploadAudio = async (file: File, language_hint?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  if (language_hint) formData.append("language_hint", language_hint);

  const res = await fetch(`${API_BASE}/api/media/audio`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Audio upload failed" }));
    throw new Error(err.detail || `Audio upload error: ${res.status}`);
  }
  return res.json();
};

export const uploadImage = async (file: File, complaint_text?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  if (complaint_text) formData.append("complaint_text", complaint_text);

  const res = await fetch(`${API_BASE}/api/media/images`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Image upload failed" }));
    throw new Error(err.detail || `Image upload error: ${res.status}`);
  }
  return res.json();
};

export const getMediaStatus = (media_id: string) =>
  fetchAPI<any>(`/api/media/${media_id}/status`);

export const retryMedia = (media_id: string) =>
  fetchAPI<any>(`/api/media/${media_id}/retry`, { method: "POST" });

export const getMultimodalModelStatus = () =>
  fetchAPI<MultimodalModelStatus>("/api/models/multimodal");

export const getVisionHealth = () =>
  fetchAPI<any>("/api/health/vision");

// ─── Module 5: Citizen Complaint Tracking ────────────────────────────────────

export const trackCitizenComplaint = (complaint_code: string) =>
  fetchAPI<CitizenTrackingResponse>(`/api/citizen/complaints/${complaint_code}`);

export const listCitizenComplaints = (limit: number = 20) =>
  fetchAPI<{ complaints: any[]; total: number }>(`/api/citizen/my-complaints?limit=${limit}`);

// ─── Module 6: Command Center & Analytics API Functions ──────────────────────
import type {
  CommandCenterOverviewResponse,
  AnalyticsSummaryResponse,
  AnalyticsTrendsResponse,
  AnalyticsCategoriesResponse,
  AnalyticsDepartmentsResponse,
  AnalyticsLanguagesResponse,
  AnalyticsSLAResponse,
  ReviewQueueResponse,
  OfficerDecisionPayload,
  FeedbackRecordsResponse,
  AuditTrailResponse,
  SystemHealthDetailsResponse,
} from "./types";

export const getCommandCenterOverview = () =>
  fetchAPI<CommandCenterOverviewResponse>("/api/command-center/overview");


export const getAnalyticsSummary = (timeframe: string = "7d", category?: string, department?: string) => {
  const params = new URLSearchParams({ timeframe });
  if (category) params.append("category", category);
  if (department) params.append("department", department);
  return fetchAPI<AnalyticsSummaryResponse>(`/api/analytics/summary?${params.toString()}`);
};

export const getAnalyticsTrends = (days: number = 7) =>
  fetchAPI<AnalyticsTrendsResponse>(`/api/analytics/trends?days=${days}`);

export const getAnalyticsCategories = () =>
  fetchAPI<AnalyticsCategoriesResponse>("/api/analytics/categories");

export const getAnalyticsDepartments = () =>
  fetchAPI<AnalyticsDepartmentsResponse>("/api/analytics/departments");

export const getAnalyticsLanguages = () =>
  fetchAPI<AnalyticsLanguagesResponse>("/api/analytics/languages");

export const getAnalyticsSLA = () =>
  fetchAPI<AnalyticsSLAResponse>("/api/analytics/sla");

export const getReviewQueue = () =>
  fetchAPI<ReviewQueueResponse>("/api/review/queue");

export const submitReviewDecision = (complaint_id: string, payload: OfficerDecisionPayload) =>
  fetchAPI<{ status: string; complaint_code: string; decision: string; message: string }>(
    `/api/review/${complaint_id}/decision`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );

export const getFeedbackRecords = () =>
  fetchAPI<FeedbackRecordsResponse>("/api/feedback");

export const getAuditTrail = (limit: number = 50) =>
  fetchAPI<AuditTrailResponse>(`/api/audit?limit=${limit}`);

export const getDetailedSystemHealth = () =>
  fetchAPI<SystemHealthDetailsResponse>("/api/system/health");


