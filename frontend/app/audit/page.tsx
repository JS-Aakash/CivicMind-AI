"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  History,
  ShieldCheck,
  Filter,
  Search,
  CheckCircle2,
  AlertTriangle,
  User,
  Brain,
  Zap,
  Clock,
  Layers,
  FileText,
} from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { getAuditTrail } from "@/lib/api";
import { AuditTrailResponse, AuditLogItem } from "@/lib/types";

export default function AuditLogPage() {
  const [events, setEvents] = useState<AuditLogItem[]>([]);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await getAuditTrail(100);
        if (res && res.events) {
          setEvents(res.events);
        }
      } catch (err) {
        console.error("Failed to load audit trail:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredEvents = events.filter((ev) => {
    if (filterType !== "ALL" && ev.event_type !== filterType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        ev.target_id.toLowerCase().includes(q) ||
        ev.summary.toLowerCase().includes(q) ||
        ev.actor.toLowerCase().includes(q) ||
        ev.event_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getEventBadge = (type: string) => {
    switch (type) {
      case "OFFICER_OVERRIDE":
        return { label: "OFFICER OVERRIDE", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" };
      case "OFFICER_APPROVAL":
        return { label: "OFFICER APPROVAL", color: "#22c55e", bg: "rgba(34, 197, 94, 0.15)" };
      case "AI_AUTO_ROUTED":
        return { label: "AI AUTO-ROUTED", color: "#818cf8", bg: "rgba(99, 102, 241, 0.15)" };
      case "INCIDENT_DETECTED":
        return { label: "INCIDENT CLUSTER", color: "#ec4899", bg: "rgba(236, 72, 153, 0.15)" };
      case "SLA_ESCALATION":
        return { label: "SLA ESCALATION", color: "#ef4444", bg: "rgba(239, 68, 68, 0.15)" };
      default:
        return { label: type, color: "#94a3b8", bg: "rgba(255, 255, 255, 0.08)" };
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", backgroundColor: "#060911" }}>
      <TopBar
        title="Governance Audit Trail"
        subtitle="Tamper-Evident Operational & AI Decision Log"
        breadcrumbs={[{ label: "System", href: "/command-center" }, { label: "Audit Log" }]}
      />

      <div style={{ padding: "16px 20px", flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Top Filter & Search Controls */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: "#0d1424",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "10px",
            padding: "12px 16px",
            gap: "12px",
            flexWrap: "wrap",
          }}
        >
          {/* Search Box */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, minWidth: "240px" }}>
            <Search size={16} color="#64748b" />
            <input
              type="text"
              placeholder="Search by case code, actor, or action..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                outline: "none",
                color: "#ffffff",
                fontSize: "13px",
                width: "100%",
              }}
            />
          </div>

          {/* Event Type Filter Buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            {["ALL", "OFFICER_OVERRIDE", "AI_AUTO_ROUTED", "INCIDENT_DETECTED", "SLA_ESCALATION"].map((type) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                style={{
                  padding: "4px 8px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  border: "none",
                  backgroundColor: filterType === type ? "#4f46e5" : "rgba(255, 255, 255, 0.04)",
                  color: filterType === type ? "#ffffff" : "#94a3b8",
                  transition: "all 0.15s ease",
                }}
              >
                {type.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Audit Timeline Records */}
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
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <History size={16} color="#818cf8" />
              <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                AUDIT LOG ENTRIES ({filteredEvents.length})
              </h3>
            </div>
            <span style={{ fontSize: "11px", color: "#64748b" }}>Immutable chronologically ordered records</span>
          </div>

          {filteredEvents.length === 0 ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
              No audit records match the selected filter.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {filteredEvents.map((ev) => {
                const badge = getEventBadge(ev.event_type);
                return (
                  <div
                    key={ev.id}
                    style={{
                      padding: "12px 16px",
                      backgroundColor: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid rgba(255, 255, 255, 0.05)",
                      borderRadius: "8px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "16px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "14px", minWidth: 0 }}>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "3px 8px",
                          borderRadius: "4px",
                          backgroundColor: badge.bg,
                          color: badge.color,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {badge.label}
                      </span>

                      <div style={{ minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff" }}>
                            {ev.target_id}
                          </span>
                          <span style={{ fontSize: "12px", color: "#cbd5e1" }}>— {ev.summary}</span>
                        </div>
                        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                          Actor: <strong style={{ color: "#94a3b8" }}>{ev.actor}</strong> · Target: {ev.target_type}
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: "11px", color: "#64748b", whiteSpace: "nowrap", textAlign: "right" }}>
                      {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
