"use client";

import React, { useState, useEffect } from "react";
import { MessageSquare, Search, Filter, SlidersHorizontal } from "lucide-react";
import { ComplaintCard } from "@/components/ComplaintCard";
import { listGrievances } from "@/lib/api";
import type { Complaint } from "@/lib/types";
import { CATEGORIES, PRIORITIES } from "@/lib/constants";

const CATEGORY_OPTS = [
  { value: "", label: "All Categories" },
  ...Object.entries(CATEGORIES).map(([v, c]) => ({ value: v, label: c.label })),
];

const PRIORITY_OPTS = [
  { value: "", label: "All Priorities" },
  ...Object.entries(PRIORITIES).map(([v, c]) => ({ value: v, label: c.label })),
];

const STATUS_OPTS = [
  { value: "", label: "All Statuses" },
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "pending", label: "Pending" },
  { value: "resolved", label: "Resolved" },
];

export default function ComplaintsPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const data = await listGrievances({
          page,
          page_size: 12,
          category: category || undefined,
          priority: priority || undefined,
          status: status || undefined,
        });
        setComplaints(data.complaints);
        setTotal(data.total);
      } catch {
        setComplaints([]);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [category, priority, status, page]);

  const filteredComplaints = complaints.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.complaint_code && c.complaint_code.toLowerCase().includes(q)) ||
      (c.text && c.text.toLowerCase().includes(q)) ||
      (c.category && c.category.toLowerCase().includes(q)) ||
      (c.location_text && c.location_text.toLowerCase().includes(q))
    );
  });

  return (
    <div>
      <div className="top-bar">
        <div>
          <h2 style={{ fontSize: 15, fontWeight: 600 }}>Complaints</h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {total} total complaints
          </p>
        </div>
        <a href="/report" className="btn btn-primary" style={{ fontSize: 13 }}>
          + Submit Complaint
        </a>
      </div>

      <div className="page-container" style={{ paddingTop: 20 }}>
        {/* Filters */}
        <div
          style={{
            display: "flex",
            gap: 10,
            marginBottom: 20,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <div style={{ position: "relative", width: 220 }}>
            <Search size={14} color="var(--text-muted)" style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)" }} />
            <input
              className="input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search complaints..."
              style={{ width: "100%", paddingLeft: 30, fontSize: 13 }}
            />
          </div>
          {[
            { value: category, onChange: setCategory, options: CATEGORY_OPTS },
            { value: priority, onChange: setPriority, options: PRIORITY_OPTS },
            { value: status, onChange: setStatus, options: STATUS_OPTS },
          ].map((filter, i) => (
            <select
              key={i}
              value={filter.value}
              onChange={(e) => { filter.onChange(e.target.value); setPage(1); }}
              className="input"
              style={{ width: 150, cursor: "pointer", fontSize: 13 }}
            >
              {filter.options.map((opt) => (
                <option key={opt.value} value={opt.value} style={{ background: "#1e2640" }}>
                  {opt.label}
                </option>
              ))}
            </select>
          ))}
        </div>

        {/* Grid */}
        {loading ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
            {[...Array(8)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 160, borderRadius: 12 }} />
            ))}
          </div>
        ) : filteredComplaints.length > 0 ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
              {filteredComplaints.map((c) => <ComplaintCard key={c.id} complaint={c} />)}
            </div>
            {/* Pagination */}
            <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 24 }}>
              <button
                className="btn btn-secondary"
                style={{ fontSize: 13 }}
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                ← Previous
              </button>
              <span style={{ padding: "8px 16px", fontSize: 13, color: "var(--text-secondary)" }}>
                Page {page}
              </span>
              <button
                className="btn btn-secondary"
                style={{ fontSize: 13 }}
                disabled={complaints.length < 12}
                onClick={() => setPage(page + 1)}
              >
                Next →
              </button>
            </div>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "64px 24px", color: "var(--text-muted)" }}>
            <MessageSquare size={40} style={{ margin: "0 auto 16px", opacity: 0.3 }} />
            <p>No complaints found</p>
          </div>
        )}
      </div>
    </div>
  );
}
