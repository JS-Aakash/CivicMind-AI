"use client";

import React, { useState, useEffect } from "react";
import {
  MessageSquare,
  AlertTriangle,
  Zap,
  TrendingUp,
  Clock,
  Activity,
  MapPin,
  RefreshCw,
  UserCheck,
  ShieldAlert,
  CheckCircle2,
  Building2,
  Compass,
} from "lucide-react";
import { KPICard } from "@/components/KPICard";
import { ComplaintCard } from "@/components/ComplaintCard";
import { listGrievances, getRoutingKPIs, listIncidents } from "@/lib/api";
import type { Complaint, RoutingKPIsResponse, Incident } from "@/lib/types";
import { DEMO_KPI } from "@/lib/constants";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const CATEGORY_DATA = [
  { name: "Water", count: 38, fill: "#3b82f6" },
  { name: "Roads", count: 24, fill: "#f97316" },
  { name: "Electricity", count: 31, fill: "#eab308" },
  { name: "Drainage", count: 18, fill: "#06b6d4" },
  { name: "Sanitation", count: 15, fill: "#22c55e" },
  { name: "Others", count: 19, fill: "#8b5cf6" },
];

const PRIORITY_DATA = [
  { name: "Critical", value: 8, fill: "#ef4444" },
  { name: "High", value: 43, fill: "#f97316" },
  { name: "Medium", value: 52, fill: "#eab308" },
  { name: "Low", value: 24, fill: "#22c55e" },
];

const LANG_DATA = [
  { name: "Tamil", count: 34 },
  { name: "Tanglish", count: 29 },
  { name: "English", count: 22 },
  { name: "Hindi", count: 18 },
  { name: "Hinglish", count: 17 },
];

const TOOLTIP_STYLE = {
  backgroundColor: "var(--brand-card)",
  border: "1px solid var(--brand-border)",
  borderRadius: 8,
  color: "var(--text-primary)",
  fontSize: 12,
};

