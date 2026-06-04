"use client";
import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, Wind, Users, Package, FileCheck } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';

// ─── Types ────────────────────────────────────────────────────────────────────
interface SimState {
  tick: number;
  is_running: boolean;
  cyclone_category: number;
  cyclone_wind: number;
}

interface Shelter {
  id: string;
  name: string;
  zone_id: string;
  capacity: number;
  current_occupancy?: number;
  food_days?: number;
  water_days?: number;
}

interface Resource {
  id: string;
  type: string;
  quantity: number;
  unit: string;
  shelter_id: string;
}

interface Allocation {
  shelter_id: string;
  resource_type: string;
  quantity_requested: number;
  quantity_allocated: number;
  explanation: string;
}

interface HistoryPoint {
  tick: number;
  occupancy: number;
  food: number;
  water: number;
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [state, setState] = useState<SimState>({ tick: 0, is_running: false, cyclone_category: 0, cyclone_wind: 0 });
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [apiError, setApiError] = useState(false);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const [resState, resShelters, resResources, resAllocations] = await Promise.all([
          fetch('http://localhost:8000/state').then(r => r.json()),
          fetch('http://localhost:8000/shelters').then(r => r.json()),
          fetch('http://localhost:8000/resources').then(r => r.json()),
          fetch('http://localhost:8000/allocations').then(r => r.json())
        ]);

        setApiError(false);
        setState(resState as SimState);
        setShelters(resShelters as Shelter[]);
        setResources(resResources as Resource[]);
        setAllocations(resAllocations as Allocation[]);

