"use client";
import React, { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import {
  Play, Pause, RotateCcw, Wind, Users, Package,
  Bell, BellRing, X, Radio, AlertTriangle, CheckCircle2, Info,
  Map, Activity, Globe,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area,
} from "recharts";
import type { MapData } from "./components/MapPanel";

// ── Dynamic import: Leaflet must not run on the server ────────────────────────
const MapPanel = dynamic(() => import("./components/MapPanel"), { ssr: false });

// ─── Types ────────────────────────────────────────────────────────────────────

interface SimState {
  tick: number;
  is_running: boolean;
  cyclone_category: number;
  cyclone_wind: number;
  cyclone_position?: { lat: number; lon: number };
  storm_surge_m?: number;
  suggested_alert?: SuggestedAlert | null;
}

interface SuggestedAlert {
  hazard_type: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  cyclone_category: number;
  affected_zones: string[];
  message: string;
  channel: string;
  tick: number;
}

interface Shelter {
  id: string;
  name: string;
  zone_id: string;
  capacity: number;
  current_occupancy?: number;
  food_days?: number;
  water_days?: number;
  location?: { lat: number; lon: number };
}

interface Resource {
  id: string;
  type: string;
  quantity: number;
  unit: string;
  shelter_id: string;
}

interface Allocation {
  agent_name: string;
  shelter_id: string;
  resource_type: string;
  requested: number;
  allocated: number;
  reasoning: string;
  problem: string;
  reason: string;
  recommended_action: string;
  priority: string;
  strategy_used: string;
}

interface CommunityAlert {
  id: string;
  tick: number;
  severity: "INFO" | "WARNING" | "CRITICAL";
  cyclone_category: number;
  affected_zones: string[];
  message: string;
  channel: string;
  status: "SENT" | "DISMISSED" | "SUGGESTED";
  sent_by: string;
  sent_at?: string;
  created_at: string;
}

interface HistoryPoint {
  tick: number;
  occupancy: number;
  food: number;
  water: number;
}

interface ScenarioInfo {
  active: string;
  label: string;
  map_center: [number, number];
  map_zoom: number;
  available: string[];
}

// ─── Constants ────────────────────────────────────────────────────────────────

const API = "http://localhost:8000";
const POLL_MS = 1500;

// Default map center = IGAD demo region (Horn of Africa / Puntland, Somalia)
const DEFAULT_CENTER: [number, number] = [10.0, 49.5];
const DEFAULT_ZOOM = 6;

const SEVERITY_CONFIG = {
  INFO: {
    bg: "bg-blue-900/40", border: "border-blue-500/40", text: "text-blue-300",
    badge: "bg-blue-500/20 text-blue-300", icon: <Info size={13} />, label: "INFO",
  },
  WARNING: {
    bg: "bg-amber-900/40", border: "border-amber-500/40", text: "text-amber-300",
    badge: "bg-amber-500/20 text-amber-300", icon: <AlertTriangle size={13} />, label: "WARNING",
  },
  CRITICAL: {
    bg: "bg-red-900/40", border: "border-red-500/40", text: "text-red-300",
    badge: "bg-red-500/20 text-red-300", icon: <AlertTriangle size={13} />, label: "CRITICAL",
  },
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function Dashboard() {
  const [state, setState] = useState<SimState>({ tick: 0, is_running: false, cyclone_category: 0, cyclone_wind: 0 });
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [alerts, setAlerts] = useState<CommunityAlert[]>([]);
  const [mapData, setMapData] = useState<MapData>({ tick: 0, shelters: [], routes: [] });
  const [scenario, setScenario] = useState<ScenarioInfo>({
    active: "igad",
    label: "Cyclone DEMO-GATI | IGAD Hackathon 2026 Demo Scenario",
    map_center: DEFAULT_CENTER,
    map_zoom: DEFAULT_ZOOM,
    available: ["igad", "research_a", "research_b", "research_c"],
  });
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [apiError, setApiError] = useState(false);
  const [broadcastBusy, setBroadcastBusy] = useState(false);
  const [broadcastSuccess, setBroadcastSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState<"dashboard" | "map">("dashboard");
  const [scenarioSwitching, setScenarioSwitching] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [resState, resShelters, resResources, resAllocations, resAlerts, resMap, resScenario] =
        await Promise.all([
          fetch(`${API}/state`).then((r) => r.json()),
          fetch(`${API}/shelters`).then((r) => r.json()),
          fetch(`${API}/resources`).then((r) => r.json()),
          fetch(`${API}/allocations`).then((r) => r.json()),
          fetch(`${API}/alerts`).then((r) => r.json()),
          fetch(`${API}/map-data`).then((r) => r.json()),
          fetch(`${API}/scenario`).then((r) => r.json()),
        ]);

      setApiError(false);
      const s = resState as SimState;
      setState(s);
      setShelters(resShelters as Shelter[]);
      setResources(resResources as Resource[]);
      setAllocations(resAllocations as Allocation[]);
      setAlerts(resAlerts as CommunityAlert[]);
      setMapData(resMap as MapData);
      setScenario(resScenario as ScenarioInfo);

      if (s.tick > 0) {
        setHistory((prev) => {
          const last = prev[prev.length - 1];
          if (last && last.tick === s.tick) return prev;
          const sl = resShelters as Shelter[];
          const rl = resResources as Resource[];
          const totalOcc = sl.reduce((a, sh) => a + (sh.current_occupancy || 0), 0);
          const totalFood = rl.filter((r) => r.type === "FOOD").reduce((a, r) => a + (r.quantity || 0), 0);
          const totalWater = rl.filter((r) => r.type === "WATER").reduce((a, r) => a + (r.quantity || 0), 0);
          return [...prev, { tick: s.tick, occupancy: totalOcc, food: totalFood / 1000, water: totalWater / 1000 }];
        });
      } else if (s.tick === 0) {
        setHistory([]);
      }
    } catch {
      setApiError(true);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, POLL_MS);
    return () => clearInterval(id);
  }, [fetchAll]);

  const controlAction = async (action: string) => {
    await fetch(`${API}/control/${action}`, { method: "POST" });
    if (action === "reset") { setHistory([]); setAlerts([]); setBroadcastSuccess(false); }
  };

  const switchScenario = async (name: string) => {
    setScenarioSwitching(true);
    try {
      await fetch(`${API}/control/scenario/${name}`, { method: "POST" });
      setHistory([]);
      setAlerts([]);
      setBroadcastSuccess(false);
      await fetchAll();
    } finally {
      setScenarioSwitching(false);
    }
  };

  const sendBroadcast = async (suggestion?: SuggestedAlert) => {
    setBroadcastBusy(true);
    try {
      const body = suggestion
        ? { affected_zones: suggestion.affected_zones, message: suggestion.message, channel: suggestion.channel }
        : { affected_zones: ["zone_01", "zone_02"], channel: "ALL" };
      await fetch(`${API}/alerts/broadcast`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      setBroadcastSuccess(true);
      setTimeout(() => setBroadcastSuccess(false), 3000);
      fetchAll();
    } finally { setBroadcastBusy(false); }
  };

  const dismissSuggestion = async () => {
    await fetch(`${API}/alerts/dismiss-suggestion`, { method: "POST" });
    fetchAll();
  };

  // Derived metrics
  const totalOccupancy = shelters.reduce((a, s) => a + (s.current_occupancy || 0), 0);
  const totalCapacity = shelters.reduce((a, s) => a + (s.capacity || 0), 0);
  const occupancyPct = totalCapacity > 0 ? ((totalOccupancy / totalCapacity) * 100).toFixed(1) : "0.0";
  const sentAlerts = alerts.filter((a) => a.status === "SENT");

  // Map center: follow cyclone if running, else use scenario default
  const mapCenter: [number, number] = mapData.cyclone?.lat && mapData.cyclone?.lon
    ? [mapData.cyclone.lat, mapData.cyclone.lon]
    : (scenario.map_center as [number, number]) || DEFAULT_CENTER;
  const mapZoom = scenario.map_zoom || DEFAULT_ZOOM;
  return (
    <div className="min-h-screen bg-neutral-950 text-white font-sans">

      {/* ── Sticky top bar ─────────────────────────────────────────────── */}
      <div className="border-b border-white/10 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-3 flex flex-col md:flex-row justify-between items-center gap-3">
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              MIRAGE OS
            </h1>
            <p className="text-neutral-500 text-xs">IGAD Early Warning &amp; Early Action — EOC Dashboard</p>
          </div>

          {/* Tab switcher */}
          <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 border border-white/10">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "dashboard" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"
              }`}
            >
              <Activity size={13} /> Dashboard
            </button>
            <button
              id="btn-map-tab"
              onClick={() => setActiveTab("map")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "map" ? "bg-blue-600 text-white" : "text-neutral-400 hover:text-white"
              }`}
            >
              <Map size={13} /> Live Map
              {state.cyclone_category >= 3 && (
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse ml-0.5" />
              )}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-lg border border-white/5">
              <span className="text-xs text-neutral-500 uppercase tracking-wider">Tick</span>
              <span className="font-mono font-bold text-base text-cyan-400">{String(state.tick).padStart(3, "0")}</span>
            </div>
            {state.is_running && (
              <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-400/10 px-2.5 py-1.5 rounded-full border border-green-400/20">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> LIVE
              </span>
            )}
            <button id="btn-start" onClick={() => controlAction("start")} disabled={state.is_running}
              className="p-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-xl transition-all shadow-[0_0_12px_rgba(37,99,235,0.4)]">
              <Play size={16} />
            </button>
            <button id="btn-pause" onClick={() => controlAction("pause")} disabled={!state.is_running}
              className="p-2 bg-neutral-800 hover:bg-neutral-700 disabled:opacity-40 rounded-xl border border-white/10 transition-all">
              <Pause size={16} />
            </button>
            <button id="btn-reset" onClick={() => controlAction("reset")}
              className="p-2 bg-red-900/50 hover:bg-red-800 text-red-300 rounded-xl border border-red-500/20 transition-all">
              <RotateCcw size={16} />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-5 space-y-5">

        {/* ── API error */}
        {apiError && (
          <div className="p-3 bg-red-900/60 border border-red-500/40 rounded-xl text-sm text-red-300">
            ⚠ Cannot reach backend at <code>http://localhost:8000</code>. Make sure uvicorn is running.
          </div>
        )}

        {/* ── Alert suggestion banner */}
        {state.suggested_alert && (
          <AlertSuggestionBanner
            suggestion={state.suggested_alert}
            busy={broadcastBusy} success={broadcastSuccess}
            onSend={() => sendBroadcast(state.suggested_alert!)}
            onDismiss={dismissSuggestion}
          />
        )}

        {/* ════════════════════════ DASHBOARD TAB ════════════════════════ */}
        {activeTab === "dashboard" && (
          <>
            {/* KPI strip */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <KpiCard icon={<Wind size={52} />} label="Cyclone Intensity" color="text-red-400">
                <h2 className="text-3xl font-bold text-red-400">CAT {state.cyclone_category}</h2>
                <p className="text-sm text-red-400/70">{state.cyclone_wind} km/h</p>
              </KpiCard>
              <KpiCard icon={<Users size={52} />} label="Shelter Occupancy" color="text-blue-400">
                <h2 className="text-3xl font-bold text-blue-400">{totalOccupancy.toLocaleString()}</h2>
                <p className="text-sm text-blue-400/70">{occupancyPct}% of capacity</p>
              </KpiCard>
              <KpiCard icon={<Package size={52} />} label="Resource Stockpiles" color="text-emerald-400">
                <h2 className="text-3xl font-bold text-emerald-400">{resources.length}</h2>
                <p className="text-sm text-emerald-400/70">Tracked depots</p>
              </KpiCard>
              <KpiCard icon={<Bell size={52} />} label="Alerts Broadcast" color="text-amber-400">
                <h2 className="text-3xl font-bold text-amber-400">{sentAlerts.length}</h2>
                <p className="text-sm text-amber-400/70">Community alerts sent</p>
              </KpiCard>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <ChartCard title="Evacuation &amp; Shelter Occupancy">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="colorOcc" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#60A5FA" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#60A5FA" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis dataKey="tick" stroke="#ffffff40" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#ffffff40" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid #ffffff20", borderRadius: "8px" }} />
                  <Area type="monotone" dataKey="occupancy" stroke="#60A5FA" strokeWidth={2} fill="url(#colorOcc)" name="Occupancy" />
                </AreaChart>
              </ChartCard>

              <ChartCard title="Resource Consumption (k Units)">
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis dataKey="tick" stroke="#ffffff40" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#ffffff40" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid #ffffff20", borderRadius: "8px" }} />
                  <Line type="monotone" dataKey="food" stroke="#34D399" strokeWidth={2} dot={false} name="Food (k kg)" />
                  <Line type="monotone" dataKey="water" stroke="#A78BFA" strokeWidth={2} dot={false} name="Water (k L)" />
                </LineChart>
              </ChartCard>
            </div>

            {/* Data panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Shelter Status */}
              <Panel title="Shelter Status" icon={<Users size={14} />}>
                {shelters.length === 0 && <EmptyState label="No shelter data yet. Press Start." />}
                {shelters.map((s, i) => {
                  const pct = s.capacity > 0 ? ((s.current_occupancy || 0) / s.capacity) * 100 : 0;
                  const bar = pct > 90 ? "bg-red-500" : pct > 70 ? "bg-amber-500" : "bg-emerald-500";
                  return (
                    <div key={i} className="bg-black/20 p-3 rounded-xl border border-white/5 space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-blue-300 text-sm">{s.name || s.id}</p>
                          <p className="text-xs text-neutral-500">{s.zone_id}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-mono text-sm">{(s.current_occupancy ?? 0).toLocaleString()}</p>
                          <p className="text-xs text-neutral-500">/ {s.capacity.toLocaleString()}</p>
                        </div>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/5">
                        <div className={`h-full rounded-full transition-all ${bar}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                      <div className="flex gap-3 text-xs">
                        <span className="text-emerald-400">{(s.food_days ?? 0).toFixed(1)}d Food</span>
                        <span className="text-blue-400">{(s.water_days ?? 0).toFixed(1)}d Water</span>
                      </div>
                    </div>
                  );
                })}
              </Panel>

              {/* AI Allocations */}
              <Panel title="AI Allocation Decisions" icon={<Activity size={14} />}>
                {allocations.length === 0 && <EmptyState label="No allocations yet. Press Start." />}
                {allocations.map((a, i) => {
                  const priorityColors: Record<string, string> = {
                    Low: "bg-neutral-500/10 text-neutral-400 border-neutral-500/20",
                    Medium: "bg-amber-500/10 text-amber-300 border-amber-500/20",
                    High: "bg-orange-500/10 text-orange-400 border-orange-500/20",
                    Critical: "bg-red-500/10 text-red-400 border-red-500/20",
                  };
                  const badgeColor = priorityColors[a.priority] || priorityColors.Medium;

                  return (
                    <div key={i} className="bg-black/20 p-3.5 rounded-xl border border-white/5 space-y-2.5 transition-all hover:border-white/10">
                      {/* Header row: Agent Name & Priority */}
                      <div className="flex justify-between items-center">
                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-[10px] font-semibold tracking-wide uppercase">{a.agent_name || "Unknown Agent"}</span>
                        <span className={`px-2 py-0.5 rounded text-[9px] uppercase tracking-wider font-bold border ${badgeColor}`}>
                          {a.priority || "Medium"}
                        </span>
                      </div>

                      {/* Problem identified & Target info */}
                      <div className="space-y-0.5">
                        <h4 className="text-sm font-semibold text-white flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                          {a.problem || "Resource Request"}
                        </h4>
                        <p className="text-[11px] text-neutral-400">
                          Target: <span className="text-neutral-200">{a.shelter_id}</span> ({a.resource_type})
                        </p>
                      </div>

                      {/* Reason paragraph */}
                      {a.reason && (
                        <p className="text-[11px] text-neutral-300 bg-white/5 p-2 rounded-lg border border-white/5 leading-normal">
                          {a.reason}
                        </p>
                      )}

                      {/* Recommended Action */}
                      <div className="text-[11px] space-y-0.5 pt-1.5 border-t border-white/5">
                        <p className="text-[9px] text-neutral-500 uppercase font-bold tracking-wider">Recommended Action</p>
                        <p className="text-cyan-300 font-medium">{a.recommended_action || `Dispatch ${a.allocated} units`}</p>
                      </div>

                      {/* Numbers row (Req / Alloc) & Strategy */}
                      <div className="flex justify-between items-center pt-2 border-t border-white/5">
                        <div className="flex gap-3 text-[11px] font-mono">
                          <span className="text-neutral-500">Req: <strong className="text-neutral-300">{a.requested}</strong></span>
                          <span className="text-cyan-400 font-bold">Alloc: <strong>{a.allocated}</strong></span>
                        </div>
                        <span className="text-neutral-500 font-mono text-[9px] uppercase">
                          {a.strategy_used}
                        </span>
                      </div>

                      {/* Keep the reasoning field (from Gemini) as helper text at bottom if available */}
                      {a.reasoning && (
                        <p className="text-[10px] text-neutral-500 italic leading-snug pt-1 border-t border-white/5 border-dashed">
                          Note: {a.reasoning}
                        </p>
                      )}
                    </div>
                  );
                })}
              </Panel>

              {/* Community Alerts */}
              <AlertsPanel alerts={alerts} onManualBroadcast={() => sendBroadcast()} busy={broadcastBusy} />
            </div>
          </>
        )}

        {/* ════════════════════════ MAP TAB ════════════════════════════── */}
        {activeTab === "map" && (
          <div className="space-y-4">
            {/* Scenario info bar */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 px-1">
              <div className="flex items-center gap-2">
                <Globe size={14} className="text-blue-400" />
                <span className="text-xs text-neutral-400">{scenario.label}</span>
                {scenario.active === "igad" && (
                  <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full border border-blue-500/20">IGAD Demo</span>
                )}
              </div>
              {/* Scenario switcher */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-neutral-500">Scenario:</span>
                <div className="flex gap-1">
                  {scenario.available.map((s) => (
                    <button
                      key={s}
                      onClick={() => switchScenario(s)}
                      disabled={scenarioSwitching || s === scenario.active}
                      className={`text-xs px-2.5 py-1 rounded-lg border transition-all disabled:cursor-not-allowed ${
                        s === scenario.active
                          ? "bg-blue-600 border-blue-500 text-white"
                          : "bg-white/5 border-white/10 text-neutral-400 hover:text-white hover:bg-white/10"
                      }`}
                    >
                      {s === "igad" ? "IGAD" : s.replace("research_", "Res-").toUpperCase()}
                    </button>
                  ))}
                </div>
                {scenarioSwitching && <span className="text-xs text-neutral-500 animate-pulse">Switching…</span>}
              </div>
            </div>
            {/* Map legend */}
            <div className="flex flex-wrap items-center gap-4 px-1 text-xs text-neutral-400">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> Shelter (&lt;70%)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> Shelter (70–90%)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> Shelter (&gt;90% / overflow)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-6 border-t-2 border-emerald-500 inline-block" /> Route (Clear)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-6 border-t-2 border-red-500 border-dashed inline-block" /> Route (Blocked)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="text-base">🌀</span> Cyclone eye
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full border border-red-500 border-dashed inline-block" /> Impact zone
              </span>
            </div>

            {/* Map container — 600px tall */}
            <div
              className="w-full rounded-2xl overflow-hidden border border-white/10"
              style={{ height: "600px" }}
            >
              {mapData.shelters.length === 0 && !mapData.cyclone ? (
                <div className="w-full h-full flex items-center justify-center bg-neutral-900 text-neutral-500 text-sm">
                  <div className="text-center space-y-2">
                    <Map size={32} className="mx-auto opacity-30" />
                    <p>Map will populate when simulation starts.</p>
                    <p className="text-xs">Press ▶ Start on the Dashboard tab first.</p>
                  </div>
                </div>
              ) : (
                <MapPanel
                  data={mapData}
                  center={mapCenter}
                  zoom={mapZoom}
                />
              )}
            </div>

            {/* Map data stats row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBadge label="Cyclone Cat." value={`CAT ${state.cyclone_category}`} color="text-red-400" />
              <StatBadge label="Wind Speed" value={`${state.cyclone_wind} km/h`} color="text-orange-400" />
              <StatBadge label="Impact Radius" value={mapData.cyclone ? `~${mapData.cyclone.impact_radius_km} km` : "—"} color="text-purple-400" />
              <StatBadge label="Shelters Mapped" value={`${mapData.shelters.length}`} color="text-blue-400" />
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

// ─── Alert suggestion banner ──────────────────────────────────────────────────

function AlertSuggestionBanner({ suggestion, busy, success, onSend, onDismiss }: {
  suggestion: SuggestedAlert; busy: boolean; success: boolean;
  onSend: () => void; onDismiss: () => void;
}) {
  const cfg = SEVERITY_CONFIG[suggestion.severity];
  return (
    <div className={`relative p-4 rounded-2xl border ${cfg.bg} ${cfg.border} flex flex-col md:flex-row gap-4 items-start md:items-center`}>
      <div className="relative flex-shrink-0">
        <BellRing size={20} className={cfg.text} />
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500 animate-ping" />
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${cfg.badge}`}>{cfg.label}</span>
          <span className="text-xs text-neutral-400">Risk Agent · Cat {suggestion.cyclone_category} · Tick {suggestion.tick}</span>
        </div>
        <p className={`text-sm font-medium ${cfg.text}`}>{suggestion.message}</p>
        <p className="text-xs text-neutral-500 mt-1">Zones: {suggestion.affected_zones.join(", ")} · Channel: {suggestion.channel}</p>
      </div>
      <div className="flex gap-2 flex-shrink-0">
        {success ? (
          <span className="flex items-center gap-1.5 text-sm text-emerald-400 bg-emerald-400/10 px-4 py-2 rounded-xl border border-emerald-400/20">
            <CheckCircle2 size={14} /> Broadcast Sent
          </span>
        ) : (
          <button id="btn-send-alert" onClick={onSend} disabled={busy}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 ${
              suggestion.severity === "CRITICAL"
                ? "bg-red-600 hover:bg-red-500 text-white shadow-[0_0_18px_rgba(220,38,38,0.4)]"
                : "bg-amber-600 hover:bg-amber-500 text-white"}`}>
            <Radio size={14} /> {busy ? "Sending…" : "Broadcast Alert"}
          </button>
        )}
        <button id="btn-dismiss-alert" onClick={onDismiss}
          className="p-2 text-neutral-500 hover:text-neutral-300 hover:bg-white/5 rounded-xl transition-all" title="Dismiss">
          <X size={15} />
        </button>
      </div>
    </div>
  );
}

// ─── Alerts feed panel ────────────────────────────────────────────────────────

function AlertsPanel({ alerts, onManualBroadcast, busy }: {
  alerts: CommunityAlert[]; onManualBroadcast: () => void; busy: boolean;
}) {
  const sentAlerts = alerts.filter((a) => a.status === "SENT");
  return (
    <div className="bg-white/5 border border-white/10 p-5 rounded-2xl flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell size={14} className="text-amber-400" />
          <h3 className="text-neutral-300 font-medium text-sm">Community Alerts</h3>
          {sentAlerts.length > 0 && (
            <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full">{sentAlerts.length} sent</span>
          )}
        </div>
        <button id="btn-manual-broadcast" onClick={onManualBroadcast} disabled={busy}
          className="text-xs px-3 py-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 rounded-lg border border-amber-500/20 transition-all disabled:opacity-50">
          + Manual Broadcast
        </button>
      </div>
      <div className="overflow-y-auto max-h-96 space-y-2 pr-0.5">
        {alerts.length === 0 && <EmptyState label="No alerts yet. Auto-suggested at Cat 3+." />}
        {alerts.map((a) => {
          const cfg = SEVERITY_CONFIG[a.severity] || SEVERITY_CONFIG.INFO;
          return (
            <div key={a.id} className={`p-3 rounded-xl border ${a.status === "SENT" ? `${cfg.bg} ${cfg.border}` : "bg-white/3 border-white/5 opacity-50"}`}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.badge}`}>
                    {cfg.icon} {cfg.label}
                  </span>
                  {a.status === "SENT" ? <span className="text-xs text-emerald-400">✓ Sent</span> : <span className="text-xs text-neutral-500">Dismissed</span>}
                </div>
                <span className="text-xs text-neutral-500 font-mono">T:{a.tick}</span>
              </div>
              <p className="text-xs text-neutral-300 leading-relaxed line-clamp-3">{a.message}</p>
              <div className="flex gap-2 mt-1.5 text-xs text-neutral-500">
                <span>📡 {a.channel}</span><span>·</span><span>{a.affected_zones.join(", ")}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Shared sub-components ────────────────────────────────────────────────────

function KpiCard({ icon, label, color, children }: { icon: React.ReactNode; label: string; color: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/5 border border-white/10 p-5 rounded-2xl flex flex-col justify-between relative overflow-hidden">
      <div className={`absolute top-0 right-0 p-3 opacity-10 ${color}`}>{icon}</div>
      <p className="text-neutral-400 text-xs font-medium uppercase tracking-wider">{label}</p>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-white/5 border border-white/10 p-5 rounded-2xl flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <span className="text-neutral-400">{icon}</span>
        <h3 className="text-neutral-300 font-medium text-sm">{title}</h3>
      </div>
      <div className="overflow-y-auto max-h-96 space-y-2 pr-0.5">{children}</div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/5 border border-white/10 p-5 rounded-2xl h-64">
      <h3 className="text-neutral-300 font-medium text-sm mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height="88%">
        {children as React.ReactElement}
      </ResponsiveContainer>
    </div>
  );
}

function StatBadge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-white/5 border border-white/10 p-3 rounded-xl">
      <p className="text-neutral-500 text-xs">{label}</p>
      <p className={`font-mono font-bold text-lg mt-0.5 ${color}`}>{value}</p>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return <p className="text-neutral-600 text-xs flex items-center justify-center h-16 text-center px-4">{label}</p>;
}
