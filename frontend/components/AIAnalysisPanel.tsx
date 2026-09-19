"use client";

import React, { useState } from "react";
import {
  Brain,
  CheckCircle,
  HelpCircle,
  Zap,
  Building2,
  ChevronDown,
  ChevronUp,
  BarChart2,
  ShieldAlert,
  Clock,
  Send,
  AlertTriangle,
  UserCheck,
  Flame,
  Info,
  Layers,
} from "lucide-react";
import { PriorityBadge } from "./PriorityBadge";
import { LanguageBadge } from "./LanguageBadge";
import type { AIAnalysisResult, Priority, RoutingDecision } from "@/lib/types";
import { confidencePercent } from "@/lib/utils";
import { CATEGORIES } from "@/lib/constants";

interface AIAnalysisPanelProps {
  analysis?: AIAnalysisResult;
  isLoading?: boolean;
  isMock?: boolean;
  onOverrideClick?: () => void;
}

export function AIAnalysisPanel({
  analysis,
  isLoading,
  isMock = false,
  onOverrideClick,
}: AIAnalysisPanelProps) {
  const [showEvidence, setShowEvidence] = useState(true);
  const [showHybridModal, setShowHybridModal] = useState(false);

  if (isLoading) {
    return (
      <div className="ai-panel">
        <div className="ai-panel-header">
          <Brain size={16} color="var(--accent-indigo)" />
          <span style={{ fontWeight: 600, fontSize: 13 }}>AI Analysis & Smart Routing</span>
        </div>
        <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="skeleton" style={{ height: 42, borderRadius: 8 }} />
          ))}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="ai-panel">
        <div className="ai-panel-header">
          <Brain size={16} color="var(--accent-indigo)" />
          <span style={{ fontWeight: 600, fontSize: 13 }}>AI Smart Routing Engine</span>
        </div>
        <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
          Submit a complaint or run grievance analysis to trigger the civic decision pipeline
        </div>
      </div>
    );
  }

  const isRealModel = !analysis.is_mock;
  const catConfig = CATEGORIES[analysis.category as keyof typeof CATEGORIES] || CATEGORIES.general;
  const catProbs = analysis.category_probabilities || {
    [analysis.category]: analysis.confidence || 0.92,
  };

  const decisionDetails = analysis.decision_details;
  const routing = decisionDetails?.routing;
  const sla = decisionDetails?.sla || analysis.sla;
  const review = decisionDetails?.review;
  const explanation = decisionDetails?.explanation;
  const priorityInfo = decisionDetails?.priority;
  const context = decisionDetails?.context;

  // Routing Decision Colors & Badge Info
  const routingDecision = analysis.routing_decision || review?.decision || "AUTO_ROUTE";
  const getDecisionBadge = (dec: RoutingDecision | string) => {
    switch (dec) {
      case "AUTO_ROUTE":
        return {
          label: "AUTO ROUTED",
          color: "#22c55e",
          bg: "rgba(34, 197, 94, 0.12)",
          border: "rgba(34, 197, 94, 0.3)",
          icon: Zap,
        };
      case "OFFICER_REVIEW":
        return {
          label: "OFFICER REVIEW",
          color: "#f59e0b",
          bg: "rgba(245, 158, 11, 0.12)",
          border: "rgba(245, 158, 11, 0.3)",
          icon: UserCheck,
        };
      case "MANUAL_REVIEW":
        return {
          label: "MANUAL REVIEW",
          color: "#ef4444",
          bg: "rgba(239, 68, 68, 0.12)",
          border: "rgba(239, 68, 68, 0.3)",
          icon: ShieldAlert,
        };
      default:
        return {
          label: dec,
          color: "#6366f1",
          bg: "rgba(99, 102, 241, 0.12)",
          border: "rgba(99, 102, 241, 0.3)",
          icon: Info,
        };
    }
  };

  const decBadge = getDecisionBadge(routingDecision);
  const DecIcon = decBadge.icon;

  // SLA Status formatting
  const getSLAStatusBadge = (status?: string) => {
    switch (status) {
      case "within_sla":
        return { label: "WITHIN SLA", color: "#22c55e", bg: "rgba(34,197,94,0.12)" };
      case "approaching_breach":
        return { label: "SLA AT RISK", color: "#f59e0b", bg: "rgba(245,158,11,0.12)" };
      case "breached":
        return { label: "SLA BREACHED", color: "#ef4444", bg: "rgba(239,68,68,0.12)" };
      case "escalated":
        return { label: "ESCALATED", color: "#a855f7", bg: "rgba(168,85,247,0.12)" };
      default:
        return { label: "ACTIVE SLA", color: "#38bdf8", bg: "rgba(56,189,248,0.12)" };
    }
  };

  const slaBadge = getSLAStatusBadge(sla?.status);

  return (
    <div className="ai-panel" style={{ maxHeight: "calc(100vh - 120px)", overflowY: "auto", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <div className="ai-panel-header" style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Brain size={16} color="var(--accent-indigo)" />
          <span style={{ fontWeight: 600, fontSize: 13 }}>Civic Decision Engine</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            className={isRealModel ? "badge badge-resolved" : "badge badge-demo"}
            style={{ fontSize: 10, letterSpacing: "0.05em" }}
          >
            {isRealModel ? "MuRIL v1.1" : "DEMO PIPELINE"}
          </span>
        </div>
      </div>

      {/* PROMINENT MODULE 3 AI ROUTING DECISION CARD */}
      <div
        style={{
          margin: "12px 14px 6px",
          padding: 14,
          background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)",
          borderRadius: 10,
          border: `1px solid ${decBadge.border}`,
          boxShadow: "0 4px 14px rgba(0, 0, 0, 0.25)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
              Routing Decision
            </span>
          </div>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              padding: "3px 9px",
              borderRadius: 6,
              fontSize: 11,
              fontWeight: 700,
              color: decBadge.color,
              background: decBadge.bg,
              border: `1px solid ${decBadge.border}`,
            }}
          >
            <DecIcon size={12} />
            {decBadge.label}
          </span>
        </div>

        {/* Primary Department & Confidence */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 10, marginBottom: 10 }}>
          <div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 2 }}>PRIMARY DEPARTMENT</div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
              <Building2 size={14} color="var(--accent-cyan)" />
              {routing?.primary_department?.name || analysis.department_name}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 2 }}>ROUTING CONFIDENCE</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#22d3ee" }}>
              {Math.round((routing?.primary_department?.confidence ?? analysis.confidence ?? 0.85) * 100)}%
            </div>
          </div>
        </div>

        {/* Secondary Departments if multi-issue */}
        {routing?.secondary_departments && routing.secondary_departments.length > 0 && (
          <div style={{ marginBottom: 10, paddingTop: 8, borderTop: "1px dashed rgba(255,255,255,0.08)" }}>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>SECONDARY DEPARTMENTS (MULTI-ISSUE)</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {routing.secondary_departments.map((sec) => (
                <span
                  key={sec.id}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                    padding: "3px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                    background: "rgba(34, 211, 238, 0.08)",
                    color: "#38bdf8",
                    border: "1px solid rgba(56, 189, 248, 0.2)",
                  }}
                >
                  <Layers size={10} />
                  {sec.name} ({Math.round(sec.confidence * 100)}%)
                </span>
              ))}
            </div>
          </div>
        )}

        {/* SLA Bar */}
        {sla && (
          <div
            style={{
              paddingTop: 8,
              borderTop: "1px solid rgba(255,255,255,0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              fontSize: 11,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)" }}>
              <Clock size={12} color="#f59e0b" />
              <span>
                Target SLA: <strong>{sla.response_window_hours || Math.round((sla.response_minutes ?? 720) / 60)}h</strong>
              </span>
            </div>
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                padding: "2px 7px",
                borderRadius: 4,
                color: slaBadge.color,
                background: slaBadge.bg,
              }}
            >
              {slaBadge.label}
            </span>
          </div>
        )}
      </div>

      {/* Main Analysis Details */}
      <div style={{ padding: "8px 16px 14px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        {/* Language Intelligence */}
        <div className="ai-field">
          <div className="ai-field-label">Language Intelligence</div>
          <div className="ai-field-value">
            <LanguageBadge
              language={analysis.primary_language}
              languageName={analysis.language_name}
              script={analysis.script}
              isCodeMixed={analysis.is_code_mixed}
              detectedLanguages={analysis.languages}
            />
          </div>
        </div>

        {/* Grievance Verification */}
        <div className="ai-field">
          <div className="ai-field-label">Grievance Status</div>
          <div className="ai-field-value" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {analysis.is_grievance ? (
              <span style={{ color: "#22c55e", fontWeight: 600, fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
                <CheckCircle size={14} /> Genuine Complaint
              </span>
            ) : (
              <span style={{ color: "#38bdf8", fontWeight: 600, fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
                <HelpCircle size={14} /> Inquiry / Non-Grievance
              </span>
            )}
          </div>
        </div>

        {/* Category & Subcategory */}
        <div className="ai-field">
          <div className="ai-field-label">Category & Subcategory</div>
          <div className="ai-field-value">
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                padding: "3px 8px",
                borderRadius: 6,
                fontSize: 11,
                fontWeight: 600,
                background: `${catConfig.color}18`,
                color: catConfig.color,
              }}
            >
              {catConfig.label}
              {analysis.subcategory && (
                <span style={{ opacity: 0.75, fontWeight: 400 }}>/ {analysis.subcategory.replace(/_/g, " ")}</span>
              )}
            </span>
          </div>
        </div>

        {/* Priority & Severity */}
        <div className="ai-field">
          <div className="ai-field-label">Priority & Severity</div>
          <div className="ai-field-value" style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <PriorityBadge priority={analysis.priority} />
            <span
              style={{
                fontSize: 10,
                padding: "2px 6px",
                borderRadius: 4,
                background: "rgba(255,255,255,0.06)",
                color: "var(--text-muted)",
                textTransform: "uppercase",
              }}
            >
              {analysis.severity} sev
            </span>
          </div>
        </div>
      </div>

      {/* HYBRID PRIORITY VISUALIZATION (Section 26) */}
      {priorityInfo && (
        <div style={{ margin: "0 14px 12px", padding: 10, background: "rgba(15, 23, 42, 0.6)", borderRadius: 8, border: "1px solid var(--brand-border)" }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
            <Zap size={11} color="var(--accent-indigo)" />
            Hybrid Priority Synthesis
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, textAlign: "center" }}>
            <div style={{ padding: "6px 4px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
              <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase" }}>Neural Signal</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", marginTop: 2, textTransform: "uppercase" }}>
                {priorityInfo.neural_prediction}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                {Math.round(priorityInfo.neural_probability * 100)}%
              </div>
            </div>

            <div style={{ padding: "6px 4px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
              <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase" }}>Context / Hazard</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: context?.safety_risk ? "#ef4444" : "#38bdf8", marginTop: 2, textTransform: "uppercase" }}>
                {context?.safety_risk ? "CRITICAL RISK" : `${priorityInfo.reasoning_mode}`}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                Score: {priorityInfo.priority_score.toFixed(2)}
              </div>
            </div>

            <div style={{ padding: "6px 4px", background: "rgba(99,102,241,0.1)", borderRadius: 6, border: "1px solid rgba(99,102,241,0.3)" }}>
              <div style={{ fontSize: 9, color: "var(--accent-cyan)", textTransform: "uppercase", fontWeight: 700 }}>Final Urgency</div>
              <div style={{ fontSize: 12, fontWeight: 800, color: "#fff", marginTop: 2, textTransform: "uppercase" }}>
                {priorityInfo.final_priority}
              </div>
              <div style={{ fontSize: 9, color: "var(--accent-indigo)" }}>OPERATIONAL</div>
            </div>
          </div>
        </div>
      )}

      {/* MULTIMODAL INTELLIGENCE & CONFLICT CARD (Module 5) */}
      <div style={{ margin: "0 14px 12px", padding: 10, background: "rgba(15, 23, 42, 0.6)", borderRadius: 8, border: "1px solid var(--brand-border)" }}>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
          <Layers size={11} color="var(--accent-indigo)" />
          Multimodal Evidence Consistency
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <div style={{ padding: "6px 8px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
            <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase" }}>Text Authority</div>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-primary)", marginTop: 2 }}>
              MuRIL v1.1 ({analysis.category.toUpperCase()})
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
              {Math.round((analysis.confidence || 0.9) * 100)}% text conf
            </div>
          </div>
          <div style={{ padding: "6px 8px", background: "rgba(255,255,255,0.03)", borderRadius: 6 }}>
            <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase" }}>Visual Model</div>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#38bdf8", marginTop: 2 }}>
              Qwen3-VL 4B (Local)
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
              Grounded Hazard Evidence
            </div>
          </div>
        </div>
      </div>

      {/* WHY THIS DECISION? — STRUCTURED EXPLANATION FACTORS (Section 16 & 25) */}
      <div style={{ padding: "0 14px 12px" }}>
        <div
          style={{
            background: "rgba(0, 0, 0, 0.25)",
            borderRadius: 8,
            padding: 12,
            border: "1px solid var(--brand-border)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 5 }}>
              <Info size={13} color="var(--accent-cyan)" />
              Why this decision? (Structured Civic Signals)
            </span>
          </div>

          <p style={{ fontSize: 12, color: "var(--text-primary)", lineHeight: 1.5, marginBottom: 10 }}>
            {explanation?.summary || analysis.explanation || analysis.routing_reason}
          </p>

          {/* Structured Factor Chips */}
          {explanation?.factors && explanation.factors.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              {explanation.factors.map((fact, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "4px 8px",
                    background: "rgba(255,255,255,0.03)",
                    borderRadius: 4,
                    fontSize: 11,
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)" }}>
                    <span style={{ color: "#22c55e", fontWeight: 700 }}>✓</span>
                    <strong style={{ color: "var(--text-primary)", textTransform: "capitalize" }}>
                      {fact.factor.replace(/_/g, " ")}:
                    </strong>{" "}
                    {fact.value}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      color: fact.impact.includes("Safety") || fact.impact.includes("elevates") ? "#ef4444" : "var(--accent-cyan)",
                      fontWeight: 500,
                    }}
                  >
                    {fact.impact}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {context?.duration_hours ? (
                <span className="badge badge-demo" style={{ fontSize: 10 }}>
                  ✓ Duration: {context.duration_hours}h
                </span>
              ) : null}
              {context?.affected_population ? (
                <span className="badge badge-demo" style={{ fontSize: 10 }}>
                  ✓ Scope: {context.affected_population.replace(/_/g, " ")}
                </span>
              ) : null}
              {context?.safety_risk ? (
                <span className="badge" style={{ fontSize: 10, background: "rgba(239,68,68,0.2)", color: "#ef4444" }}>
                  ✓ Acute Safety Hazard
                </span>
              ) : null}
            </div>
          )}

          {/* Audit & Policy Versions footer */}
          <div
            style={{
              marginTop: 10,
              paddingTop: 8,
              borderTop: "1px solid rgba(255,255,255,0.06)",
              fontSize: 10,
              color: "var(--text-muted)",
              display: "flex",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 6,
            }}
          >
            <span>Model: {analysis.model_version || "muril-v1.1"}</span>
            <span>Policy: priority-v1 • routing-v1 • sla-v1</span>
          </div>
        </div>
      </div>

      {/* Category Probability Distribution */}
      {catProbs && Object.keys(catProbs).length > 0 && (
        <div style={{ padding: "0 16px 14px" }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 8, display: "flex", alignItems: "center", gap: 5 }}>
            <BarChart2 size={11} color="var(--accent-indigo)" />
            Category Probability Distribution
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {Object.entries(catProbs).map(([catName, prob]) => {
              const cfg = CATEGORIES[catName as keyof typeof CATEGORIES] || { color: "#6366f1", label: catName };
              const pct = Math.round(prob * 100);
              return (
                <div key={catName} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}>
                  <span style={{ width: 85, color: "var(--text-secondary)", textTransform: "capitalize", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {cfg.label}
                  </span>
                  <div style={{ flex: 1, height: 6, background: "rgba(255,255,255,0.06)", borderRadius: 3, overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${pct}%`,
                        height: "100%",
                        background: cfg.color || "var(--accent-indigo)",
                        borderRadius: 3,
                        transition: "width 0.4s ease",
                      }}
                    />
                  </div>
                  <span style={{ width: 38, textAlign: "right", fontFamily: "monospace", color: "var(--text-muted)", fontSize: 10 }}>
                    {pct}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
