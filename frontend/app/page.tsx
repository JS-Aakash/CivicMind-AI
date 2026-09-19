"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Search,
  FileText,
  Mic,
  Camera,
  MapPin,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  Clock,
  CheckCircle2,
  Lock,
  Building2,
  Globe2,
  ChevronRight,
  Activity,
} from "lucide-react";

export default function CitizenPortalPage() {
  const router = useRouter();
  const [complaintId, setComplaintId] = useState("");
  const [trackError, setTrackError] = useState<string | null>(null);

  const handleTrack = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanId = complaintId.trim().toUpperCase();
    if (!cleanId) {
      setTrackError("Please enter a valid Complaint ID");
      return;
    }
    router.push(`/track/${encodeURIComponent(cleanId)}`);
  };

  const sampleIds = ["CIV-2026-00001", "CIV-2026-00002", "CIV-2026-00003"];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-cyan-500 selection:text-slate-950 font-sans">
      {/* Top Citizen Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-cyan-500/20">
              <Activity size={20} />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                CivicMind AI
              </span>
              <span className="ml-2 text-xs py-0.5 px-2 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">
                Public Portal
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/track"
              className="text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-800/60 transition-colors"
            >
              Track Complaint
            </Link>
            <Link
              href="/report"
              className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-slate-950 bg-gradient-to-r from-cyan-400 to-cyan-500 hover:from-cyan-300 hover:to-cyan-400 px-3.5 py-1.5 rounded-lg shadow-sm transition-all"
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

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 px-4 lg:px-8 border-b border-slate-800/60">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[350px] bg-gradient-to-b from-cyan-500/15 via-blue-600/5 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/80 text-xs font-medium text-cyan-300 mb-6 shadow-sm">
            <Sparkles size={13} className="text-cyan-400" />
            <span>AI-Powered Citizen Grievance Redressal</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight sm:leading-snug mb-4">
            Every Voice. Understood. <br className="hidden sm:block" />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              Prioritized. Resolved.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto mb-8">
            Submit municipal issues in English, தமிழ், or हिंदी with voice, photos, and live GPS.
            Our Multimodal AI automatically triages, routes to officers, and tracks resolution evidence.
          </p>

          {/* Quick Track & Action Bar */}
          <div className="max-w-xl mx-auto bg-slate-900/90 border border-slate-700/80 rounded-2xl p-2.5 shadow-2xl backdrop-blur-xl mb-6">
            <form onSubmit={handleTrack} className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-1">
                <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Enter Complaint ID (e.g. CIV-2026-00001)"
                  value={complaintId}
                  onChange={(e) => {
                    setComplaintId(e.target.value);
                    setTrackError(null);
                  }}
                  className="w-full bg-slate-950/70 border border-slate-700/70 rounded-xl pl-10 pr-3 py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs sm:text-sm px-5 py-2.5 rounded-xl shadow-md transition-all cursor-pointer"
              >
                <span>Track Status</span>
                <ArrowRight size={15} />
              </button>
            </form>

            {trackError && (
              <p className="text-rose-400 text-xs text-left px-3 pt-2">{trackError}</p>
            )}

            <div className="flex flex-wrap items-center gap-2 pt-2.5 px-2 text-xs text-slate-400">
              <span>Try sample IDs:</span>
              {sampleIds.map((id) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => router.push(`/track/${id}`)}
                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 font-mono text-[11px] transition-colors"
                >
                  {id}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap justify-center items-center gap-4">
            <Link
              href="/report"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <FileText size={16} />
              <span>File a New Grievance Now</span>
              <ChevronRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="py-16 px-4 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-100">
            How CivicMind AI Accelerates Municipal Redressal
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Built for transparent governance, verified field resolutions, and multilingual accessibility
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-4">
              <Mic size={20} />
            </div>
            <h3 className="font-semibold text-base text-slate-100 mb-2">Multimodal & Multilingual Input</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Record voice notes in Tamil or Hindi via Whisper STT, capture hazardous street conditions via Qwen2.5-VL vision analysis, and auto-detect exact ward locations.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
              <Sparkles size={20} />
            </div>
            <h3 className="font-semibold text-base text-slate-100 mb-2">9-Stage Verified Lifecycle</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track progress through real lifecycle states: Submitted → AI Analysis → Triaged → Routed → Assigned → In Progress → Field Verification → Resolved → Closed.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
              <CheckCircle2 size={20} />
            </div>
            <h3 className="font-semibold text-base text-slate-100 mb-2">Geofenced Resolution Proof</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Resolutions require verified field photos and resolver GPS checks. Citizens can confirm or reopen unresolved grievances with 1-click feedback.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-8 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-cyan-500/20 flex items-center justify-center text-cyan-400 text-xs font-bold">
              CM
            </div>
            <span>CivicMind AI — Intelligent Civic Redressal Platform</span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <Link href="/report" className="hover:text-slate-300">File Grievance</Link>
            <Link href="/track" className="hover:text-slate-300">Track Status</Link>
            <Link href="/admin/login" className="hover:text-cyan-400">Admin Console</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