        const s = resState as SimState;
        if (s.tick > 0) {
          setHistory(prev => {
            const last = prev[prev.length - 1];
            if (last && last.tick === s.tick) return prev;

            const shelterList = resShelters as Shelter[];
            const resourceList = resResources as Resource[];

            const totalOcc = shelterList.reduce((acc: number, sh: Shelter) => acc + (sh.current_occupancy || 0), 0);
            const totalFood = resourceList
              .filter((r: Resource) => r.type === 'FOOD')
              .reduce((acc: number, r: Resource) => acc + (r.quantity || 0), 0);
            const totalWater = resourceList
              .filter((r: Resource) => r.type === 'WATER')
              .reduce((acc: number, r: Resource) => acc + (r.quantity || 0), 0);

            return [...prev, { tick: s.tick, occupancy: totalOcc, food: totalFood / 1000, water: totalWater / 1000 }];
          });
        } else if (s.tick === 0) {
          setHistory([]);
        }
      } catch {
        setApiError(true);
      }
    };

    fetchState();
    const interval = setInterval(fetchState, 1000);
    return () => clearInterval(interval);
  }, []);

  const totalOccupancy = shelters.reduce((acc: number, s: Shelter) => acc + (s.current_occupancy || 0), 0);
  const totalCapacity   = shelters.reduce((acc: number, s: Shelter) => acc + (s.capacity || 0), 0);
  const occupancyPct    = totalCapacity > 0 ? ((totalOccupancy / totalCapacity) * 100).toFixed(1) : '0.0';

  const controlAction = async (action: string) => {
    await fetch(`http://localhost:8000/control/${action}`, { method: 'POST' });
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-white p-6 font-sans">
      {apiError && (
        <div className="mb-4 p-3 bg-red-900/60 border border-red-500/40 rounded-xl text-sm text-red-300">
          ⚠ Cannot reach backend at <code>http://localhost:8000</code>. Make sure uvicorn is running.
        </div>
      )}

      <div className="max-w-7xl mx-auto space-y-6">

        {/* ── Header & Controls ─────────────────────────────────────────────── */}
        <div className="flex flex-col md:flex-row justify-between items-center bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur-xl">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">MIRAGE OS</h1>
            <p className="text-neutral-400 text-sm mt-1">Agentic Governance Engine — Disaster Coordination Dashboard</p>
          </div>
          <div className="flex items-center gap-4 mt-4 md:mt-0">
            <div className="flex items-center gap-2 mr-4 bg-black/30 px-4 py-2 rounded-lg border border-white/5">
              <span className="text-xs uppercase tracking-wider text-neutral-400">Tick</span>
              <span className="font-mono font-bold text-xl text-cyan-400">{String(state.tick).padStart(3, '0')}</span>
            </div>
            <button
              onClick={() => controlAction('start')}
              disabled={state.is_running}
              className="p-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl transition-all shadow-[0_0_15px_rgba(37,99,235,0.5)]"
              title="Start simulation"
            >
              <Play size={20} />
            </button>
            <button
              onClick={() => controlAction('pause')}
              disabled={!state.is_running}
              className="p-3 bg-neutral-800 hover:bg-neutral-700 disabled:opacity-50 rounded-xl border border-white/10 transition-all"
              title="Pause simulation"
            >
              <Pause size={20} />
            </button>
            <button
              onClick={() => controlAction('reset')}
              className="p-3 bg-red-900/50 hover:bg-red-800 text-red-300 rounded-xl border border-red-500/20 transition-all"
              title="Reset simulation"
            >
              <RotateCcw size={20} />
            </button>
          </div>
        </div>

        {/* ── KPI Cards ─────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <KpiCard icon={<Wind size={60} />} label="Cyclone Intensity" color="text-red-400">
            <h2 className="text-3xl font-bold text-red-400">CAT {state.cyclone_category}</h2>
            <p className="text-sm text-red-400/70">{state.cyclone_wind} km/h Wind</p>
          </KpiCard>

          <KpiCard icon={<Users size={60} />} label="Shelter Occupancy" color="text-blue-400">
            <h2 className="text-3xl font-bold text-blue-400">{totalOccupancy.toLocaleString()}</h2>
            <p className="text-sm text-blue-400/70">{occupancyPct}% of Capacity</p>
          </KpiCard>

          <KpiCard icon={<Package size={60} />} label="Resource Units" color="text-green-400">
            <h2 className="text-3xl font-bold text-green-400">{resources.length}</h2>
            <p className="text-sm text-green-400/70">Tracked stockpiles</p>
          </KpiCard>

          <KpiCard icon={<FileCheck size={60} />} label="Allocation Decisions" color="text-purple-400">
            <h2 className="text-3xl font-bold text-purple-400">{allocations.length}</h2>
            <p className="text-sm text-purple-400/70">Latest tick plan</p>
          </KpiCard>
        </div>

        {/* ── Charts ────────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard title="Evacuation & Occupancy Curve">
            <AreaChart data={history}>
              <defs>
                <linearGradient id="colorOcc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#60A5FA" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#60A5FA" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
              <XAxis dataKey="tick" stroke="#ffffff50" tick={{ fontSize: 12 }} />
              <YAxis stroke="#ffffff50" tick={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ backgroundColor: '#171717', border: '1px solid #ffffff20', borderRadius: '8px' }} />
              <Area type="monotone" dataKey="occupancy" stroke="#60A5FA" strokeWidth={3} fillOpacity={1} fill="url(#colorOcc)" />
            </AreaChart>
          </ChartCard>

          <ChartCard title="Resource Consumption (k Units)">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
              <XAxis dataKey="tick" stroke="#ffffff50" tick={{ fontSize: 12 }} />
              <YAxis stroke="#ffffff50" tick={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ backgroundColor: '#171717', border: '1px solid #ffffff20', borderRadius: '8px' }} />
              <Line type="monotone" dataKey="food"  stroke="#34D399" strokeWidth={3} dot={false} name="Food" />
              <Line type="monotone" dataKey="water" stroke="#A78BFA" strokeWidth={3} dot={false} name="Water" />
            </LineChart>
          </ChartCard>
        </div>

        {/* ── Data Lists ────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Shelter Status */}
          <div className="bg-white/5 border border-white/10 p-6 rounded-2xl flex flex-col">
            <h3 className="text-neutral-300 font-medium mb-4">Shelter Status</h3>
            <div className="overflow-y-auto max-h-80 pr-1 space-y-3 custom-scrollbar">
              {shelters.length === 0 && <EmptyState label="No shelter data yet." />}
              {shelters.map((s, i) => (
                <div key={i} className="flex justify-between items-center bg-black/20 p-4 rounded-xl border border-white/5">
                  <div>
                    <h4 className="font-medium text-blue-300">{s.name || s.id}</h4>
                    <p className="text-xs text-neutral-500">Zone: {s.zone_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-lg">{s.current_occupancy ?? 0}</p>
                    <p className="text-xs text-neutral-400">/ {s.capacity} cap</p>
                  </div>
                  <div className="text-right w-24">
                    <p className="text-xs text-green-400">{(s.food_days ?? 0).toFixed(1)}d Food</p>
                    <p className="text-xs text-blue-400">{(s.water_days ?? 0).toFixed(1)}d Water</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Allocations */}
          <div className="bg-white/5 border border-white/10 p-6 rounded-2xl flex flex-col">
            <h3 className="text-neutral-300 font-medium mb-4">Latest Allocations</h3>
            <div className="overflow-y-auto max-h-80 pr-1 space-y-3 custom-scrollbar">
              {allocations.length === 0 && <EmptyState label="No allocations generated yet. Press Start." />}
              {allocations.map((a, i) => (
                <div key={i} className="bg-black/20 p-4 rounded-xl border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs font-semibold">{a.resource_type}</span>
                    <div className="flex gap-3">
                      <span className="text-xs text-neutral-400 font-mono">Req: {a.quantity_requested}</span>
                      <span className="text-xs text-cyan-400 font-mono font-bold">Alloc: {a.quantity_allocated}</span>
                    </div>
                  </div>
                  <p className="text-xs text-neutral-400">→ {a.shelter_id}</p>
                  {a.explanation && (
                    <p className="text-xs text-neutral-500 mt-1 truncate">
                      <span className="text-green-500/70">✓</span> {a.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// ─── Sub-components ────────────────────────────────────────────────────────────
function KpiCard({ icon, label, color, children }: {
  icon: React.ReactNode;
  label: string;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white/5 border border-white/10 p-5 rounded-2xl flex flex-col justify-between relative overflow-hidden">
      <div className={`absolute top-0 right-0 p-4 opacity-10 ${color}`}>{icon}</div>
      <p className="text-neutral-400 text-sm font-medium">{label}</p>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/5 border border-white/10 p-6 rounded-2xl h-80">
      <h3 className="text-neutral-300 font-medium mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height="85%">
        {children as React.ReactElement}
      </ResponsiveContainer>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <p className="text-neutral-500 text-sm flex items-center justify-center h-24">{label}</p>
  );
}
