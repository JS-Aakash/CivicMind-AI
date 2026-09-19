"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Map,
  MessageSquare,
  AlertTriangle,
  ShieldCheck,
  Clock,
  BarChart3,
  Brain,
  Cpu,
  TrendingUp,
  History,
  ChevronLeft,
  ChevronRight,
  Activity,
} from "lucide-react";
import { clearAuthSession } from "@/lib/auth";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
}

const SECTIONS: { label: string; items: NavItem[] }[] = [
  {
    label: "OVERVIEW",
    items: [
      { href: "/command-center", label: "Command Center", icon: LayoutDashboard },
      { href: "/map", label: "Live City Map", icon: Map },
    ],
  },
  {
    label: "OPERATIONS",
    items: [
      { href: "/complaints", label: "Complaints", icon: MessageSquare },
      { href: "/incidents", label: "Incidents", icon: AlertTriangle },
      { href: "/review", label: "Human Review", icon: ShieldCheck },
      { href: "/sla", label: "SLA Monitor", icon: Clock },
    ],
  },
  {
    label: "INTELLIGENCE",
    items: [
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/ai-insights", label: "AI Insights", icon: Brain },
      { href: "/model-health", label: "Model Health", icon: Cpu },
    ],
  },
  {
    label: "SYSTEM",
    items: [
      { href: "/feedback", label: "Feedback Loop", icon: TrendingUp },
      { href: "/audit", label: "Audit Log", icon: History },
    ],
  },
];

interface SidebarProps {
  collapsed?: boolean;
  setCollapsed?: (collapsed: boolean) => void;
}

export function Sidebar({ collapsed: propCollapsed, setCollapsed: propSetCollapsed }: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const collapsed = propCollapsed !== undefined ? propCollapsed : internalCollapsed;
  const setCollapsed = propSetCollapsed || setInternalCollapsed;
  const pathname = usePathname();

  const handleLogout = () => {
    clearAuthSession();
    window.location.href = "/admin/login";
  };

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Logo Header */}
      <div className="sidebar-logo" style={{ padding: "16px 14px", borderBottom: "1px solid var(--brand-border)" }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "linear-gradient(135deg, #4f46e5, #06b6d4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "0 0 10px rgba(79, 70, 229, 0.3)",
          }}
        >
          <Activity size={18} color="#ffffff" strokeWidth={2.5} />
        </div>
        {!collapsed && (
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: "#f8fafc", lineHeight: 1.2, letterSpacing: "-0.01em" }}>
              CivicMind AI
            </div>
            <div style={{ fontSize: 10, color: "#64748b", letterSpacing: "0.04em", fontWeight: 500 }}>
              Command Center
            </div>
          </div>
        )}
      </div>

      {/* Persistent Test Complaint Button for Admin */}
      <div style={{ padding: "10px 8px 6px 8px" }}>
        <Link
          href="/report"
          className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-md shadow-cyan-500/20 transition-all text-center no-underline"
          title="Submit Test Complaint"
        >
          <span style={{ fontSize: "14px", lineHeight: 1 }}>+</span>
          {!collapsed && <span>Submit Test Complaint</span>}
        </Link>
      </div>

      {/* Navigation Sections */}
      <nav style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "10px 8px" }}>
        {SECTIONS.map((section) => (
          <div key={section.label} style={{ marginBottom: "14px" }}>
            {!collapsed && (
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  color: "#475569",
                  letterSpacing: "0.08em",
                  padding: "4px 10px 6px 10px",
                }}
              >
                {section.label}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              const active =
                pathname === item.href ||
                pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`sidebar-item ${active ? "active" : ""}`}
                  title={collapsed ? item.label : undefined}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "8px 10px",
                    borderRadius: "8px",
                    marginBottom: "2px",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <Icon size={17} strokeWidth={2} />
                    {!collapsed && (
                      <span style={{ fontSize: "13px", fontWeight: active ? 600 : 400 }}>
                        {item.label}
                      </span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Links & Logout */}
      <div style={{ padding: "10px 8px", borderTop: "1px solid var(--brand-border)" }}>
        <Link
          href="/"
          className="sidebar-item"
          style={{
            display: "flex",
            alignItems: "center",
            padding: "8px 10px",
            borderRadius: "8px",
            fontSize: "12px",
            color: "#94a3b8",
            marginBottom: "4px",
            textDecoration: "none",
          }}
          title="Citizen Portal"
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: 14 }}>🏛️</span>
            {!collapsed && <span>Citizen Portal</span>}
          </div>
        </Link>
        <button
          onClick={handleLogout}
          className="sidebar-item"
          style={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            padding: "8px 10px",
            borderRadius: "8px",
            fontSize: "12px",
            color: "#f87171",
            background: "transparent",
            border: "none",
            cursor: "pointer",
            textAlign: "left",
          }}
          title="Sign Out"
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: 14 }}>🚪</span>
            {!collapsed && <span>Sign Out</span>}
          </div>
        </button>
      </div>

      {/* Collapse toggle button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        style={{
          position: "absolute",
          right: -12,
          top: "45px",
          width: 24,
          height: 24,
          borderRadius: "50%",
          background: "#1e293b",
          border: "1px solid #334155",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          zIndex: 50,
          color: "#94a3b8",
          boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
        }}
        aria-label="Toggle sidebar"
      >
        {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
      </button>
    </aside>
  );
}
