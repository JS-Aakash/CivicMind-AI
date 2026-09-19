"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Flame,
  Clock,
  CheckCircle2,
  TrendingUp,
  MapPin,
  RefreshCw,
  Eye,
  ArrowUpRight,
  ShieldAlert,
  Zap,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Info,
} from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { MapView } from "@/components/MapView";
import {
  getCommandCenterOverview,
  getMapComplaints,
  getMapIncidents,
  listIncidents,
} from "@/lib/api";
import {
  CommandCenterOverviewResponse,
  MapMarker,
  MapIncidentMarker,
  Incident,
  Complaint,
} from "@/lib/types";

export default function CommandCenterPage() {
  const [data, setData] = useState<CommandCenterOverviewResponse | null>(null);
  const [complaints, setComplaints] = useState<MapMarker[]>([]);
  const [incidents, setIncidents] = useState<MapIncidentMarker[]>([]);
  const [selectedMarker, setSelectedMarker] = useState<MapMarker | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<MapIncidentMarker | null>(null);
  const [layerFilter, setLayerFilter] = useState<"all" | "critical" | "emerging" | "incidents">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefreshedSeconds, setLastRefreshedSeconds] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchOverview = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const [overviewRes, mapComplaintsRes, mapIncidentsRes] = await Promise.all([
        getCommandCenterOverview().catch(() => null),
        getMapComplaints().catch(() => null),
        getMapIncidents().catch(() => null),
      ]);

      if (overviewRes) {
        setData(overviewRes);
      }
      if (mapComplaintsRes) {
        setComplaints(mapComplaintsRes.complaints || []);
      }
      if (mapIncidentsRes) {
        setIncidents(Array.isArray(mapIncidentsRes) ? mapIncidentsRes : []);
      }
      setLastRefreshedSeconds(0);
    } catch (err) {
      console.error("Failed to load command center data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);



  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, [fetchOverview]);

  // Timer counter for "Last updated Xs ago"
  useEffect(() => {
    const timer = setInterval(() => {
      setLastRefreshedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Filtered map markers
  const filteredComplaints = complaints.filter((c) => {
    if (layerFilter === "critical") return c.priority === "critical";
    if (layerFilter === "incidents") return !!c.incident_id;
    return true;
  });

  const filteredIncidents = incidents.filter((inc) => {
    if (layerFilter === "critical") return inc.priority === "critical";
    if (layerFilter === "emerging") return inc.is_emerging;
    return true;
  });

  const kpis = data?.kpis;

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", backgroundColor: "#060911" }}>
      {/* Top Bar */}
      <TopBar
        title="Civic Operations Command Center"
        subtitle="Live City Intelligence Grid"
      />


      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>
        {/* ─── 1. HIGH DENSITY KPI STRIP ────────────────────────────────────────── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "12px",
          }}
        >
          {/* Card 1: Total Volume */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(99, 102, 241, 0.2)",
              borderRadius: "10px",
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 600, textTransform: "uppercase" }}>
                Total Grievances
              </span>
              <span
                style={{
                  fontSize: "10px",
                  color: "#22c55e",
                  fontWeight: 700,
                  backgroundColor: "rgba(34, 197, 94, 0.12)",
                  padding: "1px 5px",
                  borderRadius: "4px",
                }}
              >
                +{kpis ? kpis.complaints_growth_pct : 8.4}%
              </span>
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#ffffff", letterSpacing: "-0.02em" }}>
              {kpis ? kpis.total_complaints.toLocaleString() : "..."}
            </div>
            <div style={{ fontSize: "11px", color: "#64748b" }}>vs previous 7-day period</div>
          </div>

          {/* Card 2: Critical */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(239, 68, 68, 0.25)",
              borderRadius: "10px",
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#f87171", fontWeight: 600, textTransform: "uppercase" }}>
                Critical Priority
              </span>
              <ShieldAlert size={14} color="#ef4444" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#ef4444", letterSpacing: "-0.02em" }}>
              {kpis ? kpis.critical_count : "..."}
            </div>
            <div style={{ fontSize: "11px", color: "#fca5a5" }}>
              {kpis ? `${kpis.immediate_attention_count} require immediate action` : "Calculating..."}
            </div>
          </div>

          {/* Card 3: Active Incidents */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              borderRadius: "10px",
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#fbbf24", fontWeight: 600, textTransform: "uppercase" }}>
                Active Incidents
              </span>
              <Flame size={14} color="#f59e0b" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#f59e0b", letterSpacing: "-0.02em" }}>
              {kpis ? kpis.active_incidents : "..."}
            </div>
            <div style={{ fontSize: "11px", color: "#fde68a" }}>
              {kpis ? `${kpis.emerging_incidents} emerging spatial clusters` : "Clustering..."}
            </div>
          </div>

          {/* Card 4: SLA At Risk */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(234, 179, 8, 0.25)",
              borderRadius: "10px",
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#facc15", fontWeight: 600, textTransform: "uppercase" }}>
                SLA At Risk
              </span>
              <Clock size={14} color="#eab308" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#eab308", letterSpacing: "-0.02em" }}>
              {kpis ? kpis.sla_at_risk_count : "..."}
            </div>
            <div style={{ fontSize: "11px", color: "#fef08a" }}>approaching deadline</div>
          </div>

          {/* Card 5: SLA Breached */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(225, 29, 72, 0.25)",
              borderRadius: "10px",
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#fda4af", fontWeight: 600, textTransform: "uppercase" }}>
                SLA Breached
              </span>
              <AlertTriangle size={14} color="#e11d48" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#f43f5e", letterSpacing: "-0.02em" }}>
              {kpis ? kpis.sla_breached_count : "..."}
            </div>
            <div style={{ fontSize: "11px", color: "#fecdd3" }}>requires escalation</div>
          </div>

          {/* Card 6: Resolution Rate */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(34, 197, 94, 0.25)",
              borderRadius: "10px",
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", color: "#4ade80", fontWeight: 600, textTransform: "uppercase" }}>
                Resolution Rate
              </span>
              <CheckCircle2 size={14} color="#22c55e" />
            </div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#22c55e", letterSpacing: "-0.02em" }}>
              {kpis ? `${kpis.resolution_rate_pct}%` : "..."}
            </div>
            <div style={{ fontSize: "11px", color: "#bbf7d0" }}>30-day municipal benchmark</div>
          </div>
        </div>

        {/* ─── 2. MAIN SPLIT VIEW: LIVE MAP CENTERPIECE + AI OPERATIONS PANEL ───────── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 380px",
            gap: "16px",
            minHeight: "560px",
          }}
          className="command-center-grid"
        >
          {/* Left Column: Live City Map Centerpiece */}
          <div
            style={{
              position: "relative",
              backgroundColor: "#0d1424",
              border: "1px solid rgba(99, 102, 241, 0.25)",
              borderRadius: "12px",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              boxShadow: "0 8px 24px rgba(0, 0, 0, 0.5)",
            }}
          >
            {/* Map Controls Header Strip */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 14px",
                backgroundColor: "rgba(13, 20, 36, 0.95)",
                borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                zIndex: 20,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "#22c55e",
                    boxShadow: "0 0 8px #22c55e",
                  }}
                />
                <span style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff" }}>
                  LIVE GIS OPERATIONS GRID
                </span>
                <span style={{ fontSize: "11px", color: "#64748b" }}>
                  ({filteredComplaints.length} cases · {filteredIncidents.length} clusters)
                </span>
              </div>

              {/* Layer toggles */}
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                {(
                  [
                    { id: "all", label: "All Layers" },
                    { id: "critical", label: "Critical Only" },
                    { id: "emerging", label: "Emerging" },
                    { id: "incidents", label: "Incidents" },
                  ] as const
                ).map((layer) => (
                  <button
                    key={layer.id}
                    onClick={() => setLayerFilter(layer.id)}
                    style={{
                      padding: "4px 8px",
                      borderRadius: "6px",
                      fontSize: "11px",
                      fontWeight: 600,
                      cursor: "pointer",
                      border: "none",
                      backgroundColor:
                        layerFilter === layer.id
                          ? "#4f46e5"
                          : "rgba(255, 255, 255, 0.05)",
                      color: layerFilter === layer.id ? "#ffffff" : "#94a3b8",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {layer.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Map Canvas */}
            <div style={{ flex: 1, position: "relative", minHeight: "480px" }}>
              <MapView
                markers={filteredComplaints}
                incidents={filteredIncidents}
                onMarkerClick={(m: MapMarker) => {
                  setSelectedMarker(m);
                  setSelectedIncident(null);
                }}
                onIncidentClick={(inc: MapIncidentMarker) => {
                  setSelectedIncident(inc);
                  setSelectedMarker(null);
                }}
              />


              {/* Rich Floating Detail Panel for Selected Incident */}
              {selectedIncident && (
                <div
                  style={{
                    position: "absolute",
                    bottom: "16px",
                    left: "16px",
                    width: "320px",
                    backgroundColor: "#0d1424",
                    border: "1px solid rgba(245, 158, 11, 0.4)",
                    borderRadius: "10px",
                    padding: "14px",
                    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.8)",
                    zIndex: 30,
                    animation: "fadeIn 0.2s ease-in-out",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        backgroundColor: "rgba(245, 158, 11, 0.2)",
                        color: "#f59e0b",
                        border: "1px solid rgba(245, 158, 11, 0.4)",
                      }}
                    >
                      {selectedIncident.incident_code} · {selectedIncident.priority?.toUpperCase()}
                    </span>
                    <button
                      onClick={() => setSelectedIncident(null)}
                      style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: "14px" }}
                    >
                      ✕
                    </button>
                  </div>

                  <h4 style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc", margin: "0 0 6px 0" }}>
                    {selectedIncident.title}
                  </h4>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "11px", color: "#94a3b8", marginBottom: "12px" }}>
                    <div>
                      <span style={{ color: "#64748b" }}>Cases: </span>
                      <strong style={{ color: "#ffffff" }}>{selectedIncident.complaint_count}</strong>
                    </div>
                    <div>
                      <span style={{ color: "#64748b" }}>Trend: </span>
                      <strong style={{ color: "#22c55e" }}>↑ {selectedIncident.trend || "Increasing"}</strong>
                    </div>
                    <div>
                      <span style={{ color: "#64748b" }}>Area: </span>
                      <strong style={{ color: "#ffffff" }}>{selectedIncident.affected_area || "1.8 km"}</strong>
                    </div>
                    <div>
                      <span style={{ color: "#64748b" }}>Status: </span>
                      <strong style={{ color: "#eab308" }}>{selectedIncident.status}</strong>
                    </div>
                  </div>

                  <Link
                    href={`/incidents/${selectedIncident.id}`}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px",
                      width: "100%",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      backgroundColor: "#4f46e5",
                      color: "#ffffff",
                      fontSize: "12px",
                      fontWeight: 600,
                      textDecoration: "none",
                    }}
                  >
                    <span>Inspect Incident Details</span>
                    <ArrowUpRight size={14} />
                  </Link>
                </div>
              )}

              {/* Rich Floating Detail Panel for Selected Complaint */}
              {selectedMarker && (
                <div
                  style={{
                    position: "absolute",
                    bottom: "16px",
                    left: "16px",
                    width: "320px",
                    backgroundColor: "#0d1424",
                    border: "1px solid rgba(99, 102, 241, 0.4)",
                    borderRadius: "10px",
                    padding: "14px",
                    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.8)",
                    zIndex: 30,
                    animation: "fadeIn 0.2s ease-in-out",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        backgroundColor: "rgba(99, 102, 241, 0.2)",
                        color: "#a5b4fc",
                        border: "1px solid rgba(99, 102, 241, 0.4)",
                      }}
                    >
                      {selectedMarker.complaint_code}
                    </span>
                    <button
                      onClick={() => setSelectedMarker(null)}
                      style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: "14px" }}
                    >
                      ✕
                    </button>
                  </div>

                  <p
                    style={{
                      fontSize: "12px",
                      color: "#e2e8f0",
                      margin: "0 0 10px 0",
                      maxHeight: "60px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    "{selectedMarker.text_preview}"
                  </p>

                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#94a3b8", marginBottom: "12px" }}>
                    <span>
                      Priority: <strong style={{ color: "#ef4444" }}>{selectedMarker.priority?.toUpperCase()}</strong>
                    </span>
                    <span>
                      Category: <strong style={{ color: "#ffffff" }}>{selectedMarker.category || "General"}</strong>
                    </span>
                  </div>

                  <Link
                    href={`/complaints/${selectedMarker.id}`}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px",
                      width: "100%",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      backgroundColor: "#4f46e5",
                      color: "#ffffff",
                      fontSize: "12px",
                      fontWeight: 600,
                      textDecoration: "none",
                    }}
                  >
                    <span>Open Case Intelligence</span>
                    <ArrowUpRight size={14} />
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: AI Operations Panel */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div
              style={{
                backgroundColor: "#0d1424",
                border: "1px solid rgba(99, 102, 241, 0.25)",
                borderRadius: "12px",
                padding: "16px",
                boxShadow: "0 8px 24px rgba(0, 0, 0, 0.5)",
                display: "flex",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Zap size={16} color="#818cf8" />
                <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                  AI OPERATIONS
                </h3>
              </div>


              {/* Critical Alert 1 */}
              <div
                style={{
                  backgroundColor: "rgba(239, 68, 68, 0.08)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  borderRadius: "8px",
                  padding: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <ShieldAlert size={14} color="#ef4444" />
                    <span style={{ fontSize: "11px", fontWeight: 700, color: "#f87171" }}>
                      ELECTRICAL HAZARD DETECTED
                    </span>
                  </div>
                  <span style={{ fontSize: "10px", color: "#fca5a5" }}>14m ago</span>
                </div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#ffffff" }}>
                  Live wire sparking near residential street
                </div>
                <div style={{ fontSize: "11px", color: "#cbd5e1" }}>
                  3 complaints · T. Nagar / Ward 112
                </div>
                <div style={{ fontSize: "10px", color: "#94a3b8" }}>
                  Signals: Voice audio (Tanglish) + Qwen3-VL visible hazard
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginTop: "4px",
                    paddingTop: "6px",
                    borderTop: "1px solid rgba(239, 68, 68, 0.15)",
                  }}
                >
                  <span style={{ fontSize: "10px", color: "#f87171", fontWeight: 600 }}>
                    SLA: 1h 42m remaining
                  </span>
                  <Link
                    href="/review"
                    style={{
                      fontSize: "11px",
                      color: "#ffffff",
                      backgroundColor: "#ef4444",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      textDecoration: "none",
                      fontWeight: 600,
                    }}
                  >
                    Review Queue
                  </Link>
                </div>
              </div>

              {/* Emerging Pattern Alert */}
              <div
                style={{
                  backgroundColor: "rgba(245, 158, 11, 0.08)",
                  border: "1px solid rgba(245, 158, 11, 0.3)",
                  borderRadius: "8px",
                  padding: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <Flame size={14} color="#f59e0b" />
                    <span style={{ fontSize: "11px", fontWeight: 700, color: "#fbbf24" }}>
                      EMERGING PATTERN
                    </span>
                  </div>
                  <span style={{ fontSize: "10px", color: "#fde68a" }}>2h window</span>
                </div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#ffffff" }}>
                  Water supply disruption surge (+42%)
                </div>
                <div style={{ fontSize: "11px", color: "#cbd5e1" }}>
                  13 related complaints · Anna Nagar Zone
                </div>
                <div style={{ fontSize: "10px", color: "#94a3b8" }}>
                  Radius: 1.8 km · DBSCAN Cohesion: 94%
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginTop: "4px",
                    paddingTop: "6px",
                    borderTop: "1px solid rgba(245, 158, 11, 0.15)",
                  }}
                >
                  <span style={{ fontSize: "10px", color: "#fbbf24", fontWeight: 600 }}>
                    ROUTED: Water Supply Dept
                  </span>
                  <Link
                    href="/incidents"
                    style={{
                      fontSize: "11px",
                      color: "#ffffff",
                      backgroundColor: "#d97706",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      textDecoration: "none",
                      fontWeight: 600,
                    }}
                  >
                    Investigate
                  </Link>
                </div>
              </div>

              {/* SLA Warning */}
              <div
                style={{
                  backgroundColor: "rgba(234, 179, 8, 0.08)",
                  border: "1px solid rgba(234, 179, 8, 0.3)",
                  borderRadius: "8px",
                  padding: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <Clock size={14} color="#eab308" />
                    <span style={{ fontSize: "11px", fontWeight: 700, color: "#facc15" }}>
                      SLA AT RISK
                    </span>
                  </div>
                  <span style={{ fontSize: "10px", color: "#fef08a" }}>7 Cases</span>
                </div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#ffffff" }}>
                  Road repair & drainage cases nearing deadline
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginTop: "4px",
                    paddingTop: "6px",
                    borderTop: "1px solid rgba(234, 179, 8, 0.15)",
                  }}
                >
                  <span style={{ fontSize: "10px", color: "#94a3b8" }}>&lt; 2 hours remaining</span>
                  <Link
                    href="/sla"
                    style={{
                      fontSize: "11px",
                      color: "#ffffff",
                      backgroundColor: "#ca8a04",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      textDecoration: "none",
                      fontWeight: 600,
                    }}
                  >
                    View Queue
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* ─── 3. DEPARTMENT WORKLOAD & OPERATIONAL SUMMARY ──────────────────────── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "14px",
          }}
        >
          {/* Water Supply */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(56, 189, 248, 0.2)",
              borderRadius: "10px",
              padding: "14px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#38bdf8" }}>
                Water Supply Department
              </span>
              <span style={{ fontSize: "10px", color: "#94a3b8" }}>SLA: 94.2%</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>
              <span>Active: <strong style={{ color: "#ffffff" }}>78 cases</strong></span>
              <span>Avg SLA: <strong style={{ color: "#ffffff" }}>11.4 hrs</strong></span>
            </div>
            <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{ width: "94.2%", height: "100%", backgroundColor: "#38bdf8" }} />
            </div>
          </div>

          {/* Roads & Bridges */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(251, 146, 60, 0.2)",
              borderRadius: "10px",
              padding: "14px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#fb923c" }}>
                Roads & Bridges Department
              </span>
              <span style={{ fontSize: "10px", color: "#94a3b8" }}>SLA: 89.6%</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>
              <span>Active: <strong style={{ color: "#ffffff" }}>84 cases</strong></span>
              <span>Avg SLA: <strong style={{ color: "#ffffff" }}>18.2 hrs</strong></span>
            </div>
            <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{ width: "89.6%", height: "100%", backgroundColor: "#fb923c" }} />
            </div>
          </div>

          {/* Electricity Board */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(234, 179, 8, 0.2)",
              borderRadius: "10px",
              padding: "14px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#eab308" }}>
                Electricity Distribution Board
              </span>
              <span style={{ fontSize: "10px", color: "#94a3b8" }}>SLA: 96.8%</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b", marginBottom: "4px" }}>
              <span>Active: <strong style={{ color: "#ffffff" }}>32 cases</strong></span>
              <span>Avg SLA: <strong style={{ color: "#ffffff" }}>3.8 hrs</strong></span>
            </div>
            <div style={{ width: "100%", height: "6px", backgroundColor: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
              <div style={{ width: "96.8%", height: "100%", backgroundColor: "#eab308" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
