/**
 * MapPanel — Leaflet map for the MIRAGE IGAD dashboard.
 *
 * Rendered client-side only (no SSR) to avoid Leaflet's window dependency.
 * Import via Next.js dynamic():
 *   const MapPanel = dynamic(() => import('./components/MapPanel'), { ssr: false });
 *
 * Shows:
 *   • Cyclone eye marker + pulsing hazard circle (radius = impact_radius_km)
 *   • Shelter pins coloured by occupancy ratio (green / amber / red)
 *   • Supply route polylines coloured by status (green=CLEAR, red=BLOCKED)
 *   • OpenStreetMap base tiles — no API key required
 */

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  Polyline,
  useMap,
} from "react-leaflet";
import { useEffect } from "react";

// ── Leaflet default icon fix (broken in webpack bundling) ────────────────────
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// ─── Types ────────────────────────────────────────────────────────────────────
interface CycloneGeo {
  lat: number;
  lon: number;
  category: number;
  wind_speed_kmh: number;
  storm_surge_m: number;
  impact_radius_km: number;
}

interface ShelterGeo {
  id: string;
  name: string;
  lat: number;
  lon: number;
  capacity: number;
  current_occupancy: number;
  occupancy_ratio: number;
  food_days: number;
  water_days: number;
  status: string;
  zone_id: string;
  overflow_risk: number;
}

interface RouteGeo {
  id: string;
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  status: string;
  distance_km: number;
}

export interface MapData {
  tick: number;
  cyclone?: CycloneGeo | null;
  shelters: ShelterGeo[];
  routes: RouteGeo[];
}

interface Props {
  data: MapData;
  center: [number, number];
  zoom: number;
}

// ─── Helper: shelter marker colour by occupancy ───────────────────────────────
function shelterColour(ratio: number, status: string): string {
  if (status === "CLOSED" || status === "DAMAGED") return "#6b7280";  // grey
  if (ratio >= 0.9) return "#ef4444";   // red — critical
  if (ratio >= 0.7) return "#f59e0b";   // amber — warning
  return "#22c55e";                      // green — operational
}

