"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { trackCitizenComplaint } from "@/lib/api";
import type { CitizenTrackingResponse } from "@/lib/types";
import {
  ArrowLeft,
  Clock,
  CheckCircle,
  Building,
  ShieldAlert,
  Globe,
  Camera,
  Mic,
  MapPin,
  FileText,
  AlertTriangle,
  Play,
  Share2,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

export default function CitizenComplaintDetailPage() {
  const params = useParams();
  const complaintCode = params.id as string;

  const [data, setData] = useState<CitizenTrackingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedLang, setSelectedLang] = useState<"en" | "ta" | "hi">("en");

  useEffect(() => {
    if (!complaintCode) return;
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const resp = await trackCitizenComplaint(complaintCode);
        setData(resp);
      } catch (err) {
        console.warn("Error tracking complaint:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [complaintCode]);

  if (loading) {
    return (
      <div style={{ maxWidth: 800, margin: "0 auto", padding: 32 }}>
        <div className="skeleton" style={{ height: 200, borderRadius: 12, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 300, borderRadius: 12 }} />
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ maxWidth: 600, margin: "60px auto", textAlign: "center", padding: 32 }}>
        <ShieldAlert size={48} color="#ef4444" style={{ margin: "0 auto 16px" }} />
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Grievance Not Found</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 14, marginBottom: 20 }}>
          Could not locate tracking record for <code>{complaintCode}</code>.
        </p>
        <Link href="/my-complaints" className="btn btn-secondary">
          ← Back to Tracking Portal
        </Link>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 880, margin: "0 auto", padding: "28px 20px" }}>
      {/* Back button */}
      <div style={{ marginBottom: 16 }}>
        <Link href="/my-complaints" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 13, display: "flex", alignItems: "center", gap: 6 }}>
          <ArrowLeft size={14} /> Back to My Grievances
        </Link>
      </div>

      {/* Main Status Header Card */}
      <div
        style={{
          background: "var(--brand-card)",
          border: "1px solid var(--brand-border)",
          borderRadius: 14,
          padding: 24,
          marginBottom: 20,
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12, flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
              <span style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: "var(--accent-indigo)" }}>
                {data.complaint_code}
              </span>
              <span className={`badge badge-${data.priority}`}>{data.priority.toUpperCase()} PRIORITY</span>
              <span style={{ fontSize: 12, background: "rgba(255,255,255,0.06)", padding: "3px 8px", borderRadius: 4, color: "var(--text-secondary)" }}>
                {data.category_display}
              </span>
            </div>
            <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Submitted {formatRelativeTime(data.submitted_at)} · Target Resolution: {data.expected_sla_hours} hours
            </p>
          </div>

          <span
            style={{
              fontSize: 12,
              fontWeight: 800,
              padding: "6px 14px",
              borderRadius: 20,
              background: data.status === "resolved" ? "rgba(34,197,94,0.2)" : "rgba(249,115,22,0.2)",
              color: data.status === "resolved" ? "#22c55e" : "#fb923c",
              border: `1px solid ${data.status === "resolved" ? "#22c55e" : "#f97316"}44`,
            }}
          >
            ● {data.status_display.toUpperCase()}
          </span>
        </div>

        {/* Multilingual Official Citizen Notice */}
        <div
          style={{
            background: "var(--brand-surface)",
            borderRadius: 10,
            padding: 16,
            border: "1px solid var(--brand-border)",
            marginTop: 16,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <Globe size={14} color="var(--accent-cyan)" />
              <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
                Official Municipal Notice
              </span>
            </div>
            <div style={{ display: "flex", gap: 4 }}>
              {(["en", "ta", "hi"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setSelectedLang(lang)}
                  style={{
                    padding: "2px 8px",
                    fontSize: 11,
                    borderRadius: 4,
                    border: "1px solid var(--brand-border)",
                    background: selectedLang === lang ? "var(--accent-indigo)" : "transparent",
                    color: selectedLang === lang ? "#fff" : "var(--text-secondary)",
                    cursor: "pointer",
                  }}
                >
                  {lang === "en" ? "English" : lang === "ta" ? "தமிழ்" : "हिंदी"}
                </button>
              ))}
            </div>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-primary)", lineHeight: 1.6, margin: 0 }}>
            {data.citizen_response_message[selectedLang] || data.citizen_response_message.en}
          </p>
        </div>
      </div>

      {/* Grid: Timeline & Department Info */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20, alignItems: "flex-start" }}>
        {/* Left: Resolution Timeline */}
        <div
          style={{
            background: "var(--brand-card)",
            border: "1px solid var(--brand-border)",
            borderRadius: 14,
            padding: 20,
          }}
        >
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <Clock size={16} color="var(--accent-indigo)" />
            <span>Resolution Timeline & Audit Trail</span>
          </h3>

          <div style={{ position: "relative", paddingLeft: 24 }}>
            {/* Timeline vertical bar */}
            <div
              style={{
                position: "absolute",
                left: 7,
                top: 8,
                bottom: 8,
                width: 2,
                background: "rgba(255,255,255,0.1)",
              }}
            />

            {data.timeline.map((evt, idx) => (
              <div key={idx} style={{ position: "relative", marginBottom: 20 }}>
                {/* Timeline dot */}
                <div
                  style={{
                    position: "absolute",
                    left: -24,
                    top: 2,
                    width: 16,
                    height: 16,
                    borderRadius: "50%",
                    background: evt.status === "completed" ? "#22c55e" : evt.status === "current" ? "#f97316" : "#334155",
                    border: "3px solid #0f172a",
                    boxShadow: evt.status === "current" ? "0 0 10px #f97316" : "none",
                  }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 2 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: evt.status === "upcoming" ? "var(--text-muted)" : "var(--text-primary)" }}>
                    {evt.title}
                  </span>
                  <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                    {evt.actor}
                  </span>
                </div>
                <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: 0, lineHeight: 1.4 }}>
                  {evt.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Department & Evidence Box */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Department SLA Box */}
          <div
            style={{
              background: "var(--brand-card)",
              border: "1px solid var(--brand-border)",
              borderRadius: 14,
              padding: 18,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <Building size={16} color="var(--accent-indigo)" />
              <h4 style={{ fontSize: 13, fontWeight: 700, margin: 0 }}>Assigned Authority</h4>
            </div>
            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 6 }}>
              {data.department_name}
            </p>
            <div style={{ fontSize: 12, color: "var(--text-muted)", display: "flex", justifyContent: "space-between", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 8 }}>
              <span>Committed SLA:</span>
              <strong style={{ color: "var(--accent-cyan)" }}>{data.expected_sla_hours} Hours</strong>
            </div>
            {data.incident_title && (
              <div style={{ marginTop: 10, padding: 8, background: "rgba(239,68,68,0.1)", borderRadius: 6, border: "1px solid rgba(239,68,68,0.2)" }}>
                <span style={{ fontSize: 11, color: "#f87171", fontWeight: 700 }}>Part of Civic Incident:</span>
                <div style={{ fontSize: 12, color: "var(--text-primary)", fontWeight: 600, marginTop: 2 }}>
                  🚨 {data.incident_title}
                </div>
              </div>
            )}
          </div>

          {/* Media Evidence preview */}
          {data.media && data.media.length > 0 && (
            <div
              style={{
                background: "var(--brand-card)",
                border: "1px solid var(--brand-border)",
                borderRadius: 14,
                padding: 18,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Camera size={16} color="var(--accent-cyan)" />
                <h4 style={{ fontSize: 13, fontWeight: 700, margin: 0 }}>Attached Evidence</h4>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
                {data.media.map((m, idx) => (
                  <div key={idx} style={{ borderRadius: 8, overflow: "hidden", border: "1px solid var(--brand-border)" }}>
                    <img src={m.media_url || m.thumbnail_url} alt="Evidence" style={{ width: "100%", height: 90, objectFit: "cover" }} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <Link
            href="/map"
            className="btn btn-secondary"
            style={{ textDecoration: "none", textAlign: "center", fontSize: 12, padding: "10px" }}
          >
            🗺️ View on Urban Civic Map
          </Link>
        </div>
      </div>
    </div>
  );
}
