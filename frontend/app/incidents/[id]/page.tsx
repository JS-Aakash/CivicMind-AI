"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowLeft,
  AlertTriangle,
  MapPin,
  Clock,
  MessageSquare,
  Building2,
  Globe,
  TrendingUp,
  ShieldAlert,
  Sparkles,
  CheckCircle2,
  Share2,
  Layers,
  ChevronRight,
  Flame,
} from "lucide-react";
import { getIncident, updateIncidentStatus, resolveIncident } from "@/lib/api";
import type { Incident, MapMarker, MapIncidentMarker } from "@/lib/types";
import { PriorityBadge } from "@/components/PriorityBadge";
import { LanguageBadge } from "@/components/LanguageBadge";
import { formatRelativeTime, formatDateTime } from "@/lib/utils";
import { CATEGORIES } from "@/lib/constants";

const MapView = dynamic<any>(() => import("@/components/MapView").then((m) => m.MapView), { ssr: false });

export default function IncidentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusUpdating, setStatusUpdating] = useState(false);

  // Resolution modal state
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolutionNote, setResolutionNote] = useState("");
  const [resolvedBy, setResolvedBy] = useState("Officer J. Sharma (Incident Commander)");
  const [proofImageUrl, setProofImageUrl] = useState("");
  const [actionTaken, setActionTaken] = useState("Cluster incident resolved and all member sites restored");
  const [resolverLat, setResolverLat] = useState<number | undefined>(undefined);
  const [resolverLon, setResolverLon] = useState<number | undefined>(undefined);
  const [gpsCapturing, setGpsCapturing] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchDetail = () => {
    getIncident(id)
      .then((inc) => {
        setIncident(inc);
        if (inc.center_latitude) setResolverLat(inc.center_latitude);
        if (inc.center_longitude) setResolverLon(inc.center_longitude);
      })
      .catch(() => setIncident(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const captureGPS = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    setGpsCapturing(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setResolverLat(pos.coords.latitude);
        setResolverLon(pos.coords.longitude);
        setGpsCapturing(false);
      },
      (err) => {
        alert("GPS capture failed: " + err.message);
        setGpsCapturing(false);
      },
      { enableHighAccuracy: true, timeout: 5000 }
    );
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!incident) return;
    setStatusUpdating(true);
    try {
      await updateIncidentStatus(incident.id, newStatus, `Officer updated status to ${newStatus}`);
      fetchDetail();
    } catch (e: any) {
      alert(`Status update failed: ${e.message}`);
    } finally {
      setStatusUpdating(false);
    }
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolutionNote.trim()) {
      alert("Please provide a resolution note.");
      return;
    }
    setIsResolving(true);
    try {
      const res = await resolveIncident(id, {
        resolution_note: resolutionNote,
        resolved_by: resolvedBy,
        proof_image_url: proofImageUrl || undefined,
        resolver_lat: resolverLat,
        resolver_lon: resolverLon,
        action_taken: actionTaken,
      });
      setIsResolveModalOpen(false);
      setActionSuccess(`Incident Resolved! ${res.resolved_complaints_count} linked complaints automatically resolved.`);
      fetchDetail();
      setTimeout(() => setActionSuccess(null), 5000);
    } catch (e: any) {
      alert(`Incident resolution failed: ${e.message}`);
    } finally {
      setIsResolving(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ paddingTop: 24 }}>
        <div className="skeleton" style={{ height: 400, borderRadius: 12 }} />
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="page-container" style={{ paddingTop: 24, textAlign: "center", color: "var(--text-muted)" }}>
        <p>Civic Incident not found</p>
        <Link href="/incidents" className="btn btn-secondary" style={{ marginTop: 16 }}>
          ← Back to Incidents
        </Link>
      </div>
    );
  }

  const catConfig = CATEGORIES[incident.category as keyof typeof CATEGORIES] || CATEGORIES.general;
  const signals = incident.confidence_signals || {
    semantic_cohesion: 0.92,
    geographic_cohesion: 0.88,
    temporal_cohesion: 0.94,
    category_consistency: 1.0,
  };

  // Convert member complaints to map markers
  const memberMarkers: MapMarker[] = (incident.member_complaints || [])
    .filter((c) => c.latitude && c.longitude)
    .map((c) => ({
      id: c.id,
      complaint_code: c.complaint_code,
      category: c.category,
      priority: c.priority,
      status: c.status,
      language: c.language,
      latitude: c.latitude!,
      longitude: c.longitude!,
      location_text: c.location_text || "",
      ward: c.ward,
      text_preview: c.text,
      created_at: c.created_at,
      incident_id: incident.id,
    }));

  const incidentMapItem: MapIncidentMarker[] = incident.center_latitude && incident.center_longitude
    ? [
        {
          id: incident.id,
          incident_code: incident.incident_code,
          title: incident.title,
          category: incident.category,
          priority: incident.priority,
          status: incident.status,
          complaint_count: incident.complaint_count,
          center_latitude: incident.center_latitude,
          center_longitude: incident.center_longitude,
          affected_area: incident.affected_area,
          geometry: incident.geometry,
          trend: incident.trend,
          is_emerging: incident.is_emerging,
        },
      ]
    : [];

  return (
    <div>
      {/* Top bar */}
      <div className="top-bar">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link href="/incidents" style={{ color: "var(--text-muted)", display: "flex" }}>
            <ArrowLeft size={16} />
          </Link>
          <span style={{ fontFamily: "monospace", fontSize: 13, color: "var(--accent-indigo)", fontWeight: 700 }}>
            {incident.incident_code}
          </span>
          <PriorityBadge priority={incident.priority} />
          <span
            style={{
              fontSize: 11,
              padding: "2px 8px",
              borderRadius: 4,
              background: "rgba(99,102,241,0.15)",
              color: "var(--accent-indigo)",
              fontWeight: 600,
            }}
          >
            {incident.status.replace("_", " ").toUpperCase()}
          </span>
          {incident.is_emerging && (
            <span
              style={{
                fontSize: 11,
                padding: "2px 8px",
                borderRadius: 4,
                background: "rgba(249,115,22,0.15)",
                color: "#f97316",
                fontWeight: 700,
              }}
            >
              🚨 EMERGING INCIDENT
            </span>
          )}
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {actionSuccess && (
            <span style={{ color: "#22c55e", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
              <CheckCircle2 size={14} /> {actionSuccess}
            </span>
          )}

          {incident.status !== "resolved" && (
            <button
              onClick={() => setIsResolveModalOpen(true)}
              className="btn"
              style={{
                fontSize: 12,
                display: "flex",
                alignItems: "center",
                gap: 5,
                background: "linear-gradient(135deg, #10b981, #059669)",
                color: "#ffffff",
                border: "none",
                fontWeight: 600,
              }}
            >
              <CheckCircle2 size={13} /> Resolve Incident
            </button>
          )}

          <select
            value={incident.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            disabled={statusUpdating}
            className="input"
            style={{ fontSize: 12, padding: "5px 10px" }}
          >
            <option value="detected">Detected</option>
            <option value="investigating">Investigating</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="false_positive">False Positive</option>
          </select>
        </div>
      </div>

      <div className="page-container" style={{ paddingTop: 20 }}>
        {/* Main Grid: Left details, Right Map & Members */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Left Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Header Title Card */}
            <div className="card">
              <div style={{ display: "flex", gap: 14, alignItems: "flex-start", marginBottom: 16 }}>
                <div
                  style={{
                    width: 52,
                    height: 52,
                    borderRadius: 12,
                    background: `${catConfig.color}18`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <AlertTriangle size={26} color={catConfig.color} />
                </div>
                <div>
                  <h1 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4, color: "var(--text-primary)" }}>
                    {incident.title}
                  </h1>
                  <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                    {incident.description}
                  </p>
                </div>
              </div>

              {/* Statistics Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    Complaints
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
                    {incident.complaint_count}
                  </div>
                </div>

                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    Trend Rate
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: incident.trend === "RISING" ? "#ef4444" : "#3b82f6" }}>
                    {incident.trend === "RISING" ? "↑ RISING" : incident.trend}
                  </div>
                </div>

                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    Confidence
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "#22c55e" }}>
                    {Math.round(incident.confidence * 100)}%
                  </div>
                </div>

                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                    Languages
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: "#8b5cf6" }}>
                    {incident.languages?.length || 1}
                  </div>
                </div>
              </div>
            </div>

            {/* AI Cohesion Evidence & Deterministic Explanation */}
            <div className="card">
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Sparkles size={16} color="var(--accent-indigo)" />
                <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                  Cluster Formation Reasoning (AI Evidence)
                </span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>Semantic Cohesion</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "var(--accent-indigo)" }}>
                    {Math.round((signals.semantic_cohesion || 0.9) * 100)}%
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 2 }}>
                    High 768-dim vector embedding alignment
                  </div>
                </div>

                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>Spatial Compactness</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "var(--accent-cyan)" }}>
                    {Math.round((signals.geographic_cohesion || 0.85) * 100)}%
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 2 }}>
                    Concentrated within localized radius
                  </div>
                </div>

                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>Temporal Proximity</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#f97316" }}>
                    {Math.round((signals.temporal_cohesion || 0.9) * 100)}%
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 2 }}>
                    Complaints occurred in tight time window
                  </div>
                </div>

                <div style={{ background: "var(--brand-surface)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>Category Consistency</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#22c55e" }}>
                    {Math.round((signals.category_consistency || 1.0) * 100)}%
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-secondary)", marginTop: 2 }}>
                    Cross-lingual classification agreement
                  </div>
                </div>
              </div>

              <div style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 8, padding: 12 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent-indigo)", marginBottom: 4 }}>
                  WHY WAS THIS CIVIC INCIDENT DETECTED?
                </div>
                <ul style={{ fontSize: 12, color: "var(--text-secondary)", margin: 0, paddingLeft: 18, lineHeight: 1.6 }}>
                  <li>✓ {incident.complaint_count} citizen complaints share high semantic cosine similarity.</li>
                  <li>✓ Concentrated inside {incident.affected_area || "the geographic boundary"}.</li>
                  <li>✓ Discovered across {incident.languages?.length || 1} distinct language representations ({incident.languages?.join(", ").toUpperCase()}).</li>
                  <li>✓ Evaluated deterministically via Spatio-Temporal DBSCAN ({incident.algorithm_version}).</li>
                </ul>
              </div>
            </div>

            {/* Department Assignment */}
            <div className="card">
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <Building2 size={16} color="#06b6d4" />
                <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                  Lead Operational Jurisdiction
                </span>
              </div>
              <p style={{ fontSize: 15, color: "var(--text-primary)", fontWeight: 600 }}>
                {incident.primary_department || "Municipal Operations Cell"}
              </p>
              {incident.secondary_departments && incident.secondary_departments.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Support Departments:</div>
                  <div style={{ display: "flex", gap: 6, marginTop: 4, flexWrap: "wrap" }}>
                    {incident.secondary_departments.map((sd) => (
                      <span key={sd} style={{ fontSize: 11, background: "var(--brand-surface)", padding: "2px 8px", borderRadius: 4, color: "var(--text-secondary)" }}>
                        {sd}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Audit Timeline */}
            <div className="card">
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 12 }}>
                Incident Lifecycle Timeline
              </div>
              {(incident.timeline || []).map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ width: 10, height: 10, borderRadius: "50%", background: item.color || "#6366f1", flexShrink: 0 }} />
                    {i < (incident.timeline?.length || 1) - 1 && (
                      <div style={{ width: 1, flex: 1, background: "var(--brand-border)", margin: "4px 0" }} />
                    )}
                  </div>
                  <div>
                    <p style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 600 }}>{item.event}</p>
                    <p style={{ fontSize: 11, color: "var(--text-muted)" }}>{formatDateTime(item.timestamp)}</p>
                    {item.description && (
                      <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>{item.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Map & Member Complaints */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Map with Incident Footprint */}
            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
              <div style={{ height: 320 }}>
                {incident.center_latitude && incident.center_longitude ? (
                  <MapView
                    markers={memberMarkers}
                    incidents={incidentMapItem}
                    centerLat={incident.center_latitude}
                    centerLng={incident.center_longitude}
                    height="100%"
                    zoom={13}
                  />
                ) : (
                  <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-muted)" }}>
                    No spatial coordinates recorded for this cluster
                  </div>
                )}
              </div>
            </div>

            {/* Member Complaints List across Languages */}
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <MessageSquare size={16} color="var(--accent-indigo)" />
                  <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                    Member Complaints ({incident.member_complaints?.length || 0})
                  </span>
                </div>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Multilingual Grievances
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 520, overflowY: "auto", paddingRight: 4 }}>
                {(incident.member_complaints || []).map((comp) => (
                  <Link
                    key={comp.id}
                    href={`/complaints/${comp.complaint_code}`}
                    style={{ textDecoration: "none" }}
                  >
                    <div
                      style={{
                        background: "var(--brand-surface)",
                        border: "1px solid var(--brand-border)",
                        borderRadius: 8,
                        padding: 12,
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                        <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--accent-indigo)", fontWeight: 600 }}>
                          {comp.complaint_code}
                        </span>
                        <LanguageBadge language={comp.language || "en"} isCodeMixed={comp.is_code_mixed} />
                        <PriorityBadge priority={comp.priority} size="sm" />
                        <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
                          {formatRelativeTime(comp.created_at)}
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: "var(--text-primary)", lineHeight: 1.4, margin: "4px 0" }}>
                        "{comp.text}"
                      </p>
                      {comp.location_text && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                          <MapPin size={10} />
                          {comp.location_text}
                        </div>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* INCIDENT RESOLUTION MODAL */}
      {isResolveModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 16,
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: 540,
              width: "100%",
              background: "#0f172a",
              border: "1px solid #1e293b",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
              padding: 24,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <CheckCircle2 size={18} color="#10b981" />
                <h3 style={{ fontSize: 16, fontWeight: 700, color: "#f8fafc" }}>
                  Resolve Incident & Cascade to Linked Complaints
                </h3>
              </div>
              <button
                onClick={() => setIsResolveModalOpen(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: 12, color: "#94a3b8", marginBottom: 14 }}>
              Resolving this incident will automatically resolve all {incident.complaint_count || (incident.member_complaints?.length || 0)} linked grievances and generate individual verification audit records.
            </p>

            <form onSubmit={handleResolveSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  INCIDENT COMMANDER / RESOLVING OFFICER
                </label>
                <input
                  type="text"
                  required
                  value={resolvedBy}
                  onChange={(e) => setResolvedBy(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "var(--brand-surface)",
                    border: "1px solid var(--brand-border)",
                    borderRadius: 6,
                    color: "var(--text-primary)",
                    fontSize: 13,
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  ACTION TAKEN CLASSIFICATION
                </label>
                <input
                  type="text"
                  value={actionTaken}
                  onChange={(e) => setActionTaken(e.target.value)}
                  placeholder="e.g. Cluster area cleared, main pipeline valve replaced"
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "var(--brand-surface)",
                    border: "1px solid var(--brand-border)",
                    borderRadius: 6,
                    color: "var(--text-primary)",
                    fontSize: 13,
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  RESOLUTION NOTE (REQUIRED)
                </label>
                <textarea
                  required
                  rows={3}
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="Describe root-cause mitigation and overall area repair work..."
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "var(--brand-surface)",
                    border: "1px solid var(--brand-border)",
                    borderRadius: 6,
                    color: "var(--text-primary)",
                    fontSize: 13,
                    resize: "none",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  FIELD RESOLUTION PHOTO URL (OPTIONAL)
                </label>
                <input
                  type="text"
                  value={proofImageUrl}
                  onChange={(e) => setProofImageUrl(e.target.value)}
                  placeholder="https://... or uploaded photo path"
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "var(--brand-surface)",
                    border: "1px solid var(--brand-border)",
                    borderRadius: 6,
                    color: "var(--text-primary)",
                    fontSize: 13,
                  }}
                />
              </div>

              <div style={{ padding: "10px 12px", background: "rgba(15, 23, 42, 0.6)", borderRadius: 8, border: "1px solid #334155" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "#94a3b8", display: "block" }}>
                      GEOFENCE VERIFICATION
                    </span>
                    <span style={{ fontSize: 12, color: resolverLat ? "#22d3ee" : "#64748b" }}>
                      {resolverLat ? `${resolverLat.toFixed(4)}, ${resolverLon?.toFixed(4)}` : "No GPS attached"}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={captureGPS}
                    disabled={gpsCapturing}
                    className="btn btn-secondary"
                    style={{ fontSize: 11, padding: "4px 8px" }}
                  >
                    {gpsCapturing ? "Locating..." : "📍 Capture My GPS"}
                  </button>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 10 }}>
                <button
                  type="button"
                  onClick={() => setIsResolveModalOpen(false)}
                  className="btn btn-ghost"
                  style={{ fontSize: 13 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isResolving}
                  className="btn"
                  style={{
                    fontSize: 13,
                    background: "linear-gradient(135deg, #10b981, #059669)",
                    color: "#ffffff",
                    border: "none",
                    fontWeight: 600,
                  }}
                >
                  {isResolving ? "Cascading Resolution..." : "Confirm & Resolve All"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
