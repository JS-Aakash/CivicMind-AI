"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Search,
  Bell,
  ChevronRight,
} from "lucide-react";
import { CommandPalette } from "./CommandPalette";

interface TopBarProps {
  breadcrumbs?: { label: string; href?: string }[];
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function TopBar({ breadcrumbs, title, subtitle, actions }: TopBarProps) {
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(3);

  return (
    <>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 20px",
          backgroundColor: "#090d16",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          minHeight: "56px",
          gap: "16px",
          zIndex: 40,
        }}
      >
        {/* Left: Title & Breadcrumbs */}
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          {breadcrumbs && breadcrumbs.length > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              {breadcrumbs.map((crumb, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <ChevronRight size={11} color="#64748b" />}
                  {crumb.href ? (
                    <Link
                      href={crumb.href}
                      style={{ fontSize: 11, color: "#94a3b8", textDecoration: "none" }}
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span style={{ fontSize: 11, color: "#cbd5e1" }}>{crumb.label}</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h1 style={{ fontSize: 16, fontWeight: 700, color: "#f8fafc", margin: 0, letterSpacing: "-0.01em" }}>
              {title}
            </h1>
            {subtitle && (
              <span
                style={{
                  fontSize: "11px",
                  color: "#94a3b8",
                  padding: "1px 8px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                }}
              >
                {subtitle}
              </span>
            )}
          </div>
        </div>

        {/* Center: Global Search Bar */}
        <div
          onClick={() => setIsPaletteOpen(true)}
          style={{
            flex: 1,
            maxWidth: "420px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.09)",
            borderRadius: "8px",
            padding: "6px 12px",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Search size={14} color="#818cf8" />
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              Search complaints, incidents, locations...
            </span>
          </div>
          <kbd
            style={{
              fontSize: "10px",
              fontFamily: "monospace",
              color: "#94a3b8",
              backgroundColor: "rgba(255, 255, 255, 0.08)",
              padding: "2px 6px",
              borderRadius: "4px",
              border: "1px solid rgba(255, 255, 255, 0.12)",
            }}
          >
            Ctrl + K
          </kbd>
        </div>

        {/* Right: Actions, Notifications & Officer */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", position: "relative" }}>
          {actions}

          {/* Notification Bell with Interactive Dropdown */}
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setIsNotifOpen((prev) => !prev)}
              style={{
                position: "relative",
                width: "34px",
                height: "34px",
                borderRadius: "6px",
                backgroundColor: isNotifOpen ? "rgba(99, 102, 241, 0.15)" : "rgba(255, 255, 255, 0.04)",
                border: isNotifOpen ? "1px solid rgba(99, 102, 241, 0.4)" : "1px solid rgba(255, 255, 255, 0.08)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                color: isNotifOpen ? "#818cf8" : "#94a3b8",
                transition: "all 0.15s ease",
              }}
              title="Operational Alerts & Live Notifications"
            >
              <Bell size={15} />
              {unreadCount > 0 && (
                <span
                  style={{
                    position: "absolute",
                    top: "3px",
                    right: "3px",
                    minWidth: "14px",
                    height: "14px",
                    padding: "0 3px",
                    borderRadius: "7px",
                    backgroundColor: "#ef4444",
                    color: "#ffffff",
                    fontSize: "9px",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "0 0 6px rgba(239, 68, 68, 0.8)",
                  }}
                >
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Notification Dropdown Panel */}
            {isNotifOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "42px",
                  right: 0,
                  width: "360px",
                  maxHeight: "440px",
                  backgroundColor: "#0d1424",
                  border: "1px solid rgba(99, 102, 241, 0.25)",
                  borderRadius: "10px",
                  boxShadow: "0 12px 36px rgba(0, 0, 0, 0.65), 0 0 16px rgba(99, 102, 241, 0.15)",
                  zIndex: 100,
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden",
                }}
              >
                {/* Header */}
                <div
                  style={{
                    padding: "12px 16px",
                    borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    backgroundColor: "rgba(99, 102, 241, 0.04)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "#f8fafc" }}>
                      Operational Alerts
                    </span>
                    {unreadCount > 0 && (
                      <span
                        style={{
                          fontSize: "10px",
                          padding: "1px 6px",
                          borderRadius: "4px",
                          backgroundColor: "rgba(239, 68, 68, 0.15)",
                          color: "#f87171",
                          fontWeight: 600,
                        }}
                      >
                        {unreadCount} New
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={() => setUnreadCount(0)}
                      style={{
                        background: "none",
                        border: "none",
                        fontSize: "11px",
                        color: "#818cf8",
                        cursor: "pointer",
                        padding: 0,
                        fontWeight: 500,
                      }}
                    >
                      Mark all read
                    </button>
                  )}
                </div>

                {/* Notification List */}
                <div style={{ overflowY: "auto", display: "flex", flexDirection: "column" }}>
                  {[
                    {
                      id: "notif-1",
                      title: "High-Priority Electrical Hazard",
                      desc: "Transformer spark & power fluctuation detected in T. Nagar.",
                      time: "2 mins ago",
                      type: "critical",
                      href: "/incidents",
                    },
                    {
                      id: "notif-2",
                      title: "Emerging Spatio-Temporal Cluster",
                      desc: "8 related sewage overflow complaints in Anna Nagar (Ward 112).",
                      time: "14 mins ago",
                      type: "warning",
                      href: "/incidents",
                    },
                    {
                      id: "notif-3",
                      title: "SLA Escalation Warning",
                      desc: "Water main rupture approaching 2h SLA deadline.",
                      time: "28 mins ago",
                      type: "sla",
                      href: "/sla",
                    },
                    {
                      id: "notif-4",
                      title: "DBSCAN Clustering Recomputed",
                      desc: "Engine updated 14 active incidents across 6 city zones.",
                      time: "1 hour ago",
                      type: "system",
                      href: "/map",
                    },
                  ].map((notif) => (
                    <Link
                      key={notif.id}
                      href={notif.href}
                      onClick={() => setIsNotifOpen(false)}
                      style={{
                        padding: "12px 16px",
                        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                        textDecoration: "none",
                        display: "flex",
                        gap: "10px",
                        alignItems: "flex-start",
                        transition: "background 0.15s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.03)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <div
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          marginTop: "4px",
                          flexShrink: 0,
                          backgroundColor:
                            notif.type === "critical"
                              ? "#ef4444"
                              : notif.type === "warning"
                              ? "#f97316"
                              : notif.type === "sla"
                              ? "#eab308"
                              : "#3b82f6",
                          boxShadow:
                            notif.type === "critical"
                              ? "0 0 6px #ef4444"
                              : "none",
                        }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: "#f1f5f9" }}>
                            {notif.title}
                          </span>
                          <span style={{ fontSize: "10px", color: "#64748b" }}>{notif.time}</span>
                        </div>
                        <p style={{ fontSize: "11px", color: "#94a3b8", margin: "3px 0 0 0", lineHeight: 1.4 }}>
                          {notif.desc}
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>

                {/* Footer Link */}
                <div
                  style={{
                    padding: "8px 16px",
                    backgroundColor: "rgba(0, 0, 0, 0.2)",
                    textAlign: "center",
                    borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                  }}
                >
                  <Link
                    href="/command-center"
                    onClick={() => setIsNotifOpen(false)}
                    style={{ fontSize: "11px", color: "#818cf8", textDecoration: "none", fontWeight: 600 }}
                  >
                    View All in Command Center →
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Officer Profile Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "4px 8px",
              borderRadius: "6px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            <div
              style={{
                width: "24px",
                height: "24px",
                borderRadius: "50%",
                backgroundColor: "#3b82f6",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                fontSize: "10px",
                fontWeight: 700,
              }}
            >
              ADM
            </div>
            <div style={{ display: "flex", flexDirection: "column", textAlign: "left" }}>
              <span style={{ fontSize: "11px", fontWeight: 600, color: "#f1f5f9", lineHeight: 1.1 }}>
                Admin Officer
              </span>
              <span style={{ fontSize: "9px", color: "#64748b" }}>Command Center</span>
            </div>
          </div>
        </div>
      </header>

      {/* Global Command Palette */}
      <CommandPalette isOpen={isPaletteOpen} onClose={() => setIsPaletteOpen(false)} />
    </>
  );
}
