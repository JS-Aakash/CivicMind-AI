"use client";

import React, { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  MapPin,
  Clock,
  Building2,
  Globe,
  Tag,
  Zap,
  CheckCircle,
  User,
  ShieldCheck,
  Edit3,
  Check,
  X,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { getGrievance, overrideComplaintDecision, reviewComplaint, getDepartments, getComplaintDuplicates } from "@/lib/api";
import type { Complaint, ComplaintDuplicatesResponse } from "@/lib/types";
import { AIAnalysisPanel } from "@/components/AIAnalysisPanel";
import { PriorityBadge } from "@/components/PriorityBadge";
import { LanguageBadge } from "@/components/LanguageBadge";
import { formatDateTime, formatRelativeTime, confidencePercent } from "@/lib/utils";
import { CATEGORIES, STATUSES } from "@/lib/constants";
import type { AIAnalysisResult } from "@/lib/types";

export default function ComplaintDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [duplicatesData, setDuplicatesData] = useState<ComplaintDuplicatesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Override / Review state
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false);
  const [departments, setDepartments] = useState<any[]>([]);
  const [overrideCategory, setOverrideCategory] = useState("");
  const [overridePriority, setOverridePriority] = useState("");
  const [overrideDepartment, setOverrideDepartment] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [officerName, setOfficerName] = useState("Officer J. Sharma");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    getGrievance(id)
      .then((c) => {
        setComplaint(c);
        setOverrideCategory(c.category || "water");
        setOverridePriority(c.priority || "medium");
        setOverrideDepartment(c.department_id || "water_supply");
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

    getComplaintDuplicates(id)
      .then(setDuplicatesData)
      .catch(() => setDuplicatesData(null));

    getDepartments()
      .then((res) => setDepartments(res.departments || []))
      .catch(() => {});
  }, [id]);

  const handleReviewAction = async (action: "APPROVE" | "REJECT" | "REASSIGN") => {
    try {
      await reviewComplaint(id, action, `Officer action: ${action}`);
      setActionSuccess(`Routing successfully updated with ${action} action.`);
      const updated = await getGrievance(id);
      setComplaint(updated);
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (e: any) {
      alert(`Review action failed: ${e.message}`);
    }
  };

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideReason.trim()) {
      alert("Please provide a reason for the override.");
      return;
    }
    try {
      await overrideComplaintDecision(id, {
        category: overrideCategory,
        priority: overridePriority,
        department_id: overrideDepartment,
        reason: overrideReason,
        officer_name: officerName,
      });
      setActionSuccess("Override recorded with full audit trail. Original AI decision preserved.");
      setIsOverrideModalOpen(false);
      const updated = await getGrievance(id);
      setComplaint(updated);
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (e: any) {
      alert(`Override failed: ${e.message}`);
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ paddingTop: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr 1fr", gap: 20 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: 400, borderRadius: 12 }} />
          ))}
        </div>
      </div>
    );
  }

  if (error || !complaint) {
    return (
      <div className="page-container" style={{ paddingTop: 24, textAlign: "center", color: "var(--text-muted)" }}>
        <p>Complaint not found: {error}</p>
        <Link href="/complaints" className="btn btn-secondary" style={{ marginTop: 16 }}>
          ← Back to Complaints
        </Link>
      </div>
    );
  }

  const catConfig = CATEGORIES[complaint.category as keyof typeof CATEGORIES] || CATEGORIES.general;

  // Canonical AI analysis construction
  const canonicalAnalysis: AIAnalysisResult = {
    primary_language: complaint.language || "en",
    language_name: complaint.detected_languages?.join("+") || complaint.language || "en",
    languages: complaint.detected_languages || [complaint.language || "en"],
    script: complaint.script || "roman",
    is_code_mixed: complaint.is_code_mixed,
    is_grievance: complaint.is_grievance ?? true,
    category: complaint.category || "general",
    subcategory: complaint.subcategory,
    severity: complaint.severity || "moderate",
    priority: complaint.priority,
    confidence: complaint.confidence || 0.88,
    entities: (complaint.entities as Record<string, unknown>) || {},
    duration_mentioned: complaint.duration_mentioned,
    department_code: complaint.department_id || "GENERAL_GRIEVANCE",
    department_name: complaint.department_id
      ? complaint.department_id.replace(/_/g, " ").toUpperCase()
      : "Department",
    routing_reason: complaint.ai_explanation || "Assigned via CivicMind Smart Routing Engine",
    explanation: complaint.ai_explanation || "",
    is_mock: false,
    model_version: "muril-v1.1",
    routing_decision: (complaint.routing_decision as any) || "AUTO_ROUTE",
    requires_human_review: complaint.requires_human_review,
    sla: complaint.sla_due_at
      ? {
          response_minutes: 720,
          response_window_hours: 12,
          due_at: complaint.sla_due_at,
          status: (complaint.sla_status as any) || "within_sla",
        }
      : undefined,
  };

  return (
    <div>
      <div className="top-bar">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link href="/complaints" style={{ color: "var(--text-muted)", display: "flex" }}>
            <ArrowLeft size={16} />
          </Link>
          <span style={{ fontFamily: "monospace", fontSize: 13, color: "var(--accent-indigo)", fontWeight: 600 }}>
            {complaint.complaint_code}
          </span>
          <PriorityBadge priority={complaint.priority} />
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {actionSuccess && (
            <span style={{ color: "#22c55e", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
              <CheckCircle size={14} /> {actionSuccess}
            </span>
          )}
          <button
            onClick={() => setIsOverrideModalOpen(true)}
            className="btn btn-secondary"
            style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}
          >
            <Edit3 size={13} /> Officer Override
          </button>
          <span
            style={{
              padding: "5px 12px",
              borderRadius: 6,
              fontSize: 12,
              background: "rgba(99,102,241,0.1)",
              color: "var(--accent-indigo)",
              border: "1px solid rgba(99,102,241,0.2)",
            }}
          >
            {STATUSES[complaint.status as keyof typeof STATUSES]?.label || complaint.status}
          </span>
        </div>
      </div>

      <div className="page-container" style={{ paddingTop: 20 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr 1fr", gap: 16 }}>
          {/* LEFT: Citizen Complaint */}
          <div>
            <div className="card" style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <User size={14} color="var(--text-muted)" />
                <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  Original Complaint
                </span>
              </div>
              <div
                style={{
                  background: "var(--brand-surface)",
                  borderRadius: 8,
                  padding: 14,
                  fontSize: 14,
                  color: "var(--text-primary)",
                  lineHeight: 1.7,
                  marginBottom: 14,
                  borderLeft: "3px solid var(--accent-indigo)",
                }}
              >
                "{complaint.text}"
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                <LanguageBadge
                  language={complaint.language}
                  script={complaint.script}
                  isCodeMixed={complaint.is_code_mixed}
                  detectedLanguages={complaint.detected_languages}
                />
              </div>
            </div>

            {/* Location */}
            {(complaint.location_text || complaint.latitude) && (
              <div className="card" style={{ marginBottom: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                  <MapPin size={14} color="var(--accent-indigo)" />
                  <span style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                    Location Context
                  </span>
                </div>
                {complaint.location_text && (
                  <p style={{ fontSize: 14, color: "var(--text-primary)", marginBottom: 4 }}>
                    {complaint.location_text}
                  </p>
                )}
                {complaint.ward && (
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>{complaint.ward}</p>
                )}
                {complaint.latitude && (
                  <p style={{ fontSize: 11, fontFamily: "monospace", color: "var(--text-muted)", marginTop: 6 }}>
                    {complaint.latitude.toFixed(4)}, {complaint.longitude?.toFixed(4)}
                  </p>
                )}
              </div>
            )}

            {/* Timeline */}
            <div className="card">
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Clock size={14} color="var(--text-muted)" />
                <span style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                  Dispatch Lifecycle
                </span>
              </div>
              {[
                { event: "Complaint registered", time: complaint.created_at, icon: CheckCircle, color: "#22c55e" },
                { event: "MuRIL v1.1 classification", time: complaint.created_at, icon: Zap, color: "#6366f1" },
                { event: "Context & Safety rules evaluated", time: complaint.created_at, icon: ShieldCheck, color: "#f59e0b" },
                { event: "SLA timer initialized", time: complaint.created_at, icon: Clock, color: "#22d3ee" },
              ].map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <item.icon size={14} color={item.color} />
                    {i < 3 && <div style={{ width: 1, flex: 1, background: "var(--brand-border)", margin: "4px 0" }} />}
                  </div>
                  <div>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", fontWeight: 500 }}>{item.event}</p>
                    <p style={{ fontSize: 11, color: "var(--text-muted)" }}>{formatRelativeTime(item.time)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CENTER: AI Decision & Routing Panel */}
          <div>
            <AIAnalysisPanel analysis={canonicalAnalysis} isMock={false} />

            {/* Extracted entities */}
            {complaint.entities && Object.keys(complaint.entities).length > 0 && (
              <div className="card" style={{ marginTop: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                  <Tag size={14} color="var(--accent-indigo)" />
                  <span style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                    Structured Context Entities
                  </span>
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {Object.entries(complaint.entities).map(([key, value]) => (
                    <span key={key} style={{ padding: "4px 10px", borderRadius: 6, fontSize: 12, background: "rgba(99,102,241,0.1)", color: "var(--text-accent)", border: "1px solid rgba(99,102,241,0.2)" }}>
                      {key}: {String(value)}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Operational Dispatch & Officer Actions */}
          <div>
            <div className="card" style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <Building2 size={14} color="var(--accent-indigo)" />
                <span style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                  Officer Dispatch Desk
                </span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
                {catConfig.label} Department
              </div>
              <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 12 }}>
                {complaint.ai_explanation || "Auto-routed according to category and severity threshold policy."}
              </p>

              {/* Action Buttons */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <button
                  onClick={() => handleReviewAction("APPROVE")}
                  className="btn btn-primary"
                  style={{ fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
                >
                  <Check size={14} /> Confirm & Dispatch
                </button>
                <button
                  onClick={() => setIsOverrideModalOpen(true)}
                  className="btn btn-secondary"
                  style={{ fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
                >
                  <Edit3 size={14} /> Reassign / Override
                </button>
              </div>
            </div>

            {/* SLA countdown badge */}
            <div className="card" style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <Clock size={14} color="#f59e0b" />
                <span style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                  SLA Target Window
                </span>
              </div>
              <div style={{ padding: 12, background: "rgba(0,0,0,0.2)", borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>ESTIMATED DUE AT</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                  {complaint.sla_due_at ? formatDateTime(complaint.sla_due_at) : "Standard 12h Turnaround"}
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "#22c55e", fontWeight: 600 }}>
                  ✓ Status: {complaint.sla_status?.replace(/_/g, " ").toUpperCase() || "WITHIN SLA"}
                </div>
              </div>
            </div>

            {/* Multi-Factor Duplicate & Related Grievances (Module 4) */}
            <div className="card" style={{ height: 420, display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Globe size={16} color="var(--accent-indigo)" />
                  <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                    Duplicate & Related Grievances
                  </span>
                </div>
                {duplicatesData && (
                  <span style={{ fontSize: 11, color: "var(--accent-indigo)", fontWeight: 600 }}>
                    {duplicatesData.total_relationships} Found
                  </span>
                )}
              </div>

              {duplicatesData && (duplicatesData.duplicates.length > 0 || duplicatesData.related.length > 0) ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1, overflowY: "auto", paddingRight: 6 }}>
                  {/* Duplicates */}
                  {duplicatesData.duplicates.map((dup) => (
                    <div
                      key={dup.target_complaint_id}
                      style={{
                        background: "rgba(239, 68, 68, 0.08)",
                        border: "1px solid rgba(239, 68, 68, 0.25)",
                        borderRadius: 8,
                        padding: 12,
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontFamily: "monospace", fontSize: 12, color: "#ef4444", fontWeight: 700 }}>
                          {dup.target_complaint_code}
                        </span>
                        <span style={{ fontSize: 10, background: "rgba(239,68,68,0.2)", color: "#ef4444", padding: "1px 6px", borderRadius: 4, fontWeight: 700 }}>
                          POSSIBLE DUPLICATE ({Math.round(dup.similarity_score * 100)}%)
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: "var(--text-primary)", margin: "4px 0" }}>
                        "{dup.target_text_preview}"
                      </p>
                      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 6, lineHeight: 1.4 }}>
                        {dup.explanation}
                      </div>
                      <Link
                        href={`/complaints/${dup.target_complaint_code}`}
                        style={{ display: "inline-block", marginTop: 6, fontSize: 11, color: "var(--accent-indigo)", textDecoration: "none", fontWeight: 600 }}
                      >
                        Compare Grievance Record →
                      </Link>
                    </div>
                  ))}

                  {/* Related */}
                  {duplicatesData.related.map((rel) => (
                    <div
                      key={rel.target_complaint_id}
                      style={{
                        background: "var(--brand-surface)",
                        border: "1px solid var(--brand-border)",
                        borderRadius: 8,
                        padding: 12,
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--accent-indigo)", fontWeight: 600 }}>
                          {rel.target_complaint_code}
                        </span>
                        <span style={{ fontSize: 10, background: "rgba(99,102,241,0.15)", color: "var(--accent-indigo)", padding: "1px 6px", borderRadius: 4, fontWeight: 600 }}>
                          RELATED ({Math.round(rel.similarity_score * 100)}%)
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "4px 0" }}>
                        "{rel.target_text_preview}"
                      </p>
                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                        {rel.explanation}
                      </div>
                      <Link
                        href={`/complaints/${rel.target_complaint_code}`}
                        style={{ display: "inline-block", marginTop: 6, fontSize: 11, color: "var(--accent-indigo)", textDecoration: "none", fontWeight: 600 }}
                      >
                        View Related →
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <div
                  style={{
                    padding: "16px",
                    textAlign: "center",
                    color: "var(--text-muted)",
                    fontSize: 12,
                    borderRadius: 8,
                    background: "var(--brand-surface)",
                  }}
                >
                  <CheckCircle size={18} color="#22c55e" style={{ margin: "0 auto 6px" }} />
                  <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>Unique Grievance Record</p>
                  <p style={{ fontSize: 11, marginTop: 4 }}>
                    No duplicate or highly similar complaint detected within current spatial/temporal window.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* OFFICER OVERRIDE MODAL */}
      {isOverrideModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: 520,
              background: "var(--brand-card)",
              border: "1px solid var(--brand-border)",
              borderRadius: 12,
              padding: 24,
              boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Edit3 size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: 16, fontWeight: 600 }}>Human-In-The-Loop Officer Override</h3>
              </div>
              <button
                onClick={() => setIsOverrideModalOpen(false)}
                style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <X size={18} />
              </button>
            </div>

            <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16 }}>
              Overrides are recorded to the audit trail while preserving the original AI prediction.
            </p>

            <form onSubmit={handleOverrideSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  REASSIGN DEPARTMENT
                </label>
                <select
                  value={overrideDepartment}
                  onChange={(e) => setOverrideDepartment(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "var(--brand-surface)",
                    border: "1px solid var(--brand-border)",
                    borderRadius: 6,
                    color: "var(--text-primary)",
                    fontSize: 13,
                  }}
                >
                  {departments.length > 0 ? (
                    departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="water_supply">Water Supply Department</option>
                      <option value="roads_highways">Municipal Engineering / Roads Department</option>
                      <option value="sanitation">Sanitation Department</option>
                      <option value="electricity_board">Electricity Department</option>
                      <option value="drainage">Drainage Department</option>
                      <option value="public_safety">Public Safety / Emergency</option>
                    </>
                  )}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                    CATEGORY
                  </label>
                  <select
                    value={overrideCategory}
                    onChange={(e) => setOverrideCategory(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      background: "var(--brand-surface)",
                      border: "1px solid var(--brand-border)",
                      borderRadius: 6,
                      color: "var(--text-primary)",
                      fontSize: 13,
                    }}
                  >
                    {Object.entries(CATEGORIES).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                    PRIORITY LEVEL
                  </label>
                  <select
                    value={overridePriority}
                    onChange={(e) => setOverridePriority(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      background: "var(--brand-surface)",
                      border: "1px solid var(--brand-border)",
                      borderRadius: 6,
                      color: "var(--text-primary)",
                      fontSize: 13,
                    }}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  OFFICER NAME / ID
                </label>
                <input
                  type="text"
                  value={officerName}
                  onChange={(e) => setOfficerName(e.target.value)}
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
                  REASON FOR OVERRIDE (REQUIRED AUDIT TRAIL)
                </label>
                <textarea
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Field officer inspected site, emergency drainage backflow requires immediate health & sanitation team dispatch."
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

              <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 10 }}>
                <button
                  type="button"
                  onClick={() => setIsOverrideModalOpen(false)}
                  className="btn btn-ghost"
                  style={{ fontSize: 13 }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" style={{ fontSize: 13 }}>
                  Save Override & Reassign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
