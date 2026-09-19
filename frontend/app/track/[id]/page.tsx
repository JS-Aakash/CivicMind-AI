"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Activity,
  CheckCircle2,
  Clock,
  MapPin,
  Building2,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  ArrowLeft,
  Camera,
  User,
  ThumbsUp,
  ThumbsDown,
  Info,
  Lock,
} from "lucide-react";
import { trackCitizenComplaint, reopenGrievance } from "@/lib/api";
import type { CitizenTrackingResponse } from "@/lib/types";

const STAGES = [
  { key: "SUBMITTED", label: "Submitted" },
  { key: "AI_ANALYSIS", label: "AI Analysis" },
  { key: "TRIAGED", label: "Triaged" },
  { key: "ROUTED", label: "Routed" },
  { key: "ASSIGNED", label: "Assigned" },
  { key: "IN_PROGRESS", label: "In Progress" },
  { key: "FIELD_VERIFICATION", label: "Field Verification" },
  { key: "RESOLVED", label: "Resolved" },
  { key: "CLOSED", label: "Closed" },
];

export default function CitizenTrackingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [data, setData] = useState<CitizenTrackingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reopen state
  const [showReopenModal, setShowReopenModal] = useState(false);
  const [reopenReason, setReopenReason] = useState("");
  const [reopening, setReopening] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  const fetchTracking = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await trackCitizenComplaint(id);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to find grievance with this Complaint ID.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTracking();
  }, [id]);

  const handleSatisfied = () => {
    setFeedbackSuccess("Thank you for confirming the resolution! This case is marked fully redressed.");
  };

  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reopenReason.trim()) return;

    setReopening(true);
    try {
      await reopenGrievance(data?.complaint_code || id, {
        reopen_reason: reopenReason,
        citizen_feedback: "Citizen indicated issue not resolved on ground",
      });
      setShowReopenModal(false);
      setFeedbackSuccess("Grievance has been reopened and forwarded to municipal supervisor review queue.");
      fetchTracking();
    } catch (err: any) {
      alert(err.message || "Failed to reopen grievance");
    } finally {
      setReopening(false);
    }
  };

  // Determine active stage index
  const currentStageKey = data?.lifecycle_stage || (data?.status ? data.status.toUpperCase() : "SUBMITTED");
  let currentStageIndex = STAGES.findIndex((s) => s.key === currentStageKey);
  if (currentStageIndex === -1) {
    if (data?.status === "resolved") currentStageIndex = 7;
    else if (data?.status === "in_progress") currentStageIndex = 5;
    else if (data?.status === "reopened") currentStageIndex = 5;
    else currentStageIndex = 0;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-16">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-8 py-3.5">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Link href="/track" className="flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors no-underline">
            <ArrowLeft size={16} />
            <span>Back to Tracker</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/report"
              className="text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-cyan-500 hover:from-cyan-300 hover:to-cyan-400 px-3.5 py-1.5 rounded-lg shadow-sm transition-all"
            >
              + File Grievance
            </Link>
            <Link
              href="/admin/login"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/80 transition-all"
            >
              <Lock size={12} />
              <span>Officer Login</span>
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 pt-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <div className="w-10 h-10 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-slate-400 text-sm">Retrieving real-time grievance tracking info...</p>
          </div>
        ) : error || !data ? (
          <div className="max-w-xl mx-auto text-center py-16 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle size={24} />
            </div>
            <h2 className="text-lg font-bold text-white mb-2">Complaint Not Found</h2>
            <p className="text-xs text-slate-400 mb-6">{error || "Could not retrieve records for this ID."}</p>
            <Link
              href="/track"
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold rounded-xl transition-all"
            >
              ← Search Another Complaint ID
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Top Status Banner */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-xl">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xl font-bold text-cyan-400">
                      {data.complaint_code}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider ${
                        data.status === "resolved"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : data.status === "reopened"
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : data.status === "in_progress"
                          ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {data.status_display || data.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Registered on: {new Date(data.submitted_at).toLocaleString()}
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs">
                  <div className="bg-slate-950/60 px-3.5 py-2 rounded-xl border border-slate-800 flex items-center gap-2">
                    <Building2 size={15} className="text-cyan-400" />
                    <div>
                      <span className="text-slate-500 block text-[10px]">Department</span>
                      <span className="font-medium text-slate-200">{data.department_name || data.category}</span>
                    </div>
                  </div>

                  <div className="bg-slate-950/60 px-3.5 py-2 rounded-xl border border-slate-800 flex items-center gap-2">
                    <Clock size={15} className="text-indigo-400" />
                    <div>
                      <span className="text-slate-500 block text-[10px]">SLA Target</span>
                      <span className="font-medium text-slate-200">{data.expected_sla_hours} Hours</span>
                    </div>
                  </div>

                  {data.assigned_officer && (
                    <div className="bg-slate-950/60 px-3.5 py-2 rounded-xl border border-slate-800 flex items-center gap-2">
                      <User size={15} className="text-emerald-400" />
                      <div>
                        <span className="text-slate-500 block text-[10px]">Assigned Officer</span>
                        <span className="font-medium text-slate-200">{data.assigned_officer}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* 9-Stage Visual Lifecycle Stepper */}
              <div className="pt-6">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
                  9-Stage Redressal Lifecycle
                </h3>

                <div className="relative">
                  {/* Progress Line */}
                  <div className="hidden sm:block absolute top-4 left-4 right-4 h-0.5 bg-slate-800 -z-0" />
                  <div
                    className="hidden sm:block absolute top-4 left-4 h-0.5 bg-gradient-to-r from-cyan-500 to-blue-500 -z-0 transition-all duration-500"
                    style={{
                      width: `${(Math.min(currentStageIndex, STAGES.length - 1) / (STAGES.length - 1)) * 95}%`,
                    }}
                  />

                  <div className="grid grid-cols-3 sm:grid-cols-9 gap-2 relative z-10">
                    {STAGES.map((stage, idx) => {
                      const isCompleted = idx < currentStageIndex;
                      const isCurrent = idx === currentStageIndex;
                      const isUpcoming = idx > currentStageIndex;

                      return (
                        <div key={stage.key} className="flex flex-col items-center text-center">
                          <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-md ${
                              isCurrent
                                ? "bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/20 font-extrabold"
                                : isCompleted
                                ? "bg-slate-800 text-cyan-400 border border-cyan-500/40"
                                : "bg-slate-900 text-slate-600 border border-slate-800"
                            }`}
                          >
                            {isCompleted ? "✓" : idx + 1}
                          </div>
                          <span
                            className={`text-[11px] mt-2 font-medium line-clamp-2 ${
                              isCurrent
                                ? "text-cyan-300 font-semibold"
                                : isCompleted
                                ? "text-slate-300"
                                : "text-slate-600"
                            }`}
                          >
                            {stage.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Resolution Verification & Evidence Section */}
            {data.status === "resolved" && data.resolution_info && (
              <div className="bg-emerald-950/20 border border-emerald-500/40 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm mb-3">
                  <CheckCircle2 size={18} />
                  <span>Official Resolution Proof & Officer Sign-Off</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="text-slate-400 block text-[11px]">Resolution Summary:</span>
                      <p className="text-slate-200 mt-1 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                        {data.resolution_info.resolution_note || "Issue rectified by field engineering team."}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-4 pt-1">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Verified By</span>
                        <span className="text-slate-300 font-medium">
                          {data.resolution_info.resolved_by || "Municipal Field Officer"}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">Resolved At</span>
                        <span className="text-slate-300 font-medium">
                          {data.resolved_at ? new Date(data.resolved_at).toLocaleString() : "Recently"}
                        </span>
                      </div>
                      {data.resolution_info.geofence_verified && (
                        <div className="flex items-center gap-1 text-cyan-400 text-[11px] bg-cyan-500/10 px-2 py-1 rounded border border-cyan-500/20">
                          <MapPin size={12} />
                          <span>GPS Geofence Verified ({Math.round(data.resolution_info.resolver_distance_meters || 0)}m from site)</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {data.resolution_info.proof_image_url && (
                    <div>
                      <span className="text-slate-400 block text-[11px] mb-2">Field Completion Photo:</span>
                      <div className="rounded-xl overflow-hidden border border-slate-700 max-h-48 bg-slate-900 flex items-center justify-center">
                        <img
                          src={data.resolution_info.proof_image_url}
                          alt="Resolution Proof"
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Citizen Feedback / Reopen Prompt */}
                <div className="mt-6 pt-5 border-t border-emerald-500/20">
                  {feedbackSuccess ? (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
                      <CheckCircle2 size={16} />
                      <span>{feedbackSuccess}</span>
                    </div>
                  ) : (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-950/70 p-4 rounded-xl border border-slate-800">
                      <div>
                        <h4 className="text-xs font-semibold text-slate-200">
                          Was this issue actually resolved on the ground?
                        </h4>
                        <p className="text-[11px] text-slate-400">
                          Your feedback ensures municipal accountability. If unresolved, you can reopen immediately.
                        </p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={handleSatisfied}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition-all cursor-pointer"
                        >
                          <ThumbsUp size={13} />
                          <span>Yes, Resolved</span>
                        </button>
                        <button
                          onClick={() => setShowReopenModal(true)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-semibold transition-all cursor-pointer"
                        >
                          <ThumbsDown size={13} />
                          <span>No, Reopen</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Reopened Alert */}
            {data.status === "reopened" && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-5 text-xs text-rose-300 flex items-start gap-3">
                <RotateCcw size={18} className="shrink-0 text-rose-400 mt-0.5" />
                <div>
                  <h4 className="font-bold text-rose-200 text-sm">Grievance Reopened by Citizen</h4>
                  <p className="mt-1 text-slate-300">
                    Reason: {data.reopen_reason || "Citizen indicated the issue persists on the ground."}
                  </p>
                  <p className="text-slate-400 text-[11px] mt-1">
                    Status: Escalated to Municipal Supervisor for priority reassessment.
                  </p>
                </div>
              </div>
            )}

            {/* AI Summary & Multilingual Citizen Responses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* AI Summary */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs">
                  <Sparkles size={15} />
                  <span>AI Multimodal Triage Summary</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
                  {data.ai_summary || "Grievance triaged and classified with confidence by CivicMind AI."}
                </p>
              </div>

              {/* Multilingual Updates */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs">
                  <Info size={15} />
                  <span>Multilingual Citizen Notice</span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60">
                    <span className="text-[10px] text-slate-500 font-semibold uppercase block">English</span>
                    <p className="text-slate-300 text-[11px] mt-0.5">{data.citizen_response_message?.en}</p>
                  </div>
                  {data.citizen_response_message?.ta && (
                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60">
                      <span className="text-[10px] text-cyan-500 font-semibold uppercase block">தமிழ்</span>
                      <p className="text-slate-300 text-[11px] mt-0.5">{data.citizen_response_message.ta}</p>
                    </div>
                  )}
                  {data.citizen_response_message?.hi && (
                    <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60">
                      <span className="text-[10px] text-amber-500 font-semibold uppercase block">हिंदी</span>
                      <p className="text-slate-300 text-[11px] mt-0.5">{data.citizen_response_message.hi}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Timeline Events */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
                Redressal Audit Timeline
              </h3>

              <div className="space-y-4">
                {data.timeline?.map((evt, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 mt-1.5 shrink-0 shadow-sm shadow-cyan-400/50" />
                    <div className="flex-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{evt.title}</span>
                        <span className="text-[11px] text-slate-500">
                          {new Date(evt.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] mt-0.5">{evt.description}</p>
                      {evt.actor && (
                        <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                          Actor: {evt.actor}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reopen Modal */}
      {showReopenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-1">Reopen Grievance</h3>
            <p className="text-xs text-slate-400 mb-4">
              Please let our municipal supervisors know why this issue is not satisfactorily resolved.
            </p>

            <form onSubmit={handleReopenSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Reason for Reopening:
                </label>
                <textarea
                  required
                  rows={3}
                  value={reopenReason}
                  onChange={(e) => setReopenReason(e.target.value)}
                  placeholder="e.g. The pothole was only filled with loose sand and collapsed again after rain..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReopenModal(false)}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={reopening}
                  className="px-4 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs shadow-md transition-all disabled:opacity-50"
                >
                  {reopening ? "Submitting Reopen..." : "Confirm & Reopen"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
