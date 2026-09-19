import React from "react";
import Link from "next/link";
import { MapPin, Clock, Zap } from "lucide-react";
import { PriorityBadge } from "./PriorityBadge";
import { LanguageBadge } from "./LanguageBadge";
import type { Complaint } from "@/lib/types";
import { formatRelativeTime, truncateText, confidencePercent } from "@/lib/utils";
import { CATEGORIES, STATUSES } from "@/lib/constants";

interface ComplaintCardProps {
  complaint: Complaint;
  compact?: boolean;
}

export function ComplaintCard({ complaint, compact = false }: ComplaintCardProps) {
  const catConfig = CATEGORIES[complaint.category as keyof typeof CATEGORIES] || CATEGORIES.general;
  const statusConfig = STATUSES[complaint.status as keyof typeof STATUSES];

  return (
    <Link
      href={`/complaints/${complaint.complaint_code}`}
      style={{ textDecoration: "none", display: "block" }}
    >
      <div className="complaint-card">
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <span
              style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12, color: "var(--accent-indigo)", fontWeight: 600 }}
            >
              {complaint.complaint_code}
            </span>
            <PriorityBadge priority={complaint.priority} size="sm" />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                padding: "3px 8px",
                borderRadius: 6,
                fontSize: 11,
                background: "rgba(148, 163, 184, 0.1)",
                color: statusConfig?.color || "var(--text-muted)",
              }}
            >
              {statusConfig?.label || complaint.status}
            </span>
          </div>
        </div>

        {/* Complaint text */}
        <p
          style={{
            fontSize: 13,
            color: "var(--text-secondary)",
            lineHeight: 1.5,
            marginBottom: 10,
            fontStyle: complaint.is_code_mixed ? "normal" : "normal",
          }}
        >
          "{truncateText(complaint.text, compact ? 80 : 120)}"
        </p>

        {/* Tags row */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
          <LanguageBadge
            language={complaint.language}
            script={complaint.script}
            isCodeMixed={complaint.is_code_mixed}
            detectedLanguages={complaint.detected_languages}
          />
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
          </span>
          {complaint.confidence !== undefined && (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                padding: "3px 8px",
                borderRadius: 6,
                fontSize: 11,
                background: "rgba(99, 102, 241, 0.1)",
                color: "var(--text-accent)",
              }}
            >
              <Zap size={10} />
              AI {confidencePercent(complaint.confidence)}
            </span>
          )}
        </div>

        {/* Footer */}
        {!compact && (
          <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 12, color: "var(--text-muted)" }}>
            {complaint.location_text && (
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                <MapPin size={11} />
                {complaint.location_text}
              </span>
            )}
            <span style={{ display: "flex", alignItems: "center", gap: 4, marginLeft: "auto" }}>
              <Clock size={11} />
              {formatRelativeTime(complaint.created_at)}
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}
