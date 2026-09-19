"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { listCitizenComplaints } from "@/lib/api";
import { Search, Clock, CheckCircle, AlertTriangle, ArrowRight, RefreshCw, FileText, Camera, Mic } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

export default function MyComplaintsPage() {
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await listCitizenComplaints(50);
      setComplaints(res.complaints || []);
    } catch (e) {
      console.warn("Failed to load complaints:", e);
      setComplaints([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filtered = complaints.filter((c) => {
    const matchesSearch =
      c.complaint_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "28px 20px" }}>
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>📋 Citizen Grievance Tracking Portal</h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Real-time tracking of your submitted complaints, municipal field actions, and SLA timelines.
          </p>
        </div>
        <Link href="/report" className="btn btn-primary" style={{ textDecoration: "none", fontSize: 13, padding: "10px 18px" }}>
          + Lodge New Grievance
        </Link>
      </div>

      {/* Filters & Search */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ position: "relative", width: 280 }}>
          <Search size={14} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          <input
            className="input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search complaints..."
            style={{ paddingLeft: 32, fontSize: 12, height: 34 }}
          />
        </div>

        <select className="input" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ width: 150, fontSize: 13 }}>
          <option value="all">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>

        <button onClick={fetchData} className="btn btn-ghost" style={{ padding: "8px 12px" }}>
          <RefreshCw size={14} className={loading ? "spin" : ""} />
        </button>
      </div>

      {/* Complaints List */}
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: 100, borderRadius: 12 }} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div
          style={{
            background: "var(--brand-card)",
            border: "1px solid var(--brand-border)",
            borderRadius: 12,
            padding: 40,
            textAlign: "center",
          }}
        >
          <FileText size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>No complaints found</h3>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
            {searchQuery ? "No grievances match your search criteria." : "You have not lodged any grievances yet."}
          </p>
          <Link href="/report" className="btn btn-primary" style={{ textDecoration: "none", fontSize: 13 }}>
            Lodge a Grievance Now
          </Link>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {filtered.map((c) => (
            <Link
              key={c.id || c.complaint_code}
              href={`/my-complaints/${c.complaint_code}`}
              style={{
                textDecoration: "none",
                display: "block",
                background: "var(--brand-card)",
                border: "1px solid var(--brand-border)",
                borderRadius: 12,
                padding: "16px 20px",
                transition: "all 0.2s ease",
              }}
              className="card-hover"
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8, flexWrap: "wrap", gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 800, color: "var(--accent-indigo)" }}>
                    {c.complaint_code}
                  </span>
                  <span className={`badge badge-${c.priority}`}>{c.priority.toUpperCase()}</span>
                  <span style={{ fontSize: 11, background: "rgba(255,255,255,0.06)", padding: "2px 8px", borderRadius: 4, textTransform: "capitalize", color: "var(--text-secondary)" }}>
                    {c.category}
                  </span>
                  {c.has_media && (
                    <span style={{ fontSize: 11, color: "var(--accent-cyan)", display: "flex", alignItems: "center", gap: 4 }}>
                      <Camera size={12} /> Photo Evidence
                    </span>
                  )}
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                    <Clock size={12} /> {formatRelativeTime(c.created_at)}
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "3px 10px",
                      borderRadius: 20,
                      background: c.status === "resolved" ? "rgba(34,197,94,0.15)" : "rgba(249,115,22,0.15)",
                      color: c.status === "resolved" ? "#22c55e" : "#f97316",
                    }}
                  >
                    {c.status.replace("_", " ").toUpperCase()}
                  </span>
                </div>
              </div>

              <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 10, lineHeight: 1.5 }}>
                "{c.text}"
              </p>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12, borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 8 }}>
                <span style={{ color: "var(--text-muted)" }}>
                  Routed to: <strong style={{ color: "var(--text-primary)" }}>{c.department_name}</strong> · SLA: <strong>{c.expected_sla_hours}h</strong>
                </span>
                <span style={{ color: "var(--accent-indigo)", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>
                  Track Timeline <ArrowRight size={13} />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
