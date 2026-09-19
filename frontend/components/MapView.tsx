"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import type { MapMarker, MapIncidentMarker, Priority } from "@/lib/types";
import { MARKER_COLORS, MAP_CENTER } from "@/lib/constants";
import { formatRelativeTime } from "@/lib/utils";

interface MapViewProps {
  markers?: MapMarker[];
  incidents?: MapIncidentMarker[];
  centerLat?: number;
  centerLng?: number;
  height?: string;
  onMarkerClick?: (marker: MapMarker) => void;
  onIncidentClick?: (incident: MapIncidentMarker) => void;
  zoom?: number;
  showIncidentsOnly?: boolean;
}

function getPriorityColor(priority: string): string {
  const p = priority?.toLowerCase();
  if (p === "critical") return "#ef4444";
  if (p === "high") return "#f97316";
  if (p === "medium") return "#eab308";
  if (p === "low") return "#22c55e";
  return MARKER_COLORS[p as Priority] || "#6366f1";
}

function createCirclePolygon(centerLng: number, centerLat: number, radiusMeters = 500, points = 32) {
  const coords: [number, number][] = [];
  const km = radiusMeters / 1000;
  const distanceX = km / (111.32 * Math.cos((centerLat * Math.PI) / 180));
  const distanceY = km / 110.574;

  for (let i = 0; i < points; i++) {
    const theta = (i / points) * (2 * Math.PI);
    const x = centerLng + distanceX * Math.cos(theta);
    const y = centerLat + distanceY * Math.sin(theta);
    coords.push([x, y]);
  }
  coords.push(coords[0]);
  return {
    type: "Polygon",
    coordinates: [coords],
  };
}

