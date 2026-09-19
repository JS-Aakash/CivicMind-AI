"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Search, Activity, ArrowRight, ShieldCheck, Clock, FileText, CheckCircle2, Lock } from "lucide-react";
import { listGrievances } from "@/lib/api";
import type { Complaint } from "@/lib/types";

export default function TrackSearchPage() {
  const router = useRouter();
  const [complaintId, setComplaintId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [recentComplaints, setRecentComplaints] = useState<Complaint[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);

  useEffect(() => {
    listGrievances({ page_size: 6 })
      .then((data) => {
        setRecentComplaints(data.complaints || []);
      })
      .catch(() => {})
      .finally(() => setLoadingRecent(false));
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanId = complaintId.trim().toUpperCase();
    if (!cleanId) {
      setError("Please enter a valid Complaint ID (e.g. CIV-2026-00001)");
      return;
    }
    router.push(`/track/${encodeURIComponent(cleanId)}`);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 no-underline">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-cyan-500/20">
              <Activity size={20} />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                CivicMind AI
              </span>
              <span className="ml-2 text-xs py-0.5 px-2 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">
                Public Tracker
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/report"
              className="text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-cyan-500 hover:from-cyan-300 hover:to-cyan-400 px-3.5 py-1.5 rounded-lg shadow-sm transition-all"
            >
              + File Grievance
            </Link>
            <Link
              href="/admin/login"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/80 transition-all"
            >
              <Lock size={12} />
              <span>Officer Login</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Track Grievance Status</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-2">
            Enter your unique Complaint ID to check real-time progress, assigned officers, and resolution proofs.
          </p>
        </div>

        {/* Search Bar */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl backdrop-blur-xl mb-12">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={complaintId}
                onChange={(e) => {
                  setComplaintId(e.target.value);
                  setError(null);
                }}
                placeholder="Enter Complaint ID (e.g. CIV-2026-00001)"
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-11 pr-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 shadow-inner"
              />
            </div>
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-md transition-all cursor-pointer"
            >
              <span>Track Redressal</span>
              <ArrowRight size={16} />
            </button>
          </form>

          {error && <p className="text-rose-400 text-xs px-3 pt-2">{error}</p>}
        </div>

        {/* Recent Public Grievances */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Recent Public Grievances
          </h2>

          {loadingRecent ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-pulse">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-28 bg-slate-900/60 rounded-xl border border-slate-800" />
              ))}
            </div>
          ) : recentComplaints.length === 0 ? (
            <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-500 text-xs">
              No recent complaints registered yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {recentComplaints.map((c) => (
                <Link
                  key={c.id}
                  href={`/track/${c.complaint_code || c.id}`}
                  className="bg-slate-900/70 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 rounded-xl p-4 transition-all block group no-underline"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-semibold text-cyan-400">
                      {c.complaint_code || c.id.slice(0, 8)}
                    </span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                        c.status === "resolved"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : c.status === "in_progress"
                          ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {c.status.replace("_", " ").toUpperCase()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2 mb-3">
                    {c.text}
                  </p>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
                    <span>{c.department_name || c.category || "General"}</span>
                    <span className="group-hover:text-cyan-400 transition-colors flex items-center gap-1">
                      View Timeline →
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
