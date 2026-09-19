"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { getMapComplaints, getMapIncidents, recomputeIncidents } from "@/lib/api";
import type { MapMarker, MapIncidentMarker } from "@/lib/types";
import { MAP_CENTER } from "@/lib/constants";
import { MapPin, RefreshCw, Layers, AlertTriangle, ShieldAlert, Sparkles } from "lucide-react";

// SSR-safe dynamic import for the map
const MapView = dynamic(() => import("@/components/MapView").then((m) => m.MapView), {
  ssr: false,
  loading: () => (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "var(--brand-card)",
        borderRadius: 12,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--text-muted)",
        fontSize: 14,
      }}
    >
      Loading urban civic intelligence map…
    </div>
  ),
});

export default function MapPage() {
  const [complaintMarkers, setComplaintMarkers] = useState<MapMarker[]>([]);
  const [incidentMarkers, setIncidentMarkers] = useState<MapIncidentMarker[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRecomputing, setIsRecomputing] = useState(false);
  const [selectedPriority, setSelectedPriority] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [viewMode, setViewMode] = useState<"all" | "incidents" | "complaints">("all");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [compData, incData] = await Promise.all([
        getMapComplaints({
          priority: selectedPriority || undefined,
          category: selectedCategory || undefined,
        }),
        getMapIncidents({
          priority: selectedPriority || undefined,
          category: selectedCategory || undefined,
        }),
      ]);
      setComplaintMarkers(compData.markers || compData.complaints || []);
      setIncidentMarkers(incData || []);
    } catch {
      setComplaintMarkers([]);
      setIncidentMarkers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecompute = async () => {
    setIsRecomputing(true);
    try {
      await recomputeIncidents({ hours: 72, dry_run: false });
      await fetchData();
    } catch (e: any) {
      alert(`Recomputation failed: ${e.message}`);
    } finally {
      setIsRecomputing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedPriority, selectedCategory]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <div className="top-bar">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <h2 style={{ fontSize: 15, fontWeight: 600 }}>Urban Civic Intelligence Command Map</h2>
            <span style={{ fontSize: 11, background: "rgba(99,102,241,0.15)", color: "var(--accent-indigo)", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
              Module 4 Live
            </span>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {incidentMarkers.length} Active Incidents · {complaintMarkers.length} Geolocated Complaints · Spatio-Temporal DBSCAN
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {/* Layer View Filter */}
          <div style={{ display: "flex", background: "var(--brand-card)", borderRadius: 6, padding: 2, border: "1px solid var(--brand-border)" }}>
            <button
              onClick={() => setViewMode("all")}
              style={{
                padding: "4px 10px",
                fontSize: 11,
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                background: viewMode === "all" ? "var(--accent-indigo)" : "transparent",
                color: viewMode === "all" ? "#fff" : "var(--text-secondary)",
                fontWeight: viewMode === "all" ? 600 : 400,
              }}
            >
              All Layers
            </button>
            <button
              onClick={() => setViewMode("incidents")}
              style={{
                padding: "4px 10px",
                fontSize: 11,
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                background: viewMode === "incidents" ? "var(--accent-indigo)" : "transparent",
                color: viewMode === "incidents" ? "#fff" : "var(--text-secondary)",
                fontWeight: viewMode === "incidents" ? 600 : 400,
              }}
            >
              Incidents ({incidentMarkers.length})
            </button>
            <button
              onClick={() => setViewMode("complaints")}
              style={{
                padding: "4px 10px",
                fontSize: 11,
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                background: viewMode === "complaints" ? "var(--accent-indigo)" : "transparent",
                color: viewMode === "complaints" ? "#fff" : "var(--text-secondary)",
                fontWeight: viewMode === "complaints" ? 600 : 400,
              }}
            >
              Complaints ({complaintMarkers.length})
            </button>
          </div>

          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="input"
            style={{ width: 130, fontSize: 12 }}
          >
            <option value="">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="input"
            style={{ width: 140, fontSize: 12 }}
          >
            <option value="">All Categories</option>
            <option value="water">Water</option>
            <option value="roads">Roads</option>
            <option value="electricity">Electricity</option>
            <option value="sanitation">Sanitation</option>
            <option value="drainage">Drainage</option>
          </select>

          <button
            onClick={handleRecompute}
            disabled={isRecomputing}
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: "6px 12px", display: "flex", alignItems: "center", gap: 6 }}
            title="Trigger spatio-temporal DBSCAN cluster recomputation"
          >
            <Sparkles size={13} color="var(--accent-indigo)" />
            {isRecomputing ? "Clustering..." : "Recluster Incidents"}
          </button>

          <button onClick={fetchData} className="btn btn-ghost" style={{ padding: "6px 10px" }}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      <div style={{ flex: 1, padding: 16, position: "relative" }}>
        <MapView
          markers={viewMode === "incidents" ? [] : complaintMarkers}
          incidents={viewMode === "complaints" ? [] : incidentMarkers}
          showIncidentsOnly={viewMode === "incidents"}
          centerLat={MAP_CENTER.lat}
          centerLng={MAP_CENTER.lng}
          height="100%"
          zoom={12}
        />
        {loading && (
          <div
            style={{
              position: "absolute",
              top: 28,
              right: 120,
              background: "rgba(15, 23, 42, 0.85)",
              backdropFilter: "blur(8px)",
              padding: "6px 12px",
              borderRadius: 6,
              border: "1px solid var(--brand-border)",
              fontSize: 12,
              color: "var(--accent-indigo)",
              display: "flex",
              alignItems: "center",
              gap: 6,
              zIndex: 10,
            }}
          >
            <RefreshCw size={12} className="spin" /> Syncing GIS layers...
          </div>
        )}
      </div>
    </div>
  );
}
