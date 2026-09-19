"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  Map,
  MessageSquare,
  AlertTriangle,
  BarChart3,
  Brain,
  ShieldCheck,
  Clock,
  History,
  TrendingUp,
  Cpu,
  Settings,
  Sparkles,
  ArrowRight,
  X,
} from "lucide-react";

interface PaletteItem {
  id: string;
  title: string;
  category: "Navigation" | "Operations" | "Intelligence" | "System" | "Demo";
  icon: React.ComponentType<{ size?: number; className?: string }>;
  href: string;
  shortcut?: string;
  description?: string;
}

const PALETTE_ITEMS: PaletteItem[] = [
  {
    id: "nav-cc",
    title: "Command Center",
    category: "Navigation",
    icon: LayoutDashboard,
    href: "/command-center",
    shortcut: "G C",
    description: "Flagship real-time civic operations center & live map",
  },
  {
    id: "nav-map",
    title: "Live City Map",
    category: "Navigation",
    icon: Map,
    href: "/map",
    shortcut: "G M",
    description: "Interactive spatiotemporal complaint & incident GIS layers",
  },
  {
    id: "nav-complaints",
    title: "All Complaints",
    category: "Operations",
    icon: MessageSquare,
    href: "/complaints",
    description: "Search, filter, and inspect incoming citizen grievances",
  },
  {
    id: "nav-incidents",
    title: "Active Incidents",
    category: "Operations",
    icon: AlertTriangle,
    href: "/incidents",
    description: "DBSCAN spatiotemporal clusters and emerging patterns",
  },
  {
    id: "nav-review",
    title: "Human Review Queue",
    category: "Operations",
    icon: ShieldCheck,
    href: "/review",
    description: "Officer verification & override workflow for ambiguous cases",
  },
  {
    id: "nav-sla",
    title: "SLA Monitor & Queue",
    category: "Operations",
    icon: Clock,
    href: "/sla",
    description: "Countdowns, at-risk escalations, and department compliance",
  },
  {
    id: "nav-analytics",
    title: "Analytics & Reports",
    category: "Intelligence",
    icon: BarChart3,
    href: "/analytics",
    description: "Volume trends, department loads, and language distributions",
  },
  {
    id: "nav-insights",
    title: "AI Insights & Explanations",
    category: "Intelligence",
    icon: Brain,
    href: "/ai-insights",
    description: "Neural explainability, category probability & calibration",
  },
  {
    id: "nav-feedback",
    title: "Feedback & Continuous Learning",
    category: "System",
    icon: TrendingUp,
    href: "/feedback",
    description: "Officer corrections dataset and model calibration metrics",
  },
  {
    id: "nav-audit",
    title: "Governance Audit Log",
    category: "System",
    icon: History,
    href: "/audit",
    description: "Tamper-evident log of AI decisions and officer overrides",
  },
  {
    id: "nav-health",
    title: "Model & System Health",
    category: "System",
    icon: Cpu,
    href: "/model-health",
    description: "MuRIL v1.1, Whisper, Qwen3-VL 4B, and pgvector statuses",
  },
];


export function CommandPalette({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  const filteredItems = PALETTE_ITEMS.filter((item) => {
    const q = query.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      (item.description && item.description.toLowerCase().includes(q))
    );
  });

  const handleSelect = useCallback(
    (item: PaletteItem) => {
      onClose();
      router.push(item.href);
    },
    [onClose, router]
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open handled externally
        }
      }

      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
      } else if (e.key === "Enter" && filteredItems[selectedIndex]) {
        e.preventDefault();
        handleSelect(filteredItems[selectedIndex]);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, filteredItems, selectedIndex, handleSelect]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(3, 7, 18, 0.75)",
        backdropFilter: "blur(6px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "12vh",
        paddingLeft: "16px",
        paddingRight: "16px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "620px",
          backgroundColor: "#0d1424",
          border: "1px solid rgba(99, 102, 241, 0.3)",
          borderRadius: "14px",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(99, 102, 241, 0.15)",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "14px 18px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            gap: "12px",
          }}
        >
          <Search size={18} color="#818cf8" />
          <input
            type="text"
            placeholder="Search commands, complaints, incidents, views... (↑↓ to navigate)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            autoFocus
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#f1f5f9",
              fontSize: "14px",
              fontFamily: "inherit",
            }}
          />
          <button
            onClick={onClose}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              borderRadius: "6px",
              padding: "4px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Results List */}
        <div
          style={{
            maxHeight: "360px",
            overflowY: "auto",
            padding: "8px",
          }}
        >
          {filteredItems.length === 0 ? (
            <div
              style={{
                padding: "32px",
                textAlign: "center",
                color: "#64748b",
                fontSize: "13px",
              }}
            >
              No matching commands or destinations found.
            </div>
          ) : (
            filteredItems.map((item, index) => {
              const Icon = item.icon;
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    cursor: "pointer",
                    backgroundColor: isSelected ? "rgba(99, 102, 241, 0.15)" : "transparent",
                    border: isSelected
                      ? "1px solid rgba(99, 102, 241, 0.3)"
                      : "1px solid transparent",
                    transition: "all 0.12s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
                    <div
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "8px",
                        backgroundColor: isSelected
                          ? "rgba(99, 102, 241, 0.3)"
                          : "rgba(255, 255, 255, 0.04)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: isSelected ? "#a5b4fc" : "#94a3b8",
                        flexShrink: 0,
                      }}
                    >
                      <Icon size={16} />
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: "13px",
                          fontWeight: 500,
                          color: isSelected ? "#ffffff" : "#e2e8f0",
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                        }}
                      >
                        <span>{item.title}</span>
                        <span
                          style={{
                            fontSize: "10px",
                            padding: "1px 6px",
                            borderRadius: "4px",
                            backgroundColor: "rgba(255, 255, 255, 0.06)",
                            color: "#94a3b8",
                          }}
                        >
                          {item.category}
                        </span>
                      </div>
                      {item.description && (
                        <div
                          style={{
                            fontSize: "11px",
                            color: "#64748b",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {item.description}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
                    {item.shortcut && (
                      <kbd
                        style={{
                          fontSize: "10px",
                          fontFamily: "monospace",
                          color: "#64748b",
                          padding: "2px 6px",
                          backgroundColor: "rgba(255, 255, 255, 0.04)",
                          border: "1px solid rgba(255, 255, 255, 0.08)",
                          borderRadius: "4px",
                        }}
                      >
                        {item.shortcut}
                      </kbd>
                    )}
                    <ArrowRight
                      size={14}
                      color={isSelected ? "#818cf8" : "transparent"}
                      style={{ transition: "all 0.12s ease" }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div
          style={{
            padding: "8px 18px",
            borderTop: "1px solid rgba(255, 255, 255, 0.06)",
            backgroundColor: "rgba(0, 0, 0, 0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "11px",
            color: "#64748b",
          }}
        >
          <div>
            Press <kbd style={{ padding: "1px 4px", background: "rgba(255,255,255,0.08)", borderRadius: "3px" }}>↵</kbd> to select, <kbd style={{ padding: "1px 4px", background: "rgba(255,255,255,0.08)", borderRadius: "3px" }}>ESC</kbd> to close
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#22c55e" }}></span>
            <span>Civic Operations v6.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
