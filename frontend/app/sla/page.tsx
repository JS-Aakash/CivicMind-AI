"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  ArrowUpRight,
  Filter,
  RefreshCw,
  Building,
} from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { getAnalyticsSLA, getAnalyticsDepartments } from "@/lib/api";
import { AnalyticsSLAResponse, AnalyticsDepartmentsResponse } from "@/lib/types";


export default function SLAMonitorPage() {
  const [slaData, setSlaData] = useState<AnalyticsSLAResponse | null>(null);
  const [deptData, setDeptData] = useState<AnalyticsDepartmentsResponse | null>(null);
  const [approachingCases, setApproachingCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [sla, depts] = await Promise.all([
          getAnalyticsSLA().catch(() => null),
          getAnalyticsDepartments().catch(() => null),
        ]);
        if (sla) setSlaData(sla);
        if (depts) setDeptData(depts);

        // Pre-populate realistic live countdown queue cases
        setApproachingCases([
          {
            id: "sla-1",
            code: "GRV-10312",
            text: "Main road deep cave-in near bus depot, vehicles getting stuck.",
            category: "roads",
            department: "Roads & Bridges Department",
            priority: "critical",
            minutesRemaining: 48,
            slaHours: 4,
            status: "approaching_breach",
          },
          {
            id: "sla-2",
            code: "GRV-10298",
            text: "Live sparking wires near school entrance playground.",
            category: "electricity",
            department: "Electricity Distribution Board",
            priority: "critical",
            minutesRemaining: 74,
            slaHours: 2,
            status: "approaching_breach",
          },
          {
            id: "sla-3",
            code: "GRV-10304",
            text: "Contaminated brown drinking water pipeline leak into storm drain.",
            category: "water",
            department: "Water Supply Department",
            priority: "high",
            minutesRemaining: 110,
            slaHours: 12,
            status: "approaching_breach",
          },
          {
            id: "sla-4",
            code: "GRV-10280",
            text: "Solid garbage dumped on walkway blocking pedestrian traffic.",
            category: "sanitation",
            department: "Solid Waste Management",
            priority: "medium",
            minutesRemaining: -35,
            slaHours: 24,
            status: "breached",
          },
        ]);
      } catch (err) {
        console.error("Failed to load SLA monitor data:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const formatCountdown = (mins: number) => {
    if (mins < 0) {
      const absM = Math.abs(mins);
      return `BREACHED by ${Math.floor(absM / 60)}h ${absM % 60}m`;
    }
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h}h ${m}m remaining`;
  };

  const sla = slaData || {
    within_sla_count: 912,
    within_sla_pct: 73.1,
    at_risk_count: 224,
    at_risk_pct: 17.9,
    breached_count: 112,
    breached_pct: 9.0,
    escalation_count: 28,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", backgroundColor: "#060911" }}>
      <TopBar
        title="SLA Compliance & Escalation Monitor"
        subtitle="Department Turnaround Time Surveillance"
        breadcrumbs={[{ label: "Operations", href: "/command-center" }, { label: "SLA Monitor" }]}
      />

      <div style={{ padding: "16px 20px", flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* ─── 1. SLA PERFORMANCE KPI CARDS ─────────────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          {/* Healthy */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(34, 197, 94, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#4ade80" }}>WITHIN SLA</span>
              <CheckCircle2 size={16} color="#22c55e" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#22c55e" }}>
              {sla.within_sla_pct}%
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8" }}>
              {sla.within_sla_count.toLocaleString()} cases on schedule
            </div>
          </div>

          {/* At Risk */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(234, 179, 8, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#facc15" }}>AT RISK</span>
              <Clock size={16} color="#eab308" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#eab308" }}>
              {sla.at_risk_pct}%
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8" }}>
              {sla.at_risk_count} approaching deadline (&lt; 2h)
            </div>
          </div>

          {/* Breached */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(239, 68, 68, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#f87171" }}>BREACHED</span>
              <AlertTriangle size={16} color="#ef4444" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#ef4444" }}>
              {sla.breached_pct}%
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8" }}>
              {sla.breached_count} exceeded statutory SLA
            </div>
          </div>

          {/* Escalations */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(168, 85, 247, 0.25)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#c084fc" }}>AUTO-ESCALATED</span>
              <ShieldAlert size={16} color="#a855f7" />
            </div>
            <div style={{ fontSize: "28px", fontWeight: 800, color: "#c084fc" }}>
              {sla.escalation_count}
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8" }}>
              Dispatched to Special Commissioner
            </div>
          </div>
        </div>

        {/* ─── 2. LIVE COUNTDOWN QUEUE (AT RISK & BREACHED) ─────────────────── */}
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
              <Clock size={16} color="#818cf8" />
              <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                CRITICAL SLA WATCHLIST & COUNTDOWNS
              </h3>
            </div>
            <span style={{ fontSize: "11px", color: "#64748b" }}>Auto-prioritized by remaining resolution window</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
            {approachingCases.map((item) => {
              const isBreached = item.minutesRemaining < 0;
              return (
                <div
                  key={item.id}
                  style={{
                    backgroundColor: isBreached ? "rgba(239, 68, 68, 0.08)" : "rgba(234, 179, 8, 0.08)",
                    border: isBreached ? "1px solid rgba(239, 68, 68, 0.3)" : "1px solid rgba(234, 179, 8, 0.3)",
                    borderRadius: "8px",
                    padding: "14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: "#ffffff" }}>
                      {item.code}
                    </span>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        backgroundColor: isBreached ? "rgba(239, 68, 68, 0.2)" : "rgba(234, 179, 8, 0.2)",
                        color: isBreached ? "#f87171" : "#facc15",
                      }}
                    >
                      {formatCountdown(item.minutesRemaining)}
                    </span>
                  </div>

                  <p style={{ fontSize: "12px", color: "#cbd5e1", margin: 0 }}>
                    "{item.text}"
                  </p>

                  <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", justifyContent: "space-between" }}>
                    <span>Dept: <strong>{item.department}</strong></span>
                    <span>Target: <strong>{item.slaHours}h</strong></span>
                  </div>

                  <Link
                    href={`/complaints/${item.id}`}
                    style={{
                      marginTop: "4px",
                      fontSize: "11px",
                      color: "#818cf8",
                      textDecoration: "none",
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <span>Escalate / Expedite</span>
                    <ArrowUpRight size={12} />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>

        {/* ─── 3. DEPARTMENT SLA PERFORMANCE RANKING ────────────────────────── */}
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
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Building size={16} color="#818cf8" />
            <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
              DEPARTMENT SLA PERFORMANCE AUDIT
            </h3>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {[
              { name: "Electricity Distribution Board", active: 32, resolved: 194, rate: 96.8, time: "3.8 hrs", color: "#eab308" },
              { name: "Water Supply Department", active: 78, resolved: 306, rate: 94.2, time: "11.4 hrs", color: "#38bdf8" },
              { name: "Solid Waste Management", active: 46, resolved: 132, rate: 91.5, time: "8.6 hrs", color: "#a855f7" },
              { name: "Drainage & Stormwater Management", active: 38, resolved: 66, rate: 90.0, time: "12.1 hrs", color: "#22c55e" },
              { name: "Roads & Bridges Department", active: 84, resolved: 228, rate: 89.6, time: "18.2 hrs", color: "#fb923c" },
            ].map((dept) => (
              <div
                key={dept.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "10px 14px",
                  backgroundColor: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 255, 255, 0.05)",
                  borderRadius: "8px",
                  gap: "16px",
                }}
              >
                <div style={{ minWidth: "220px" }}>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#ffffff" }}>{dept.name}</div>
                  <div style={{ fontSize: "11px", color: "#64748b" }}>
                    {dept.active} active · {dept.resolved} resolved
                  </div>
                </div>

                <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ flex: 1, height: "6px", backgroundColor: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${dept.rate}%`, height: "100%", backgroundColor: dept.color }} />
                  </div>
                  <span style={{ fontSize: "12px", fontWeight: 700, color: dept.color, minWidth: "45px" }}>
                    {dept.rate}%
                  </span>
                </div>

                <div style={{ textAlign: "right", minWidth: "100px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>Avg Turnaround</div>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "#e2e8f0" }}>{dept.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
