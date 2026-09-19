"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  MapPin,
  Clock,
  TrendingUp,
  Activity,
  Flame,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  Building2,
  Globe,
  ChevronRight,
} from "lucide-react";
import { listIncidents, recomputeIncidents } from "@/lib/api";
import type { Incident, IncidentListResponse } from "@/lib/types";
import { PriorityBadge } from "@/components/PriorityBadge";
import { formatRelativeTime } from "@/lib/utils";
import { CATEGORIES } from "@/lib/constants";

export default function IncidentsPage() {
  const [data, setData] = useState<IncidentListResponse | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTab, setFilterTab] = useState<"all" | "emerging" | "critical" | "rising" | "resolved">("all");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [isRecomputing, setIsRecomputing] = useState(false);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const res = await listIncidents({
        category: categoryFilter || undefined,
        trend: filterTab === "rising" ? "RISING" : undefined,
        priority: filterTab === "critical" ? "critical" : undefined,
        status: filterTab === "resolved" ? "resolved" : undefined,
      });
      setData(res);
      let list = res.incidents;
      if (filterTab === "emerging") {
        list = list.filter((i) => i.is_emerging);
      }
      setIncidents(list);
    } catch {
      setIncidents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecompute = async () => {
    setIsRecomputing(true);
    try {
      await recomputeIncidents({ hours: 72, dry_run: false });
      await fetchIncidents();
    } catch (e: any) {
      alert(`Recompute failed: ${e.message}`);
    } finally {
      setIsRecomputing(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [filterTab, categoryFilter]);

  return (
    <div>
      <div className="top-bar">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <h2 style={{ fontSize: 15, fontWeight: 600 }}>Civic Incident Intelligence Dashboard</h2>
            <span style={{ fontSize: 11, background: "rgba(99,102,241,0.15)", color: "var(--accent-indigo)", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
              Module 4 Production
            </span>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Spatio-temporal DBSCAN cluster discovery from multilingual citizen grievances
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={handleRecompute}
            disabled={isRecomputing}
            className="btn btn-primary"
            style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6 }}
          >
            <Sparkles size={13} />
            {isRecomputing ? "Clustering Engine Running..." : "Recompute Incidents"}
          </button>
          <button onClick={fetchIncidents} className="btn btn-ghost" style={{ padding: "6px 10px" }}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      <div className="page-container" style={{ paddingTop: 20 }}>
        {/* KPI Summary Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
          <div className="card" style={{ padding: 14 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Active Incidents</span>
              <Activity size={16} color="var(--accent-indigo)" />
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>
              {data?.active_count ?? incidents.length}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              Active spatio-temporal clusters
            </div>
          </div>

          <div className="card" style={{ padding: 14, borderLeft: "3px solid #f97316" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "#f97316", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>Emerging Early Warnings</span>
              <Flame size={16} color="#f97316" />
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#f97316" }}>
              {data?.emerging_count ?? incidents.filter((i) => i.is_emerging).length}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              Rapid growth within localized radius
            </div>
          </div>

          <div className="card" style={{ padding: 14, borderLeft: "3px solid #ef4444" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "#ef4444", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>Critical Severity</span>
              <ShieldAlert size={16} color="#ef4444" />
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#ef4444" }}>
              {data?.critical_count ?? incidents.filter((i) => i.priority === "critical").length}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              Immediate hazards & high impact
            </div>
          </div>

          <div className="card" style={{ padding: 14, borderLeft: "3px solid #3b82f6" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "#3b82f6", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600 }}>Rising Velocity</span>
              <TrendingUp size={16} color="#3b82f6" />
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#3b82f6" }}>
              {data?.rising_count ?? incidents.filter((i) => i.trend === "RISING").length}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              Rate increasing in past 6 hours
            </div>
          </div>
        </div>

        {/* Filter Bar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
          <div style={{ display: "flex", gap: 6, background: "var(--brand-card)", padding: 4, borderRadius: 8, border: "1px solid var(--brand-border)" }}>
            {(
              [
                { id: "all", label: "All Incidents" },
                { id: "emerging", label: "🚨 Emerging" },
                { id: "critical", label: "Critical" },
                { id: "rising", label: "↑ Rising" },
                { id: "resolved", label: "Resolved" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilterTab(tab.id)}
                style={{
                  padding: "5px 12px",
                  fontSize: 12,
                  border: "none",
                  borderRadius: 6,
                  cursor: "pointer",
                  background: filterTab === tab.id ? "var(--accent-indigo)" : "transparent",
                  color: filterTab === tab.id ? "#fff" : "var(--text-secondary)",
                  fontWeight: filterTab === tab.id ? 600 : 400,
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              className="input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search incidents..."
              style={{ width: 180, fontSize: 12, padding: "5px 10px" }}
            />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input"
              style={{ width: 140, fontSize: 12, padding: "5px 8px" }}
            >
              <option value="">All Categories</option>
              <option value="water">Water Supply</option>
              <option value="roads">Road Damage</option>
              <option value="sanitation">Sanitation</option>
              <option value="electricity">Electricity</option>
              <option value="drainage">Drainage</option>
            </select>
          </div>
        </div>

        {/* Incident List */}
        {(() => {
          const filteredIncidents = incidents.filter((inc) => {
            if (!searchQuery.trim()) return true;
            const q = searchQuery.toLowerCase();
            return (
              (inc.incident_code && inc.incident_code.toLowerCase().includes(q)) ||
              (inc.title && inc.title.toLowerCase().includes(q)) ||
              (inc.category && inc.category.toLowerCase().includes(q)) ||
              (inc.affected_area && inc.affected_area.toLowerCase().includes(q))
            );
          });

          if (loading) {
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="skeleton" style={{ height: 130, borderRadius: 12 }} />
                ))}
              </div>
            );
          }

          if (filteredIncidents.length === 0) {
            return (
              <div className="card" style={{ padding: 40, textAlign: "center" }}>
                <AlertTriangle size={32} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>No incidents found</h3>
                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  Try adjusting search or category filters.
                </p>
              </div>
            );
          }

          return (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {filteredIncidents.map((inc) => {
              const catConfig = CATEGORIES[inc.category as keyof typeof CATEGORIES] || CATEGORIES.general;
              return (
                <Link
                  key={inc.id}
                  href={`/incidents/${inc.incident_code}`}
                  style={{ textDecoration: "none" }}
                >
                  <div
                    className="complaint-card"
                    style={{
                      display: "flex",
                      gap: 16,
                      alignItems: "center",
                      borderLeft: inc.is_emerging
                        ? "4px solid #f97316"
                        : inc.priority === "critical"
                        ? "4px solid #ef4444"
                        : "1px solid var(--brand-border)",
                    }}
                  >
                    {/* Icon */}
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
                      <AlertTriangle size={24} color={catConfig.color} />
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                        <span style={{ fontFamily: "monospace", fontSize: 12, color: "var(--accent-indigo)", fontWeight: 600 }}>
                          {inc.incident_code}
                        </span>
                        <PriorityBadge priority={inc.priority} size="sm" />
                        <span
                          style={{
                            fontSize: 11,
                            padding: "2px 8px",
                            borderRadius: 4,
                            background: "rgba(99,102,241,0.1)",
                            color: "var(--accent-indigo)",
                            fontWeight: 600,
                          }}
                        >
                          {inc.status.replace("_", " ").toUpperCase()}
                        </span>
                        {inc.is_emerging && (
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
                        {inc.trend && (
                          <span
                            style={{
                              fontSize: 11,
                              padding: "2px 8px",
                              borderRadius: 4,
                              background:
                                inc.trend === "RISING"
                                  ? "rgba(239,68,68,0.12)"
                                  : "rgba(59,130,246,0.12)",
                              color: inc.trend === "RISING" ? "#ef4444" : "#3b82f6",
                              fontWeight: 600,
                            }}
                          >
                            {inc.trend === "RISING" ? "↑ RISING" : inc.trend}
                          </span>
                        )}
                      </div>

                      <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, color: "var(--text-primary)" }}>
                        {inc.title}
                      </h3>

                      <p style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>
                        {inc.description}
                      </p>

                      <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--text-muted)", flexWrap: "wrap", alignItems: "center" }}>
                        <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                          👥 {inc.complaint_count} Related Complaints
                        </span>
                        {inc.affected_area && (
                          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <MapPin size={12} color="var(--accent-indigo)" />
                            {inc.affected_area}
                          </span>
                        )}
                        {inc.primary_department && (
                          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <Building2 size={12} color="#06b6d4" />
                            {inc.primary_department}
                          </span>
                        )}
                        {inc.languages && inc.languages.length > 0 && (
                          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <Globe size={12} color="#8b5cf6" />
                            {inc.languages.join(", ").toUpperCase()}
                          </span>
                        )}
                        {inc.confidence && (
                          <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
                            Confidence: {Math.round(inc.confidence * 100)}%
                          </span>
                        )}
                      </div>
                    </div>

                    <ChevronRight size={18} color="var(--text-muted)" />
                  </div>
                </Link>
              );
            })}
          </div>
        );
      })()}
      </div>
    </div>
  );
}
