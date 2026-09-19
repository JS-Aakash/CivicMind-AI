"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Edit3,
  XCircle,
  Brain,
  UserCheck,
  Clock,
  ArrowRight,
  Sparkles,
  Info,
  Check,
  Layers,
} from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { getReviewQueue, submitReviewDecision } from "@/lib/api";
import { ReviewQueueItem, OfficerDecisionPayload } from "@/lib/types";

export default function HumanReviewPage() {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [selectedCase, setSelectedCase] = useState<ReviewQueueItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Form states for officer override
  const [editCategory, setEditCategory] = useState("");
  const [editPriority, setEditPriority] = useState("");
  const [editDepartment, setEditDepartment] = useState("");
  const [editSlaHours, setEditSlaHours] = useState(24);
  const [officerReason, setOfficerReason] = useState("");

  const loadQueue = async () => {
    try {
      setLoading(true);
      const res = await getReviewQueue();
      if (res && res.items) {
        setQueue(res.items);
        if (res.items.length > 0 && !selectedCase) {
          selectCase(res.items[0]);
        }
      }
    } catch (err) {
      console.error("Failed to load review queue:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const selectCase = (c: ReviewQueueItem) => {
    setSelectedCase(c);
    setEditCategory(c.category || "roads");
    setEditPriority(c.priority || "high");
    setEditDepartment(c.department_name || "Roads & Bridges Department");
    setEditSlaHours(c.sla_hours || 24);
    setOfficerReason("");
  };

  const handleDecision = async (action: "accept" | "modify" | "reject") => {
    if (!selectedCase) return;
    try {
      setSubmitting(true);
      const payload: OfficerDecisionPayload = {
        action,
        category: editCategory,
        priority: editPriority,
        department_name: editDepartment,
        sla_hours: editSlaHours,
        officer_name: "Admin Officer (Review Center)",
        reason: officerReason || (action === "accept" ? "AI prediction verified and accepted." : "Officer manual correction."),
      };

      await submitReviewDecision(selectedCase.id, payload);

      setToastMessage(`Case ${selectedCase.complaint_code} decision recorded: ${action.toUpperCase()}`);
      setTimeout(() => setToastMessage(null), 4000);

      // Remove from active queue locally
      const remaining = queue.filter((item) => item.id !== selectedCase.id);
      setQueue(remaining);
      if (remaining.length > 0) {
        selectCase(remaining[0]);
      } else {
        setSelectedCase(null);
      }
    } catch (err) {
      console.error("Failed to submit decision:", err);
      alert("Failed to submit review decision");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", backgroundColor: "#060911" }}>
      <TopBar
        title="Human Review Center"
        subtitle="AI-in-the-Loop Verification & Calibration"
        breadcrumbs={[{ label: "Operations", href: "/command-center" }, { label: "Human Review" }]}
      />

      {toastMessage && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            backgroundColor: "#0d1424",
            border: "1px solid #22c55e",
            borderRadius: "8px",
            padding: "12px 18px",
            color: "#4ade80",
            fontSize: "13px",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.8)",
            zIndex: 9999,
            animation: "fadeIn 0.2s ease-in-out",
          }}
        >
          <CheckCircle2 size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      <div style={{ padding: "16px 20px", flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Banner */}
        <div
          style={{
            backgroundColor: "rgba(99, 102, 241, 0.08)",
            border: "1px solid rgba(99, 102, 241, 0.25)",
            borderRadius: "10px",
            padding: "12px 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Brain size={18} color="#818cf8" />
            <div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff" }}>
                AI Recommends. Human Decides When Uncertain.
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Cases in this queue triggered confidence thresholds (&lt;70%), multimodal cross-evidence conflicts, or multi-department overlaps.
              </div>
            </div>
          </div>
          <div
            style={{
              fontSize: "12px",
              fontWeight: 700,
              color: "#f87171",
              backgroundColor: "rgba(239, 68, 68, 0.12)",
              padding: "4px 10px",
              borderRadius: "6px",
              border: "1px solid rgba(239, 68, 68, 0.3)",
            }}
          >
            {queue.length} Cases Require Verification
          </div>
        </div>

        {/* Main Grid: Queue on Left, Side-by-Side Review on Right */}
        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "16px" }}>
          {/* Queue List */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "14px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              maxHeight: "calc(100vh - 200px)",
              overflowY: "auto",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Pending Verification ({queue.length})
            </div>

            {queue.length === 0 ? (
              <div style={{ padding: "40px 16px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                <CheckCircle2 size={32} color="#22c55e" style={{ margin: "0 auto 10px auto" }} />
                <div>All pending cases reviewed.</div>
                <div style={{ fontSize: "11px", marginTop: "4px" }}>System is running autonomously within confidence bounds.</div>
              </div>
            ) : (
              queue.map((item) => {
                const isSelected = selectedCase?.id === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => selectCase(item)}
                    style={{
                      padding: "12px",
                      borderRadius: "8px",
                      backgroundColor: isSelected ? "rgba(99, 102, 241, 0.12)" : "rgba(255, 255, 255, 0.02)",
                      border: isSelected
                        ? "1px solid rgba(99, 102, 241, 0.4)"
                        : "1px solid rgba(255, 255, 255, 0.05)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: "#ffffff" }}>
                        {item.complaint_code}
                      </span>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: "4px",
                          backgroundColor:
                            item.priority === "critical"
                              ? "rgba(239, 68, 68, 0.2)"
                              : "rgba(245, 158, 11, 0.2)",
                          color: item.priority === "critical" ? "#ef4444" : "#f59e0b",
                        }}
                      >
                        {item.priority?.toUpperCase()}
                      </span>
                    </div>

                    <div style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: 1.3 }}>
                      "{item.text.length > 70 ? item.text.substring(0, 70) + "..." : item.text}"
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "10px", color: "#94a3b8" }}>
                      <span style={{ color: "#fca5a5" }}>⚠ {Math.round(item.confidence * 100)}% Conf</span>
                      <span>·</span>
                      <span>{item.department_name}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Active Case Inspection & Officer Workflow */}
          {selectedCase ? (
            <div
              style={{
                backgroundColor: "#0d1424",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "12px",
                padding: "20px",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
              }}
            >
              {/* Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "14px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                      Case {selectedCase.complaint_code}
                    </h2>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "4px",
                        backgroundColor: "rgba(245, 158, 11, 0.15)",
                        color: "#fbbf24",
                        border: "1px solid rgba(245, 158, 11, 0.3)",
                      }}
                    >
                      Requires Officer Review
                    </span>
                  </div>
                  <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "2px" }}>
                    Flagged: {selectedCase.review_reason}
                  </div>
                </div>

                <div style={{ fontSize: "12px", color: "#64748b" }}>
                  Submitted: {new Date(selectedCase.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>

              {/* Citizen Text Quote */}
              <div
                style={{
                  backgroundColor: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "8px",
                  padding: "14px 16px",
                }}
              >
                <div style={{ fontSize: "10px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: "4px" }}>
                  Citizen Grievance Submission (Language: {selectedCase.language_name || selectedCase.language || "Tamil / Tanglish"})
                </div>
                <div style={{ fontSize: "14px", color: "#f8fafc", fontStyle: "italic", lineHeight: 1.4 }}>
                  "{selectedCase.text}"
                </div>
              </div>

              {/* SIDE BY SIDE: AI PREDICTION VS OFFICER CORRECTION */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                {/* Left: AI Assessment */}
                <div
                  style={{
                    backgroundColor: "rgba(99, 102, 241, 0.05)",
                    border: "1px solid rgba(99, 102, 241, 0.2)",
                    borderRadius: "10px",
                    padding: "16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid rgba(99, 102, 241, 0.15)", paddingBottom: "8px" }}>
                    <Brain size={16} color="#818cf8" />
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "#a5b4fc" }}>
                      AI Model Prediction (MuRIL v1.1)
                    </span>
                  </div>

                  <div>
                    <div style={{ fontSize: "11px", color: "#64748b" }}>Predicted Category</div>
                    <div style={{ fontSize: "14px", fontWeight: 600, color: "#ffffff", textTransform: "capitalize" }}>
                      {selectedCase.category}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "11px", color: "#64748b" }}>Assigned Priority</div>
                    <div style={{ fontSize: "14px", fontWeight: 700, color: "#ef4444", textTransform: "uppercase" }}>
                      {selectedCase.priority}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "11px", color: "#64748b" }}>Target Department</div>
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "#ffffff" }}>
                      {selectedCase.department_name}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: "11px", color: "#64748b" }}>Confidence Score</div>
                    <div style={{ fontSize: "13px", fontWeight: 700, color: "#fbbf24" }}>
                      {Math.round(selectedCase.confidence * 100)}% (Uncertainty threshold triggered)
                    </div>
                  </div>
                </div>

                {/* Right: Officer Override Form */}
                <div
                  style={{
                    backgroundColor: "rgba(34, 197, 94, 0.03)",
                    border: "1px solid rgba(34, 197, 94, 0.25)",
                    borderRadius: "10px",
                    padding: "16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "1px solid rgba(34, 197, 94, 0.15)", paddingBottom: "8px" }}>
                    <UserCheck size={16} color="#4ade80" />
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "#4ade80" }}>
                      Officer Verification & Correction
                    </span>
                  </div>

                  {/* Field 1: Category */}
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                      Category
                    </label>
                    <select
                      value={editCategory}
                      onChange={(e) => setEditCategory(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#090d16",
                        border: "1px solid rgba(255, 255, 255, 0.12)",
                        borderRadius: "6px",
                        padding: "6px 10px",
                        color: "#ffffff",
                        fontSize: "12px",
                      }}
                    >
                      <option value="water">Water Supply</option>
                      <option value="roads">Roads & Pavements</option>
                      <option value="drainage">Drainage & Stormwater</option>
                      <option value="electricity">Electricity & Lighting</option>
                      <option value="sanitation">Solid Waste & Sanitation</option>
                    </select>
                  </div>

                  {/* Field 2: Priority */}
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                      Priority
                    </label>
                    <select
                      value={editPriority}
                      onChange={(e) => setEditPriority(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#090d16",
                        border: "1px solid rgba(255, 255, 255, 0.12)",
                        borderRadius: "6px",
                        padding: "6px 10px",
                        color: "#ffffff",
                        fontSize: "12px",
                      }}
                    >
                      <option value="critical">CRITICAL (Immediate safety / life hazard)</option>
                      <option value="high">HIGH (Severe disruption)</option>
                      <option value="medium">MEDIUM (Standard civic issue)</option>
                      <option value="low">LOW (Minor aesthetic / maintenance)</option>
                    </select>
                  </div>

                  {/* Field 3: Department */}
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                      Assigned Department
                    </label>
                    <select
                      value={editDepartment}
                      onChange={(e) => setEditDepartment(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#090d16",
                        border: "1px solid rgba(255, 255, 255, 0.12)",
                        borderRadius: "6px",
                        padding: "6px 10px",
                        color: "#ffffff",
                        fontSize: "12px",
                      }}
                    >
                      <option value="Drainage & Stormwater Management">Drainage & Stormwater Management</option>
                      <option value="Roads & Bridges Department">Roads & Bridges Department</option>
                      <option value="Water Supply Department">Water Supply Department</option>
                      <option value="Electricity Distribution Board">Electricity Distribution Board</option>
                      <option value="Solid Waste Management">Solid Waste Management</option>
                    </select>
                  </div>

                  {/* Field 4: Reason */}
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                      Officer Rationale (Logged for Continuous Learning)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Audio indicates flooded sewage near school entrance"
                      value={officerReason}
                      onChange={(e) => setOfficerReason(e.target.value)}
                      style={{
                        width: "100%",
                        backgroundColor: "#090d16",
                        border: "1px solid rgba(255, 255, 255, 0.12)",
                        borderRadius: "6px",
                        padding: "6px 10px",
                        color: "#ffffff",
                        fontSize: "12px",
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  gap: "10px",
                  borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                  paddingTop: "16px",
                }}
              >
                <button
                  disabled={submitting}
                  onClick={() => handleDecision("reject")}
                  style={{
                    padding: "8px 14px",
                    borderRadius: "6px",
                    backgroundColor: "rgba(239, 68, 68, 0.15)",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    color: "#f87171",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Reject / Duplicate
                </button>

                <button
                  disabled={submitting}
                  onClick={() => handleDecision("accept")}
                  style={{
                    padding: "8px 14px",
                    borderRadius: "6px",
                    backgroundColor: "rgba(255, 255, 255, 0.06)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    color: "#f8fafc",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Accept AI Decision
                </button>

                <button
                  disabled={submitting}
                  onClick={() => handleDecision("modify")}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "6px",
                    backgroundColor: "#4f46e5",
                    border: "none",
                    color: "#ffffff",
                    fontSize: "12px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Edit3 size={14} />
                  <span>Submit Officer Correction</span>
                </button>
              </div>
            </div>
          ) : (
            <div
              style={{
                backgroundColor: "#0d1424",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "12px",
                padding: "60px 20px",
                textAlign: "center",
                color: "#64748b",
              }}
            >
              Select a case from the queue to review AI predictions and apply officer overrides.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