export function MapView({
  markers = [],
  incidents = [],
  centerLat = MAP_CENTER.lat,
  centerLng = MAP_CENTER.lng,
  height = "100%",
  onMarkerClick,
  onIncidentClick,
  zoom = 11,
  showIncidentsOnly = false,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const maplibreglRef = useRef<any>(null);
  const htmlMarkersRef = useRef<any[]>([]);
  const hasAutoFittedRef = useRef(false);

  const [selectedMarker, setSelectedMarker] = useState<MapMarker | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<MapIncidentMarker | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Store initial values in ref so initMap has stable identity
  const initialCenterRef = useRef<[number, number]>([centerLng, centerLat]);
  const initialZoomRef = useRef<number>(zoom);

  // Initialize MapLibre ONCE on mount
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    let isCancelled = false;

    const startMap = async () => {
      try {
        const maplibregl = await import("maplibre-gl");
        if (isCancelled || !mapContainer.current) return;
        maplibreglRef.current = maplibregl;

        const map = new maplibregl.Map({
          container: mapContainer.current,
          style: {
            version: 8,
            glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
            sources: {
              "esri-dark": {
                type: "raster",
                tiles: [
                  "https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                ],
                tileSize: 256,
                attribution: "© Esri, HERE, Garmin, OpenStreetMap",
                maxzoom: 16,
              },
              "esri-dark-ref": {
                type: "raster",
                tiles: [
                  "https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
                ],
                tileSize: 256,
                maxzoom: 16,
              },
            },
            layers: [
              {
                id: "esri-dark-layer",
                type: "raster",
                source: "esri-dark",
                minzoom: 0,
                maxzoom: 22,
              },
              {
                id: "esri-dark-ref-layer",
                type: "raster",
                source: "esri-dark-ref",
                minzoom: 0,
                maxzoom: 22,
              },
            ],
          },
          center: initialCenterRef.current,
          zoom: initialZoomRef.current,
        });

        map.addControl(new maplibregl.NavigationControl(), "top-right");

        map.on("load", () => {
          if (isCancelled) return;
          mapRef.current = map;
          map.resize();
          setLoaded(true);
        });
      } catch (err) {
        console.error("MapLibre initialization error:", err);
      }
    };

    startMap();

    return () => {
      isCancelled = true;
      htmlMarkersRef.current.forEach((m) => m.remove());
      htmlMarkersRef.current = [];
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        setLoaded(false);
      }
    };
  }, []);

  // Pan smoothly when center coordinates prop changes without destroying map
  useEffect(() => {
    if (loaded && mapRef.current && centerLat && centerLng) {
      mapRef.current.flyTo({
        center: [centerLng, centerLat],
        zoom: zoom || 13,
        essential: true,
        duration: 800,
      });
    }
  }, [centerLat, centerLng, zoom, loaded]);

  // Handle Container Resizing automatically
  useEffect(() => {
    if (!mapContainer.current) return;
    const observer = new ResizeObserver(() => {
      if (mapRef.current) {
        mapRef.current.resize();
      }
    });
    observer.observe(mapContainer.current);
    return () => observer.disconnect();
  }, []);


  // Render Polygons & HTML Markers
  useEffect(() => {
    if (!loaded || !mapRef.current) return;
    const map = mapRef.current;
    const maplibregl = maplibreglRef.current;
    if (!maplibregl) return;

    // 1. Clean up existing HTML markers
    htmlMarkersRef.current.forEach((m) => m.remove());
    htmlMarkersRef.current = [];

    // 2. Incident Polygons (Convex Hulls or High-Precision Geodesic Buffers)
    const polygonFeatures: any[] = [];
    incidents.forEach((inc) => {
      let geom: any = inc.geometry;
      if (typeof geom === "string") {
        try {
          geom = JSON.parse(geom);
        } catch (e) {
          geom = null;
        }
      }
      if (!geom || !geom.coordinates || geom.coordinates.length === 0) {
        if (inc.center_longitude && inc.center_latitude) {
          geom = createCirclePolygon(inc.center_longitude, inc.center_latitude, 450);
        }
      }
      if (geom && geom.coordinates) {
        polygonFeatures.push({
          type: "Feature" as const,
          properties: {
            id: inc.id,
            title: inc.title,
            priority: inc.priority,
            color: getPriorityColor(inc.priority),
          },
          geometry: geom,
        });
      }
    });

    const polygonGeoJson = {
      type: "FeatureCollection" as const,
      features: polygonFeatures,
    };

    if (map.getSource("incident-polygons-src")) {
      try {
        map.getSource("incident-polygons-src").setData(polygonGeoJson);
      } catch (e) {
        console.warn("Error updating polygon geojson:", e);
      }
    } else if (polygonFeatures.length > 0) {
      try {
        map.addSource("incident-polygons-src", {
          type: "geojson",
          data: polygonGeoJson,
        });

        map.addLayer({
          id: "incident-polygons-fill",
          type: "fill",
          source: "incident-polygons-src",
          paint: {
            "fill-color": ["get", "color"],
            "fill-opacity": 0.22,
          },
        });

        map.addLayer({
          id: "incident-polygons-outline",
          type: "line",
          source: "incident-polygons-src",
          paint: {
            "line-color": ["get", "color"],
            "line-width": 2.5,
            "line-dasharray": [2, 1],
          },
        });
      } catch (e) {
        console.warn("Error adding polygon layers:", e);
      }
    }

    // 3. Render HTML DOM Markers for Incidents (Beacons with glowing animated rings)
    incidents.forEach((inc) => {
      if (!inc.center_latitude || !inc.center_longitude) return;
      const color = getPriorityColor(inc.priority);

      // Wrapper element that MapLibre controls via transform: translate3d(...)
      const wrapper = document.createElement("div");
      wrapper.className = "civic-incident-marker-wrapper";
      wrapper.style.cursor = "pointer";

      const beacon = document.createElement("div");
      beacon.className = "civic-incident-beacon";
      beacon.style.cssText = `
        position: relative;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
      `;

      beacon.innerHTML = `
        <div style="
          position: absolute;
          width: 100%;
          height: 100%;
          border-radius: 50%;
          background: ${color};
          opacity: 0.35;
          animation: beacon-pulse 2s infinite ease-in-out;
        "></div>
        <div style="
          position: absolute;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: ${color};
          opacity: 0.55;
          border: 1.5px solid #ffffff;
        "></div>
        <div style="
          position: relative;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #0f172a;
          border: 2px solid ${color};
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 800;
          color: #ffffff;
          box-shadow: 0 0 12px ${color};
        ">
          ${inc.complaint_count}
        </div>
      `;

      wrapper.appendChild(beacon);

      wrapper.addEventListener("click", (e) => {
        e.stopPropagation();
        setSelectedMarker(null);
        setSelectedIncident(inc);
        onIncidentClick?.(inc);
        if (inc.center_longitude && inc.center_latitude) {
          map.flyTo({ center: [inc.center_longitude, inc.center_latitude], zoom: 14, duration: 600 });
        }
      });

      const marker = new maplibregl.Marker({ element: wrapper, anchor: "center" })
        .setLngLat([inc.center_longitude, inc.center_latitude])
        .addTo(map);

      htmlMarkersRef.current.push(marker);
    });

    // 4. Render HTML DOM Markers for Complaints (Clean glowing dots)
    if (!showIncidentsOnly) {
      markers.forEach((m) => {
        if (!m.latitude || !m.longitude) return;
        const color = getPriorityColor(m.priority);

        // Wrapper for MapLibre position control
        const wrapper = document.createElement("div");
        wrapper.className = "civic-complaint-marker-wrapper";
        wrapper.style.cursor = "pointer";

        const pin = document.createElement("div");
        pin.className = "civic-complaint-pin";
        pin.style.cssText = `
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: ${color};
          border: 2px solid #ffffff;
          box-shadow: 0 0 8px ${color};
          transition: transform 0.15s ease;
        `;

        wrapper.addEventListener("mouseenter", () => {
          pin.style.transform = "scale(1.5)";
        });
        wrapper.addEventListener("mouseleave", () => {
          pin.style.transform = "scale(1.0)";
        });

        wrapper.addEventListener("click", (e) => {
          e.stopPropagation();
          setSelectedIncident(null);
          setSelectedMarker(m);
          onMarkerClick?.(m);
          map.flyTo({ center: [m.longitude, m.latitude], zoom: 14.5, duration: 500 });
        });

        wrapper.appendChild(pin);

        const marker = new maplibregl.Marker({ element: wrapper, anchor: "center" })
          .setLngLat([m.longitude, m.latitude])
          .addTo(map);

        htmlMarkersRef.current.push(marker);
      });
    }

    // 5. Auto-Fit Bounds ONCE on initial data load to include all incidents & markers without forcing recenter on subsequent pan/polled updates
    if (!hasAutoFittedRef.current && (markers.length > 0 || incidents.length > 0)) {
      const bounds = new maplibregl.LngLatBounds();
      incidents.forEach((inc) => {
        if (inc.center_longitude && inc.center_latitude) {
          bounds.extend([inc.center_longitude, inc.center_latitude]);
        }
      });
      if (!showIncidentsOnly) {
        markers.forEach((m) => {
          if (m.longitude && m.latitude) bounds.extend([m.longitude, m.latitude]);
        });
      }
      if (!bounds.isEmpty()) {
        map.resize();
        map.fitBounds(bounds, { padding: 60, maxZoom: 13.5, animate: false });
        hasAutoFittedRef.current = true;
      }
    }
  }, [loaded, markers, incidents, showIncidentsOnly, onMarkerClick, onIncidentClick]);

  const handleResetView = () => {
    if (!mapRef.current) return;
    mapRef.current.flyTo({ center: [centerLng, centerLat], zoom, duration: 1000 });
  };

  return (
    <div style={{ position: "relative", height, borderRadius: 12, overflow: "hidden", border: "1px solid var(--brand-border)" }}>
      {/* Dynamic Keyframes for Beacon Animation */}
      <style>{`
        @keyframes beacon-pulse {
          0% { transform: scale(0.85); opacity: 0.7; }
          50% { transform: scale(1.35); opacity: 0.15; }
          100% { transform: scale(0.85); opacity: 0.7; }
        }
      `}</style>

      <div ref={mapContainer} style={{ width: "100%", height: "100%" }} />

      {/* Floating View Reset Control */}
      <button
        onClick={handleResetView}
        style={{
          position: "absolute",
          top: 16,
          right: 52,
          background: "rgba(17, 24, 39, 0.92)",
          backdropFilter: "blur(8px)",
          border: "1px solid var(--brand-border)",
          color: "var(--text-secondary)",
          borderRadius: 6,
          padding: "6px 12px",
          fontSize: 11,
          fontWeight: 600,
          cursor: "pointer",
          zIndex: 5,
        }}
        title="Reset map view to Chennai civic center"
      >
        🎯 Reset Center
      </button>

      {/* Incident Rich Command Popup Card */}
      {selectedIncident && (
        <div
          style={{
            position: "absolute",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(15, 23, 42, 0.96)",
            backdropFilter: "blur(16px)",
            border: `1.5px solid ${getPriorityColor(selectedIncident.priority)}`,
            borderRadius: 14,
            padding: 20,
            minWidth: 340,
            maxWidth: 440,
            zIndex: 20,
            boxShadow: `0 16px 48px rgba(0,0,0,0.75), 0 0 24px ${getPriorityColor(selectedIncident.priority)}44`,
          }}
        >
          <button
            onClick={() => setSelectedIncident(null)}
            style={{
              position: "absolute",
              top: 12,
              right: 12,
              background: "rgba(255,255,255,0.08)",
              border: "none",
              borderRadius: "50%",
              width: 24,
              height: 24,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-muted)",
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            ×
          </button>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, paddingRight: 24 }}>
            <span style={{ fontSize: 15, fontWeight: 800, color: "#ffffff", letterSpacing: "-0.01em" }}>
              🚨 {selectedIncident.title}
            </span>
          </div>

          <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
            <span className={`badge badge-${selectedIncident.priority}`}>{selectedIncident.priority.toUpperCase()}</span>
            <span style={{ fontSize: 11, background: "rgba(99,102,241,0.2)", color: "#818cf8", padding: "2px 8px", borderRadius: 4, fontWeight: 700 }}>
              {selectedIncident.complaint_count} Related Complaints
            </span>
            <span style={{ fontSize: 11, background: "rgba(249,115,22,0.2)", color: "#fb923c", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
              Trend: {selectedIncident.trend || "RISING"}
            </span>
          </div>

          {selectedIncident.affected_area && (
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>
              📍 <span>{selectedIncident.affected_area}</span>
            </div>
          )}

          <a
            href={`/incidents/${selectedIncident.id || selectedIncident.incident_code}`}
            style={{
              display: "block",
              padding: "10px 14px",
              background: "linear-gradient(135deg, #6366f1, #4f46e5)",
              color: "#fff",
              borderRadius: 8,
              fontSize: 12,
              textAlign: "center",
              textDecoration: "none",
              fontWeight: 700,
              boxShadow: "0 4px 14px rgba(99,102,241,0.4)",
            }}
          >
            Open Incident Command Center →
          </a>
        </div>
      )}

      {/* Complaint popup */}
      {selectedMarker && (
        <div
          style={{
            position: "absolute",
            bottom: 24,
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(15, 23, 42, 0.96)",
            backdropFilter: "blur(16px)",
            border: `1.5px solid ${getPriorityColor(selectedMarker.priority)}`,
            borderRadius: 14,
            padding: 18,
            minWidth: 300,
            maxWidth: 400,
            zIndex: 20,
            boxShadow: "0 12px 36px rgba(0,0,0,0.7)",
          }}
        >
          <button
            onClick={() => setSelectedMarker(null)}
            style={{
              position: "absolute",
              top: 10,
              right: 10,
              background: "rgba(255,255,255,0.08)",
              border: "none",
              borderRadius: "50%",
              width: 22,
              height: 22,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-muted)",
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            ×
          </button>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontFamily: "monospace", fontSize: 12, color: "#818cf8", fontWeight: 700 }}>
              {selectedMarker.complaint_code}
            </span>
            <span className={`badge badge-${selectedMarker.priority}`}>{selectedMarker.priority}</span>
            <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto", paddingRight: 18 }}>
              {formatRelativeTime(selectedMarker.created_at)}
            </span>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 8, lineHeight: 1.5 }}>
            "{selectedMarker.text_preview}"
          </p>
          {selectedMarker.location_text && (
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10 }}>
              📍 {selectedMarker.location_text}
            </div>
          )}
          <a
            href={`/complaints/${selectedMarker.complaint_code || selectedMarker.id}`}
            style={{
              display: "block",
              padding: "8px 12px",
              background: "var(--accent-indigo)",
              color: "#fff",
              borderRadius: 6,
              fontSize: 12,
              textAlign: "center",
              textDecoration: "none",
              fontWeight: 600,
            }}
          >
            View Grievance & AI Evidence →
          </a>
        </div>
      )}

      {/* Modern High-Tech Map Legend */}
      <div
        style={{
          position: "absolute",
          top: 16,
          left: 16,
          background: "rgba(17, 24, 39, 0.94)",
          backdropFilter: "blur(12px)",
          border: "1px solid var(--brand-border)",
          borderRadius: 10,
          padding: "12px 14px",
          boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          zIndex: 5,
        }}
      >
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "#818cf8", marginBottom: 8 }}>
          Spatial Intelligence
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
          <div style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid #ef4444", background: "rgba(239, 68, 68, 0.4)" }} />
          <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Incident Beacon ({incidents.length})</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#6366f1", border: "1.5px solid #fff" }} />
          <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Citizen Report ({markers.length})</span>
        </div>

        <div style={{ borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: 6, marginTop: 6 }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", marginBottom: 4 }}>
            Priority Levels
          </div>
          {(["critical", "high", "medium", "low"] as Priority[]).map((p) => (
            <div key={p} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: getPriorityColor(p) }} />
              <span style={{ fontSize: 11, color: "var(--text-secondary)", textTransform: "capitalize" }}>{p}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