function makeCircleIcon(colour: string, ratio: number): L.DivIcon {
  const size = 18 + Math.round(ratio * 14);  // 18–32 px based on occupancy
  return L.divIcon({
    className: "",
    html: `
      <div style="
        width:${size}px; height:${size}px;
        background:${colour};
        border:2px solid rgba(255,255,255,0.8);
        border-radius:50%;
        box-shadow:0 0 8px ${colour}99;
        display:flex; align-items:center; justify-content:center;
        font-size:9px; font-weight:bold; color:#fff;
      ">${Math.round(ratio * 100)}%</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function makeCycloneIcon(category: number): L.DivIcon {
  const catColors: Record<number, string> = {
    1: "#fde68a", 2: "#fbbf24", 3: "#f97316", 4: "#ef4444", 5: "#9333ea",
  };
  const col = catColors[category] || "#ef4444";
  return L.divIcon({
    className: "",
    html: `
      <div style="
        position:relative; width:36px; height:36px;
        display:flex; align-items:center; justify-content:center;
      ">
        <div style="
          position:absolute; width:36px; height:36px;
          border:3px solid ${col}; border-radius:50%;
          animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite;
          opacity:0.6;
        "></div>
        <div style="
          width:22px; height:22px;
          background:${col};
          border:2px solid white;
          border-radius:50%;
          display:flex; align-items:center; justify-content:center;
          font-size:10px; font-weight:900; color:#000;
          box-shadow:0 0 14px ${col};
          z-index:1;
        ">🌀</div>
      </div>
      <style>
        @keyframes ping {
          0% { transform:scale(1); opacity:.6 }
          75%,100% { transform:scale(2.2); opacity:0 }
        }
      </style>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

// ─── Auto-recenter when map data changes ─────────────────────────────────────
function RecenterOnData({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center[0], center[1], zoom]);  // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function MapPanel({ data, center, zoom }: Props) {
  const { cyclone, shelters, routes } = data;

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ width: "100%", height: "100%", borderRadius: "12px" }}
      zoomControl={true}
      scrollWheelZoom={true}
    >
      {/* OpenStreetMap tiles — no API key required */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        // Dark-style tiles via CartoDB — better visual for disaster dashboards
      />

      {/* Dark overlay tile for better dashboard aesthetics */}
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />

      <RecenterOnData center={center} zoom={zoom} />

      {/* ── Cyclone eye + impact zone ─────────────────────────────────── */}
      {cyclone && cyclone.lat && cyclone.lon && (
        <>
          {/* Outer hazard circle — full impact radius */}
          <Circle
            center={[cyclone.lat, cyclone.lon]}
            radius={cyclone.impact_radius_km * 1000}  // metres
            pathOptions={{
              color: "#ef4444",
              fillColor: "#ef444420",
              fillOpacity: 0.25,
              weight: 2,
              dashArray: "8 4",
            }}
          />
          {/* Inner storm-surge zone (~40% of impact radius) */}
          <Circle
            center={[cyclone.lat, cyclone.lon]}
            radius={cyclone.impact_radius_km * 400}
            pathOptions={{
              color: "#9333ea",
              fillColor: "#9333ea30",
              fillOpacity: 0.35,
              weight: 1.5,
              dashArray: "4 3",
            }}
          />
          {/* Cyclone eye marker */}
          <Marker
            position={[cyclone.lat, cyclone.lon]}
            icon={makeCycloneIcon(cyclone.category)}
          >
            <Popup>
              <div style={{ fontFamily: "monospace", fontSize: "12px", lineHeight: "1.6" }}>
                <strong>🌀 Cyclone — Category {cyclone.category}</strong><br />
                Wind: {cyclone.wind_speed_kmh} km/h<br />
                Storm surge: {cyclone.storm_surge_m} m<br />
                Impact radius: ~{cyclone.impact_radius_km} km<br />
                Position: {cyclone.lat.toFixed(3)}°, {cyclone.lon.toFixed(3)}°
              </div>
            </Popup>
          </Marker>
        </>
      )}

      {/* ── Supply routes ─────────────────────────────────────────────── */}
      {routes.map((r) => {
        if (!r.origin || !r.destination) return null;
        const colour = r.status === "BLOCKED" ? "#ef4444"
          : r.status === "DEGRADED" ? "#f59e0b"
          : "#22c55e";
        return (
          <Polyline
            key={r.id}
            positions={[
              [r.origin.lat, r.origin.lon],
              [r.destination.lat, r.destination.lon],
            ]}
            pathOptions={{ color: colour, weight: 3, dashArray: r.status === "BLOCKED" ? "6 4" : undefined }}
          >
            <Popup>
              <div style={{ fontFamily: "monospace", fontSize: "12px" }}>
                <strong>Route {r.id}</strong><br />
                Status: <span style={{ color: colour }}>{r.status}</span><br />
                Distance: {r.distance_km} km
              </div>
            </Popup>
          </Polyline>
        );
      })}

      {/* ── Shelter markers ───────────────────────────────────────────── */}
      {shelters.map((s) => {
        const col = shelterColour(s.occupancy_ratio, s.status);
        return (
          <Marker
            key={s.id}
            position={[s.lat, s.lon]}
            icon={makeCircleIcon(col, s.occupancy_ratio)}
          >
            <Popup>
              <div style={{ fontFamily: "sans-serif", fontSize: "12px", lineHeight: "1.7", minWidth: "160px" }}>
                <strong style={{ fontSize: "13px" }}>{s.name}</strong><br />
                <span style={{ color: "#6b7280" }}>{s.zone_id}</span><br />
                <hr style={{ margin: "4px 0", borderColor: "#e5e7eb" }} />
                Occupancy:{" "}
                <strong style={{ color: col }}>
                  {s.current_occupancy.toLocaleString()} / {s.capacity.toLocaleString()}
                  {" "}({Math.round(s.occupancy_ratio * 100)}%)
                </strong><br />
                Food supply: <strong>{s.food_days.toFixed(1)} days</strong><br />
                Water supply: <strong>{s.water_days.toFixed(1)} days</strong><br />
                Status: <strong>{s.status}</strong>
                {s.overflow_risk > 0.7 && (
                  <><br /><span style={{ color: "#ef4444" }}>⚠ Overflow risk: {Math.round(s.overflow_risk * 100)}%</span></>
                )}
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
