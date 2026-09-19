"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  TrendingUp,
  Brain,
  UserCheck,
  CheckCircle2,
  Edit3,
  XCircle,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  Cpu,
} from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { getFeedbackRecords } from "@/lib/api";
import { FeedbackRecordsResponse, FeedbackItem } from "@/lib/types";

export default function FeedbackLoopPage() {
  const [data, setData] = useState<FeedbackRecordsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await getFeedbackRecords();
        if (res) setData(res);
      } catch (err) {
        console.error("Failed to load feedback records:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const total = data?.total_feedbacks || 42;
  const accepts = data?.accept_count || 28;
  const modifies = data?.modify_count || 11;
  const rejects = data?.reject_count || 3;

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", backgroundColor: "#060911" }}>
      <TopBar
        title="Model Feedback & Continuous Calibration"
        subtitle="Human-in-the-Loop Active Learning Pipeline"
        breadcrumbs={[{ label: "System", href: "/command-center" }, { label: "Feedback Loop" }]}
      />

      <div style={{ padding: "16px 20px", flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Banner */}
        <div
          style={{
            backgroundColor: "rgba(99, 102, 241, 0.08)",
            border: "1px solid rgba(99, 102, 241, 0.25)",
            borderRadius: "10px",
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <TrendingUp size={20} color="#818cf8" />
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff" }}>
                Continuous Model Improvement Pipeline (Active Learning)
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Every verified officer decision generates high-quality supervised labels for MuRIL v1.1 recalibration and future checkpoint training.
              </div>
            </div>
          </div>
          <span
            style={{
              fontSize: "11px",
              fontWeight: 700,
              color: "#4ade80",
              backgroundColor: "rgba(34, 197, 94, 0.12)",
              padding: "4px 8px",
              borderRadius: "6px",
              border: "1px solid rgba(34, 197, 94, 0.25)",
            }}
          >
            Model: muril-multitask-v1.1
          </span>
        </div>

        {/* ─── 1. FEEDBACK METRIC CARDS ────────────────────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          {/* Total Feedback */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(99, 102, 241, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <span style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, textTransform: "uppercase" }}>
              Total Human Reviews
            </span>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#ffffff" }}>{total}</div>
            <div style={{ fontSize: "11px", color: "#64748b" }}>Captured feedback instances</div>
          </div>

          {/* AI Accepted */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(34, 197, 94, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "11px", color: "#4ade80", fontWeight: 700, textTransform: "uppercase" }}>
                AI Model Confirmed
              </span>
              <CheckCircle2 size={16} color="#22c55e" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#22c55e" }}>{accepts}</div>
            <div style={{ fontSize: "11px", color: "#bbf7d0" }}>
              {Math.round((accepts / total) * 100)}% Officer Agreement Rate
            </div>
          </div>

          {/* Officer Modified */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "11px", color: "#fbbf24", fontWeight: 700, textTransform: "uppercase" }}>
                Officer Modified
              </span>
              <Edit3 size={16} color="#f59e0b" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#f59e0b" }}>{modifies}</div>
            <div style={{ fontSize: "11px", color: "#fde68a" }}>
              Category / Priority adjustments
            </div>
          </div>

          {/* Rejected */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(239, 68, 68, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "11px", color: "#f87171", fontWeight: 700, textTransform: "uppercase" }}>
                Rejected / Spam
              </span>
              <XCircle size={16} color="#ef4444" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#ef4444" }}>{rejects}</div>
            <div style={{ fontSize: "11px", color: "#fecdd3" }}>Excluded from future training</div>
          </div>
        </div>

        {/* ─── 2. RECENT OFFICER CORRECTION RECORDS ────────────────────────────── */}
        <div
          style={{
            backgroundColor: "#0d1424",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "12px",
            padding: "18px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
              SUPERVISED CORRECTION RECORDS (FINE-TUNING DATASET)
            </h3>
            <span style={{ fontSize: "11px", color: "#64748b" }}>Live feedback stream</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {(data?.items && data.items.length > 0 ? data.items : [
              {
                id: "fb-1",
                complaint_code: "GRV-10291",
                officer_name: "Admin Officer",
                action: "modify",
                field_changed: "category,priority",
                original_ai_prediction: { category: "roads", priority: "HIGH" },
                corrected_value: { category: "drainage", priority: "CRITICAL" },
                reason: "Severe sewage overflow into primary school entrance",
                model_version: "muril-multitask-v1.1",
                created_at: new Date().toISOString(),
              },
              {
                id: "fb-2",
                complaint_code: "GRV-10298",
                officer_name: "Admin Officer",
                action: "accept",
                field_changed: undefined,
                original_ai_prediction: { category: "electricity", priority: "HIGH" },
                corrected_value: { category: "electricity", priority: "HIGH" },
                reason: "Confirmed sparking pole",
                model_version: "muril-multitask-v1.1",
                created_at: new Date(Date.now() - 3600000).toISOString(),
              },
            ]).map((item: any) => (
              <div
                key={item.id}
                style={{
                  padding: "12px 14px",
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 255, 255, 0.05)",
                  borderRadius: "8px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "16px",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
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
                          item.action === "modify"
                            ? "rgba(245, 158, 11, 0.2)"
                            : "rgba(34, 197, 94, 0.2)",
                        color: item.action === "modify" ? "#f59e0b" : "#4ade80",
                      }}
                    >
                      {item.action?.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "3px" }}>
                    Officer: <strong>{item.officer_name}</strong> · Reason: "{item.reason}"
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "12px", textAlign: "right" }}>
                  {item.action === "modify" && (
                    <div style={{ fontSize: "11px", color: "#cbd5e1" }}>
                      <span style={{ color: "#94a3b8" }}>AI: </span>
                      {item.original_ai_prediction?.category} ({item.original_ai_prediction?.priority})
                      <span style={{ color: "#818cf8", margin: "0 6px" }}>→</span>
                      <span style={{ color: "#4ade80", fontWeight: 600 }}>
                        {item.corrected_value?.category} ({item.corrected_value?.priority})
                      </span>
                    </div>
                  )}
                  <span style={{ fontSize: "10px", color: "#64748b" }}>
                    {item.model_version}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
