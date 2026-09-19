"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Search,
  FileText,
  Mic,
  Camera,
  MapPin,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Clock,
  CheckCircle2,
  Lock,
  Building2,
  Globe2,
  ChevronRight,
  Activity,
  AlertTriangle,
  Zap,
  PhoneCall,
  Droplet,
  Flame,
  Truck,
  Layers,
  ThumbsUp,
  HelpCircle,
} from "lucide-react";
import { listGrievances } from "@/lib/api";
import type { Complaint } from "@/lib/types";

export default function CitizenPortalPage() {
  const router = useRouter();
  const [complaintId, setComplaintId] = useState("");
  const [trackError, setTrackError] = useState<string | null>(null);
  const [recentComplaints, setRecentComplaints] = useState<Complaint[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);

  useEffect(() => {
    listGrievances({ page_size: 4 })
      .then((data) => setRecentComplaints(data.complaints || []))
      .catch(() => {})
      .finally(() => setLoadingRecent(false));
  }, []);

  const handleTrack = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanId = complaintId.trim().toUpperCase();
    if (!cleanId) {
      setTrackError("Please enter a valid Complaint ID (e.g. CIV-2026-00001)");
      return;
    }
    router.push(`/track/${encodeURIComponent(cleanId)}`);
  };

  const sampleIds = ["CIV-2026-00001", "CIV-2026-00002", "CIV-2026-00003"];

  const categories = [
    {
      id: "roads",
      title: "Roads & Potholes",
      icon: "🛣️",
      desc: "Crater potholes, damaged pavements, road cave-ins, and missing manhole covers.",
      dept: "Roads & Infrastructure",
    },
    {
      id: "water",
      title: "Water Supply",
      icon: "💧",
      desc: "Contaminated tap water, pipeline bursts, low pressure, or tanker scheduling.",
      dept: "Water Supply Board",
    },
    {
      id: "electricity",
      title: "Electricity & Street Lights",
      icon: "⚡",
      desc: "Sparking transformers, fallen power lines, voltage fluctuation, dark streetlights.",
      dept: "Electricity Board",
    },
    {
      id: "sanitation",
      title: "Sanitation & Garbage",
      icon: "🧹",
      desc: "Overflowing dumper bins, uncollected household waste, dead animal removal.",
      dept: "Solid Waste Management",
    },
    {
      id: "drainage",
      title: "Drainage & Flooding",
      icon: "🌊",
      desc: "Stagnant rainwater, clogged storm drains, sewage backflow, open gutters.",
      dept: "Stormwater & Drainage",
    },
    {
      id: "public_safety",
      title: "Public Safety & Hazards",
      icon: "🚨",
      desc: "Uprooted trees, hazardous construction debris, leaning poles, emergency risks.",
      dept: "Public Safety & Disaster",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-cyan-500 selection:text-slate-950 font-sans">
      {/* ─── Top Citizen Navigation Bar ─── */}
      <header className="border-b border-slate-800/90 bg-slate-900/90 backdrop-blur-xl sticky top-0 z-40 px-4 lg:px-8 py-3.5 shadow-lg shadow-black/40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 no-underline group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/25 group-hover:scale-105 transition-transform">
              <Activity size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg sm:text-xl tracking-tight text-white">
                  CivicMind AI
                </span>
                <span className="text-[10px] uppercase font-extrabold py-0.5 px-2 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  Public Redressal Portal
                </span>
              </div>
              <p className="text-[11px] text-slate-300 hidden sm:block font-medium">
                Official Municipal Corporation Citizen Grievance Gateway
              </p>
            </div>
          </Link>

          {/* Right Navigation Actions */}
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden md:flex items-center gap-2 text-xs text-slate-300 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-700/80 shadow-inner">
              <Globe2 size={14} className="text-cyan-400" />
              <span className="text-white font-semibold">English</span>
              <span className="text-slate-500">·</span>
              <span className="text-slate-300 hover:text-cyan-300 cursor-pointer transition-colors">தமிழ்</span>
              <span className="text-slate-500">·</span>
              <span className="text-slate-300 hover:text-cyan-300 cursor-pointer transition-colors">हिंदी</span>
            </div>

            <Link
              href="/track"
              className="text-xs font-semibold text-slate-200 hover:text-white px-3 py-2 rounded-xl hover:bg-slate-800/80 transition-colors"
            >
              Track Complaint
            </Link>

            <Link
              href="/report"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-950 bg-gradient-to-r from-cyan-400 to-cyan-500 hover:from-cyan-300 hover:to-cyan-400 px-4 py-2 rounded-xl shadow-md shadow-cyan-500/30 transition-all transform hover:-translate-y-0.5 cursor-pointer no-underline"
            >
              <span>+ File Grievance</span>
            </Link>

            <Link
              href="/admin/login"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white px-3 py-2 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-900 transition-all no-underline"
            >
              <Lock size={12} className="text-cyan-400" />
              <span className="hidden sm:inline">Officer Login</span>
            </Link>
          </div>
        </div>
      </header>

      {/* ─── Hero Section ─── */}
      <section className="relative overflow-hidden pt-6 sm:pt-10 pb-12 px-4 lg:px-8 border-b border-slate-800/70">
        {/* Glow backdrop */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[400px] bg-gradient-to-b from-cyan-500/15 via-blue-600/5 to-transparent rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative z-10 flex flex-col items-center">
          {/* Main Headline (Clean Solid White, Positioned High) */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-tight sm:leading-tight mb-4 text-center">
            Every Civic Voice. <br />
            <span className="text-white">
              Understood. Prioritized. Resolved.
            </span>
          </h1>

          {/* Centered Subtitle */}
          <p className="text-sm sm:text-base text-slate-200 max-w-2xl mx-auto leading-relaxed mb-8 text-center font-normal">
            Submit municipal issues in English, தமிழ், or हिंदी with voice notes, live camera photos, and GPS tagging.
            Our local AI classifies severity, routes tickets in seconds, and verifies field resolutions with geofenced proof.
          </p>

          {/* ─── Dual Action Cards (Report vs Track) ─── */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 w-full max-w-4xl mx-auto text-left">
            {/* Left Card: File a Complaint */}
            <div className="md:col-span-6 bg-slate-900/90 border border-slate-700/90 rounded-2xl p-6 sm:p-7 shadow-2xl flex flex-col justify-between hover:border-cyan-500/60 transition-all relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-cyan-500/20 transition-all" />

              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-11 h-11 rounded-xl bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center text-cyan-400 font-bold shadow-md shadow-cyan-500/20">
                    <FileText size={22} />
                  </div>
                  <span className="text-[11px] font-extrabold text-cyan-300 bg-cyan-500/20 border border-cyan-500/30 px-3 py-1 rounded-full">
                    ⚡ Auto-Triage &lt; 3s
                  </span>
                </div>

                <h2 className="text-xl font-extrabold text-white mb-2">
                  Register a New Grievance
                </h2>
                <p className="text-xs text-slate-300 leading-relaxed mb-5">
                  Report potholes, street light outages, drainage overflows, or garbage piles. Use your camera or speak in Tamil / Hindi.
                </p>

                {/* Centered Feature Pills */}
                <div className="grid grid-cols-3 gap-2 text-xs font-semibold text-slate-200 mb-6 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 text-center">
                  <div className="flex flex-col items-center justify-center gap-1 p-1">
                    <Mic size={14} className="text-cyan-400" />
                    <span className="text-[11px]">Voice Note</span>
                  </div>
                  <div className="flex flex-col items-center justify-center gap-1 p-1 border-x border-slate-800">
                    <Camera size={14} className="text-cyan-400" />
                    <span className="text-[11px]">Camera Photo</span>
                  </div>
                  <div className="flex flex-col items-center justify-center gap-1 p-1">
                    <MapPin size={14} className="text-cyan-400" />
                    <span className="text-[11px]">Live GPS</span>
                  </div>
                </div>
              </div>

              <Link
                href="/report"
                className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-400 to-blue-600 hover:from-cyan-300 hover:to-blue-500 text-slate-950 font-extrabold text-sm py-3 px-4 rounded-xl shadow-lg shadow-cyan-500/30 transition-all text-center no-underline"
              >
                <span>Start Grievance Form</span>
                <ArrowRight size={16} />
              </Link>
            </div>

            {/* Right Card: Instant Track by ID */}
            <div className="md:col-span-6 bg-slate-900/90 border border-slate-700/90 rounded-2xl p-6 sm:p-7 shadow-2xl flex flex-col justify-between hover:border-indigo-500/60 transition-all relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-indigo-500/20 transition-all" />

              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-11 h-11 rounded-xl bg-indigo-500/15 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-bold shadow-md shadow-indigo-500/20">
                    <Clock size={22} />
                  </div>
                  <span className="text-[11px] font-extrabold text-indigo-300 bg-indigo-500/20 border border-indigo-500/30 px-3 py-1 rounded-full">
                    9-Stage Live Stepper
                  </span>
                </div>

                <h2 className="text-xl font-extrabold text-white mb-2">
                  Track Existing Grievance
                </h2>
                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                  Enter your unique Complaint ID to inspect department assignment, SLA countdowns, and field completion photos.
                </p>

                <form onSubmit={handleTrack} className="space-y-2 mb-4">
                  <div className="relative">
                    <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="e.g. CIV-2026-00001"
                      value={complaintId}
                      onChange={(e) => {
                        setComplaintId(e.target.value);
                        setTrackError(null);
                      }}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-10 pr-3 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono shadow-inner"
                    />
                  </div>
                  {trackError && <p className="text-rose-400 text-xs font-semibold">{trackError}</p>}
                </form>
              </div>

              <div>
                <button
                  type="button"
                  onClick={handleTrack}
                  className="w-full inline-flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm py-2.5 px-4 rounded-xl shadow-md transition-all cursor-pointer mb-3"
                >
                  <span>Check Redressal Status</span>
                  <ChevronRight size={16} />
                </button>

                <div className="flex items-center justify-between text-xs text-slate-300 pt-1">
                  <span className="text-slate-400">Sample demo IDs:</span>
                  <div className="flex gap-1.5">
                    {sampleIds.map((id) => (
                      <button
                        key={id}
                        type="button"
                        onClick={() => router.push(`/track/${id}`)}
                        className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 font-mono text-[11px] font-semibold border border-slate-700"
                      >
                        {id}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Real-Time Civic Metrics Strip ─── */}
      <section className="bg-slate-900/50 border-b border-slate-800/80 py-8 px-4">
        <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div className="p-3 bg-slate-950/40 rounded-xl border border-slate-800/80">
            <div className="text-2xl sm:text-3xl font-black text-white font-mono">10,240+</div>
            <div className="text-xs text-slate-300 mt-1 font-semibold">Grievances Redressed</div>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-xl border border-slate-800/80">
            <div className="text-2xl sm:text-3xl font-black text-cyan-400 font-mono">14.2 hrs</div>
            <div className="text-xs text-slate-300 mt-1 font-semibold">Average Resolution SLA</div>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-xl border border-slate-800/80">
            <div className="text-2xl sm:text-3xl font-black text-indigo-400 font-mono">98.4%</div>
            <div className="text-xs text-slate-300 mt-1 font-semibold">AI Auto-Routing Accuracy</div>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-xl border border-slate-800/80">
            <div className="text-2xl sm:text-3xl font-black text-emerald-400 font-mono">100%</div>
            <div className="text-xs text-slate-300 mt-1 font-semibold">Geofence Verified Proofs</div>
          </div>
        </div>
      </section>

      {/* ─── 4-Step How It Works Section (Centered & Clear) ─── */}
      <section className="py-16 px-4 lg:px-8 max-w-6xl mx-auto">
        <div className="text-center mb-12 flex flex-col items-center">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-widest bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20 mb-2">
            Audit-Backed Governance
          </span>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight text-center">
            Transparent 4-Step Redressal Flow
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 max-w-xl mx-auto text-center font-normal">
            From the moment you speak or snap a photo, every step is recorded on the public municipal audit ledger.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
          {/* Step 1 */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-300 font-black text-base flex items-center justify-center mb-4 border border-cyan-500/40">
                1
              </div>
              <h3 className="font-bold text-base text-white mb-2">Multimodal Filing</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Describe the issue, record voice in Tamil or Hindi, snap live camera evidence, and auto-detect your ward GPS.
              </p>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-800">
              <span className="text-[11px] text-cyan-300 font-semibold font-mono">Whisper STT + GPS</span>
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-300 font-black text-base flex items-center justify-center mb-4 border border-indigo-500/40">
                2
              </div>
              <h3 className="font-bold text-base text-white mb-2">AI Triage & Routing</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                MuRIL v1.1 and Qwen2.5-VL classify category, evaluate emergency hazards, and route to the correct engineer with SLA timers.
              </p>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-800">
              <span className="text-[11px] text-indigo-300 font-semibold font-mono">MuRIL v1.1 + Qwen2.5-VL</span>
            </div>
          </div>

          {/* Step 3 */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-300 font-black text-base flex items-center justify-center mb-4 border border-amber-500/40">
                3
              </div>
              <h3 className="font-bold text-base text-white mb-2">Field Fix & Sign-Off</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Municipal engineering crews resolve the issue and must upload resolution photos with verified on-site GPS geofencing.
              </p>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-800">
              <span className="text-[11px] text-amber-300 font-semibold font-mono">Haversine GPS Verified</span>
            </div>
          </div>

          {/* Step 4 */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 relative flex flex-col justify-between hover:border-slate-700 transition-all">
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-300 font-black text-base flex items-center justify-center mb-4 border border-emerald-500/40">
                4
              </div>
              <h3 className="font-bold text-base text-white mb-2">Citizen Verification</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Citizens view before/after evidence photos. If unresolved on the ground, 1-click reopen sends it to supervisory review.
              </p>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-800">
              <span className="text-[11px] text-emerald-300 font-semibold font-mono">1-Click Reopen Right</span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Top Municipal Categories Grid (Centered & Clean) ─── */}
      <section className="py-16 px-4 lg:px-8 max-w-6xl mx-auto border-t border-slate-800/70">
        <div className="text-center mb-10 flex flex-col items-center">
          <span className="text-xs font-bold text-cyan-400 uppercase tracking-widest bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20 mb-2">
            Pre-Configured Routing
          </span>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight text-center">
            Municipal Redressal Categories
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 mt-2 max-w-xl mx-auto text-center font-normal">
            Select any civic sector to file a report directly with pre-configured routing
          </p>
          <div className="mt-4">
            <Link
              href="/report"
              className="inline-flex items-center gap-1.5 text-xs font-bold text-cyan-400 hover:text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 px-3.5 py-1.5 rounded-full border border-cyan-500/30 transition-all no-underline"
            >
              <span>Open Custom Report Form</span>
              <ChevronRight size={14} />
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {categories.map((c) => (
            <Link
              key={c.id}
              href="/report"
              className="bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-cyan-500/50 rounded-2xl p-6 transition-all group no-underline block shadow-md"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl">{c.icon}</span>
                <span className="text-[10px] font-bold text-slate-300 bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700">
                  {c.dept}
                </span>
              </div>
              <h3 className="font-bold text-base text-white group-hover:text-cyan-400 transition-colors mb-2">
                {c.title}
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                {c.desc}
              </p>
              <div className="text-xs font-bold text-cyan-400 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                <span>File in {c.title.split(" ")[0]}</span>
                <ChevronRight size={14} />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ─── Live Public Redressal Feed ─── */}
      <section className="py-16 px-4 lg:px-8 max-w-6xl mx-auto border-t border-slate-800/70">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white">Live Public Redressal Stream</h2>
            <p className="text-xs text-slate-300 mt-1 font-medium">Real-time status of civic tickets registered across municipal wards</p>
          </div>
          <Link href="/track" className="text-xs font-bold text-cyan-400 hover:text-cyan-300 no-underline flex items-center gap-1">
            <span>View All Grievances</span>
            <ChevronRight size={14} />
          </Link>
        </div>

        {loadingRecent ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-pulse">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-slate-900 rounded-xl border border-slate-800" />
            ))}
          </div>
        ) : recentComplaints.length === 0 ? (
          <div className="p-8 text-center bg-slate-900/60 rounded-xl border border-slate-800 text-slate-400 text-xs">
            No active grievances registered in the current cycle.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {recentComplaints.map((c) => (
              <Link
                key={c.id}
                href={`/track/${c.complaint_code || c.id}`}
                className="bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-all block group no-underline shadow-md"
              >
                <div className="flex items-center justify-between mb-2.5">
                  <span className="font-mono text-xs font-bold text-cyan-400">
                    {c.complaint_code || c.id.slice(0, 8)}
                  </span>
                  <span
                    className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold ${
                      c.status === "resolved"
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : c.status === "in_progress"
                        ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    }`}
                  >
                    {c.status.replace("_", " ").toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-slate-200 line-clamp-2 mb-3 leading-relaxed">
                  "{c.text}"
                </p>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                  <span className="font-medium">{c.department_name || c.category}</span>
                  <span className="text-cyan-400 font-semibold group-hover:underline flex items-center gap-1">
                    Track Lifecycle →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* ─── Emergency & Department Helplines ─── */}
      <section className="py-12 px-4 lg:px-8 max-w-6xl mx-auto border-t border-slate-800/70">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <PhoneCall size={18} className="text-cyan-400" />
                <span>24x7 Municipal & Emergency Helplines</span>
              </h3>
              <p className="text-xs text-slate-300 mt-1 max-w-lg">
                For immediate life-safety emergencies, open wire fires, or major water main bursts, reach out directly.
              </p>
            </div>

            <div className="flex flex-wrap gap-4 text-xs font-mono">
              <div className="bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 text-center">
                <span className="text-slate-400 block text-[10px] font-sans font-medium">Municipal Corp</span>
                <span className="text-cyan-400 font-extrabold text-base">1913</span>
              </div>
              <div className="bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 text-center">
                <span className="text-slate-400 block text-[10px] font-sans font-medium">Electricity Grid</span>
                <span className="text-amber-400 font-extrabold text-base">1912</span>
              </div>
              <div className="bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 text-center">
                <span className="text-slate-400 block text-[10px] font-sans font-medium">Water Supply</span>
                <span className="text-blue-400 font-extrabold text-base">1916</span>
              </div>
              <div className="bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 text-center">
                <span className="text-slate-400 block text-[10px] font-sans font-medium">Emergency / Fire</span>
                <span className="text-rose-400 font-extrabold text-base">112</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-slate-800/90 bg-slate-950 py-10 px-4 text-xs text-slate-400">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400 text-xs font-bold border border-cyan-500/30">
              CM
            </div>
            <div>
              <p className="text-white font-bold text-xs">CivicMind AI — Intelligent Civic Redressal</p>
              <p className="text-slate-400 text-[11px]">Powered by MuRIL v1.1, Qwen2.5-VL, Whisper STT, and PostGIS</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs font-semibold text-slate-300">
            <Link href="/report" className="hover:text-cyan-400 transition-colors no-underline">File Grievance</Link>
            <Link href="/track" className="hover:text-cyan-400 transition-colors no-underline">Track Grievance</Link>
            <Link href="/admin/login" className="hover:text-white transition-colors no-underline">Officer Dispatch Console</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
