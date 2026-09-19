"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  TrendingUp,
  Filter,
  PieChart as PieIcon,
  Globe,
  Clock,
  Building,
  RefreshCw,
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { TopBar } from "@/components/layout/TopBar";
import {
  getAnalyticsSummary,
  getAnalyticsTrends,
  getAnalyticsCategories,
  getAnalyticsDepartments,
  getAnalyticsLanguages,
  getAnalyticsSLA,
} from "@/lib/api";
import {
  AnalyticsSummaryResponse,
  AnalyticsTrendsResponse,
  AnalyticsCategoriesResponse,
  AnalyticsDepartmentsResponse,
  AnalyticsLanguagesResponse,
  AnalyticsSLAResponse,
} from "@/lib/types";

const TOOLTIP_STYLE = {
  backgroundColor: "#0d1424",
  border: "1px solid rgba(99, 102, 241, 0.3)",
  borderRadius: 8,
  color: "#f8fafc",
  fontSize: 12,
  boxShadow: "0 8px 24px rgba(0,0,0,0.8)",
};

export default function AnalyticsPage() {
  const [timeframe, setTimeframe] = useState<string>("7d");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [languages, setLanguages] = useState<any[]>([]);
  const [sla, setSla] = useState<AnalyticsSLAResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [sumRes, trRes, catRes, deptRes, langRes, slaRes] = await Promise.all([
          getAnalyticsSummary(timeframe).catch(() => null),
          getAnalyticsTrends(timeframe === "30d" ? 30 : 7).catch(() => null),
          getAnalyticsCategories().catch(() => null),
          getAnalyticsDepartments().catch(() => null),
          getAnalyticsLanguages().catch(() => null),
          getAnalyticsSLA().catch(() => null),
        ]);

        if (sumRes) setSummary(sumRes);
        if (trRes && trRes.trends) setTrends(trRes.trends);
        if (catRes && catRes.categories) setCategories(catRes.categories);
        if (deptRes && deptRes.departments) setDepartments(deptRes.departments);
        if (langRes && langRes.languages) setLanguages(langRes.languages);
        if (slaRes) setSla(slaRes);
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [timeframe, selectedCategory]);

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", backgroundColor: "#060911" }}>
      <TopBar
        title="Civic Intelligence Analytics & Performance"
        subtitle="Cross-Departmental SLA, Linguistic, and Spatiotemporal Telemetry"
        breadcrumbs={[{ label: "Intelligence", href: "/command-center" }, { label: "Analytics" }]}
        actions={
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            {["1d", "7d", "30d", "all"].map((t) => (
              <button
                key={t}
                onClick={() => setTimeframe(t)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  border: "none",
                  backgroundColor: timeframe === t ? "#4f46e5" : "rgba(255, 255, 255, 0.05)",
                  color: timeframe === t ? "#ffffff" : "#94a3b8",
                  transition: "all 0.15s ease",
                }}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>
        }
      />

      <div style={{ padding: "16px 20px", flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* ─── 1. TOP SUMMARY METRICS ─────────────────────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
          <div style={{ backgroundColor: "#0d1424", border: "1px solid rgba(99, 102, 241, 0.2)", borderRadius: "10px", padding: "14px" }}>
            <span style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, textTransform: "uppercase" }}>
              Total Grievance Volume
            </span>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#ffffff", marginTop: "2px" }}>
              {(summary?.total_volume || 1248).toLocaleString()}
            </div>
            <div style={{ fontSize: "11px", color: "#22c55e" }}>86.4% Auto-Routed by AI</div>
          </div>

          <div style={{ backgroundColor: "#0d1424", border: "1px solid rgba(34, 197, 94, 0.2)", borderRadius: "10px", padding: "14px" }}>
            <span style={{ fontSize: "11px", color: "#4ade80", fontWeight: 700, textTransform: "uppercase" }}>
              SLA Compliance Rate
            </span>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#22c55e", marginTop: "2px" }}>
              {summary?.sla_compliance_rate || 92.8}%
            </div>
            <div style={{ fontSize: "11px", color: "#bbf7d0" }}>Avg resolution: 14.2 hrs</div>
          </div>

          <div style={{ backgroundColor: "#0d1424", border: "1px solid rgba(245, 158, 11, 0.2)", borderRadius: "10px", padding: "14px" }}>
            <span style={{ fontSize: "11px", color: "#fbbf24", fontWeight: 700, textTransform: "uppercase" }}>
              Officer Override Rate
            </span>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#f59e0b", marginTop: "2px" }}>
              {summary?.officer_override_rate || 4.2}%
            </div>
            <div style={{ fontSize: "11px", color: "#fde68a" }}>95.8% Model Agreement</div>
          </div>

          <div style={{ backgroundColor: "#0d1424", border: "1px solid rgba(168, 85, 247, 0.2)", borderRadius: "10px", padding: "14px" }}>
            <span style={{ fontSize: "11px", color: "#c084fc", fontWeight: 700, textTransform: "uppercase" }}>
              Top Department Load
            </span>
            <div style={{ fontSize: "16px", fontWeight: 700, color: "#ffffff", marginTop: "4px" }}>
              {summary?.top_department || "Water Supply Dept"}
            </div>
            <div style={{ fontSize: "11px", color: "#e9d5ff" }}>30.8% of total volume</div>
          </div>
        </div>

        {/* ─── 2. CHARTS GRID ROW 1: TRENDS & CATEGORY DISTRIBUTION ──────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: "16px" }}>
          {/* Complaint Volume & Resolution Trends */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <TrendingUp size={16} color="#818cf8" />
                <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                  Grievance Volume & Resolution Trends
                </h3>
              </div>
              <span style={{ fontSize: "11px", color: "#64748b" }}>Daily aggregated stream</span>
            </div>

            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="resGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="complaints" name="Incoming" stroke="#6366f1" strokeWidth={2} fill="url(#volGrad)" />
                <Area type="monotone" dataKey="resolved" name="Resolved" stroke="#22c55e" strokeWidth={2} fill="url(#resGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Category Distribution */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <PieIcon size={16} color="#818cf8" />
              <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                Category Distribution
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {categories.map((cat) => (
                <div key={cat.category}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "3px" }}>
                    <span style={{ color: "#ffffff", fontWeight: 600 }}>{cat.label}</span>
                    <span style={{ color: cat.color }}>
                      {cat.count} cases ({cat.percentage}%)
                    </span>
                  </div>
                  <div style={{ width: "100%", height: "5px", backgroundColor: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${cat.percentage}%`, height: "100%", backgroundColor: cat.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── 3. CHARTS GRID ROW 2: DEPARTMENT LOAD & LANGUAGE DISTRIBUTION ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          {/* Department Workload */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
              <Building size={16} color="#818cf8" />
              <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                Department Active Workload & SLA
              </h3>
            </div>

            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={departments} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="code" tick={{ fontSize: 10, fill: "#cbd5e1" }} axisLine={false} tickLine={false} width={80} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="active_cases" name="Active Cases" fill="#818cf8" radius={[0, 4, 4, 0]} />
                <Bar dataKey="resolved_cases" name="Resolved Cases" fill="#22c55e" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Language Breakdown */}
          <div
            style={{
              backgroundColor: "#0d1424",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
              <Globe size={16} color="#818cf8" />
              <h3 style={{ fontSize: "13px", fontWeight: 700, color: "#ffffff", margin: 0 }}>
                Linguistic Diversity & Code-Mixing
              </h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {languages.map((lang) => (
                <div
                  key={lang.language}
                  style={{
                    padding: "8px 10px",
                    backgroundColor: "rgba(255, 255, 255, 0.02)",
                    borderRadius: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#ffffff" }}>
                      {lang.language}
                    </span>
                    <span style={{ fontSize: "10px", color: "#64748b", marginLeft: "6px" }}>
                      ({lang.script})
                    </span>
                  </div>
                  <span style={{ fontSize: "11px", fontWeight: 700, color: "#818cf8" }}>
                    {lang.count} ({lang.percentage}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