export default function DashboardPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [routingKPIs, setRoutingKPIs] = useState<RoutingKPIsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const fetchDashboardData = async () => {
    try {
      const [grievancesData, kpiData, incData] = await Promise.allSettled([
        listGrievances({ page: 1, page_size: 8 }),
        getRoutingKPIs(),
        listIncidents({ page_size: 4 }),
      ]);

      if (grievancesData.status === "fulfilled") {
        setComplaints(grievancesData.value.complaints);
      }
      if (kpiData.status === "fulfilled") {
        setRoutingKPIs(kpiData.value);
      }
      if (incData.status === "fulfilled") {
        setIncidents(incData.value.incidents);
      }
    } catch {
      // Fallback to local state if backend is off
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      {/* Top bar */}
      <div className="top-bar">
        <div>
          <h2 style={{ fontSize: 15, fontWeight: 600 }}>Grievance Intelligence Center</h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Real-time overview of citizen complaints, smart department routing, and SLA compliance.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="demo-banner">
            <span>MODULE 3</span>
            <span>Smart Routing & SLA</span>
          </div>
          <button
            onClick={fetchDashboardData}
            className="btn btn-ghost"
            style={{ padding: "6px 10px", fontSize: 12 }}
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>
      </div>

      <div className="page-container" style={{ paddingTop: 20 }}>
        {/* Row 1: High Level Grievance Volume KPIs */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 14,
            marginBottom: 16,
          }}
        >
          <KPICard
            label="Total Complaints"
            value={DEMO_KPI.total.toLocaleString()}
            icon={MessageSquare}
            iconColor="#6366f1"
            change={12}
            changeLabel="this week"
          />
          <KPICard
            label="Today's Complaints"
            value={DEMO_KPI.today}
            icon={Clock}
            iconColor="#22d3ee"
            change={8}
          />
          <KPICard
            label="High Priority"
            value={DEMO_KPI.high_priority}
            icon={TrendingUp}
            iconColor="#f97316"
            change={5}
          />
          <KPICard
            label="Critical Incidents"
            value={routingKPIs ? routingKPIs.critical_cases_count : DEMO_KPI.critical}
            icon={AlertTriangle}
            iconColor="#ef4444"
          />
          <KPICard
            label="AI Confidence"
            value={DEMO_KPI.ai_confidence}
            icon={Zap}
            iconColor="#22c55e"
            highlight
          />
          <KPICard
            label="Open Incidents"
            value={DEMO_KPI.open_incidents}
            icon={Activity}
            iconColor="#a855f7"
          />
        </div>

        {/* Row 2: MODULE 3 SMART ROUTING & SLA OPERATIONAL KPIs (Section 29) */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
            gap: 14,
            marginBottom: 24,
          }}
        >
          <div className="kpi-card" style={{ borderLeft: "3px solid #22c55e" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                Auto-Routed
              </span>
              <CheckCircle2 size={16} color="#22c55e" />
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
              {routingKPIs ? `${routingKPIs.auto_routed_percent}%` : "82.4%"}
            </div>
            <div style={{ fontSize: 11, color: "#22c55e", marginTop: 2 }}>
              {routingKPIs ? `${routingKPIs.auto_routed_count} cases` : "122 dispatched auto"}
            </div>
          </div>

          <div className="kpi-card" style={{ borderLeft: "3px solid #f59e0b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                Officer Review
              </span>
              <UserCheck size={16} color="#f59e0b" />
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
              {routingKPIs ? `${routingKPIs.officer_review_percent}%` : "13.5%"}
            </div>
            <div style={{ fontSize: 11, color: "#f59e0b", marginTop: 2 }}>
              {routingKPIs ? `${routingKPIs.officer_review_count} pending triage` : "20 cases"}
            </div>
          </div>

          <div className="kpi-card" style={{ borderLeft: "3px solid #ef4444" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                Manual Review
              </span>
              <ShieldAlert size={16} color="#ef4444" />
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
              {routingKPIs ? `${routingKPIs.manual_review_percent}%` : "4.1%"}
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Low confidence queue</div>
          </div>

          <div className="kpi-card" style={{ borderLeft: "3px solid #38bdf8" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                SLA Compliance
              </span>
              <Clock size={16} color="#38bdf8" />
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>
              {routingKPIs ? `${routingKPIs.sla_within_count} Active` : "138 On-Track"}
            </div>
            <div style={{ fontSize: 11, color: "#38bdf8", marginTop: 2 }}>Target 94% on-time</div>
          </div>

          <div className="kpi-card" style={{ borderLeft: "3px solid #f97316" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                SLA At Risk
              </span>
              <AlertTriangle size={16} color="#f97316" />
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f97316" }}>
              {routingKPIs ? `${routingKPIs.sla_at_risk_count}` : "7"}
            </div>
            <div style={{ fontSize: 11, color: "#f97316", marginTop: 2 }}>Approaching breach window</div>
          </div>

          <div className="kpi-card" style={{ borderLeft: "3px solid #dc2626" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                SLA Breached
              </span>
              <AlertTriangle size={16} color="#dc2626" />
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#dc2626" }}>
              {routingKPIs ? `${routingKPIs.sla_breached_count}` : "3"}
            </div>
            <div style={{ fontSize: 11, color: "#dc2626", marginTop: 2 }}>Escalation triggered</div>
          </div>
        </div>

        {/* Charts Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
          {/* Category Distribution */}
          <div className="card">
            <h3 style={{ fontSize: 13, marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}>
              <MapPin size={14} color="var(--accent-indigo)" />
              By Category
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={CATEGORY_DATA} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--brand-border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {CATEGORY_DATA.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Priority Pie */}
          <div className="card" style={{ display: "flex", flexDirection: "column" }}>
            <h3 style={{ fontSize: 13, marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}>
              <AlertTriangle size={14} color="#f97316" />
              By Priority
            </h3>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={PRIORITY_DATA} cx="50%" cy="50%" innerRadius={40} outerRadius={65} dataKey="value" strokeWidth={0}>
                    {PRIORITY_DATA.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center", marginTop: 4 }}>
                {PRIORITY_DATA.map((d) => (
                  <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: d.fill }} />
                    <span style={{ color: "var(--text-muted)" }}>
                      {d.name} ({d.value})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Language Distribution */}
          <div className="card">
            <h3 style={{ fontSize: 13, marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}>
              <Zap size={14} color="var(--accent-cyan)" />
              By Language
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {LANG_DATA.map((lang) => {
                const maxCount = Math.max(...LANG_DATA.map((l) => l.count));
                const pct = (lang.count / maxCount) * 100;
                return (
                  <div key={lang.name}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{lang.name}</span>
                      <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{lang.count}</span>
                    </div>
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{ width: `${pct}%`, background: "linear-gradient(90deg, #6366f1, #22d3ee)" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Emerging Civic Incidents (Module 4) */}
        {incidents.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, display: "flex", alignItems: "center", gap: 8, color: "var(--text-primary)" }}>
                <span style={{ fontSize: 16 }}>🚨</span>
                Emerging Civic Incidents (Spatio-Temporal Clusters)
              </h3>
              <Link
                href="/incidents"
                style={{ fontSize: 12, color: "var(--accent-indigo)", textDecoration: "none", fontWeight: 600 }}
              >
                View Incident Command ({incidents.length}) →
              </Link>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
              {incidents.slice(0, 4).map((inc) => (
                <Link
                  key={inc.id}
                  href={`/incidents/${inc.incident_code}`}
                  style={{ textDecoration: "none" }}
                >
                  <div
                    className="card"
                    style={{
                      padding: 14,
                      borderLeft: inc.is_emerging
                        ? "4px solid #f97316"
                        : inc.priority === "critical"
                        ? "4px solid #ef4444"
                        : "3px solid var(--accent-indigo)",
                      transition: "transform 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                      <span style={{ fontFamily: "monospace", fontSize: 11, color: "var(--accent-indigo)", fontWeight: 600 }}>
                        {inc.incident_code}
                      </span>
                      <div style={{ display: "flex", gap: 4 }}>
                        <span
                          className={`badge badge-${inc.priority}`}
                          style={{ fontSize: 10, padding: "1px 6px" }}
                        >
                          {inc.priority.toUpperCase()}
                        </span>
                        {inc.trend && (
                          <span
                            style={{
                              fontSize: 10,
                              padding: "1px 6px",
                              borderRadius: 4,
                              background: inc.trend === "RISING" ? "rgba(239,68,68,0.15)" : "rgba(59,130,246,0.15)",
                              color: inc.trend === "RISING" ? "#ef4444" : "#3b82f6",
                              fontWeight: 600,
                            }}
                          >
                            {inc.trend === "RISING" ? "↑ RISING" : inc.trend}
                          </span>
                        )}
                      </div>
                    </div>

                    <h4 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {inc.title}
                    </h4>

                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                      <span>👥 {inc.complaint_count} reports</span>
                      <span>📍 {inc.affected_area || "Metropolitan Area"}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Live Feed */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <h3 style={{ fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>
              <div className="status-dot" />
              Live Grievance Feed & Dispatch Stream
            </h3>
            <span suppressHydrationWarning style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          </div>

          {loading ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="skeleton" style={{ height: 140, borderRadius: 12 }} />
              ))}
            </div>
          ) : complaints.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 12 }}>
              {complaints.map((c) => (
                <ComplaintCard key={c.id} complaint={c} />
              ))}
            </div>
          ) : (
            <div
              style={{
                textAlign: "center",
                padding: "48px 24px",
                background: "var(--brand-card)",
                borderRadius: 12,
                border: "1px solid var(--brand-border)",
                color: "var(--text-muted)",
              }}
            >
              <MessageSquare size={32} style={{ margin: "0 auto 12px", opacity: 0.4 }} />
              <p style={{ fontSize: 14, marginBottom: 6 }}>Backend running with seeded complaints</p>
              <p style={{ fontSize: 12 }}>Explore complaints in the complaints registry or test routing in AI Report</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
