from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

from mirage.core.engine import SimulationClock
from mirage.dt.cyclone import CycloneDT
from mirage.dt.shelter import ShelterDT
from mirage.dt.population import PopDT
from mirage.dt.resource import ResourceDT
from mirage.dt.infra import InfraDT
from mirage.core.blackboard import Blackboard
from mirage.models.entities import (
    CommunityAlert, AlertBroadcastRequest, ApprovalDecision,
    AlertSeverity, AlertStatus, BroadcastChannel
)
# Research scenarios (validated, unchanged)
from data.scenarios import (
    SCENARIO_A, SCENARIO_B, SCENARIO_C,
    INITIAL_SHELTERS, INITIAL_RESOURCES, DISTRICT_CONFIG, INITIAL_ROUTES
)
# IGAD demo scenario (East Africa / Horn of Africa context)
from data.igad_scenario import (
    IGAD_CYCLONE, IGAD_DISTRICT_CONFIG, IGAD_SHELTERS,
    IGAD_RESOURCES, IGAD_ROUTES, IGAD_MAP_CONFIG
)

app = FastAPI(title="MIRAGE Operational Dashboard - IGAD Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory alert store ────────────────────────────────────────────────────
# DESIGN: same pattern as the Blackboard's in-memory fallback.
# In production, persist to the existing SQLite DB or PostgreSQL.
_alert_store: List[CommunityAlert] = []

# ─── Alert severity thresholds ────────────────────────────────────────────────
ALERT_THRESHOLDS = {
    1: AlertSeverity.INFO,
    2: AlertSeverity.INFO,
    3: AlertSeverity.WARNING,
    4: AlertSeverity.CRITICAL,
    5: AlertSeverity.CRITICAL,
}

def _generate_alert_message(category: int, severity: AlertSeverity, zones: List[str]) -> str:
    """Generate a human-readable alert message for the affected zones."""
    zone_str = ", ".join(zones) if zones else "all affected zones"
    if severity == AlertSeverity.CRITICAL:
        return (
            f"⚠ CRITICAL CYCLONE ALERT — Category {category} cyclone imminent. "
            f"IMMEDIATE EVACUATION REQUIRED for {zone_str}. "
            f"Move to designated shelters NOW. Do not wait."
        )
    elif severity == AlertSeverity.WARNING:
        return (
            f"⚡ CYCLONE WARNING — Category {category} cyclone approaching. "
            f"Prepare to evacuate: {zone_str}. "
            f"Pack emergency supplies and await further instructions from EOC."
        )
    else:
        return (
            f"ℹ CYCLONE WATCH — Tropical system intensifying. "
            f"Monitor conditions in {zone_str}. "
            f"Follow EOC guidance and be ready to act."
        )


def _mock_broadcast(alert: CommunityAlert) -> str:
    """
    MOCK broadcast provider.
    In production: replace this with the Africa's Talking / Twilio SDK call.
    Returns a mock receipt string for audit purposes.
    """
    receipt = (
        f"[MOCK-BROADCAST] Channel={alert.channel.value} | "
        f"Zones={','.join(alert.affected_zones)} | "
        f"Severity={alert.severity.value} | "
        f"SentAt={alert.sent_at.isoformat() if alert.sent_at else 'N/A'}"
    )
    print(receipt)  # Visible in uvicorn server log during demo
    return receipt


def _get_suggested_alert(tick: int, category: int, zones: List[str]) -> Optional[dict]:
    """
    Build a suggested (not yet sent) alert dict when cyclone category ≥ 3.
    Returns None if below threshold or if an identical suggestion already exists.
    """
    if category < 1:
        return None

    severity = ALERT_THRESHOLDS.get(category, AlertSeverity.INFO)

    # Suppress suggestion below Cat 3 for INFO-only (reduce noise)
    if severity == AlertSeverity.INFO and category < 3:
        return None

    # Don't re-suggest if a SENT alert for same category already exists
    already_sent = any(
        a.status == AlertStatus.SENT and a.cyclone_category == category
        for a in _alert_store
    )
    if already_sent:
        return None

    message = _generate_alert_message(category, severity, zones)
    return {
        "hazard_type": "CYCLONE",
        "severity": severity.value,
        "cyclone_category": category,
        "affected_zones": zones,
        "message": message,
        "channel": BroadcastChannel.ALL.value,
        "tick": tick,
    }


# ─── Simulation state ─────────────────────────────────────────────────────────

# Lookup table: scenario name → (cyclone_cfg, district_cfg, shelters, resources, routes)
_SCENARIO_REGISTRY = {
    "igad": {
        "cyclone":   IGAD_CYCLONE,
        "district":  IGAD_DISTRICT_CONFIG,
        "shelters":  IGAD_SHELTERS,
        "resources": IGAD_RESOURCES,
        "routes":    IGAD_ROUTES,
        "label":     IGAD_MAP_CONFIG["scenario_label"],
        "map_center": IGAD_MAP_CONFIG["default_center"],
        "map_zoom":   IGAD_MAP_CONFIG["default_zoom"],
    },
    "research_a": {
        "cyclone":   SCENARIO_A,
        "district":  DISTRICT_CONFIG,
        "shelters":  INITIAL_SHELTERS,
        "resources": INITIAL_RESOURCES,
        "routes":    INITIAL_ROUTES,
        "label":     "Research Scenario A — The Sprint (Bay of Bengal)",
        "map_center": [19.0, 84.5],
        "map_zoom":   8,
    },
    "research_b": {
        "cyclone":   SCENARIO_B,
        "district":  DISTRICT_CONFIG,
        "shelters":  INITIAL_SHELTERS,
        "resources": INITIAL_RESOURCES,
        "routes":    INITIAL_ROUTES,
        "label":     "Research Scenario B — The Slow Burn (Bay of Bengal)",
        "map_center": [19.0, 84.5],
        "map_zoom":   8,
    },
    "research_c": {
        "cyclone":   SCENARIO_C,
        "district":  DISTRICT_CONFIG,
        "shelters":  INITIAL_SHELTERS,
        "resources": INITIAL_RESOURCES,
        "routes":    INITIAL_ROUTES,
        "label":     "Research Scenario C — Coast Buster (Bay of Bengal)",
        "map_center": [19.0, 84.5],
        "map_zoom":   8,
    },
}

class SimulationState:
    def __init__(self):
        self.is_running = False
        self.tick = 0
        self.blackboard = None
        self.clock = None
        self.task = None
        # Default to IGAD scenario for hackathon demo
        self.active_scenario = "igad"

sim_state = SimulationState()

def initialize_simulation(scenario_name: Optional[str] = None):
    """Initialise (or reinitialise) the simulation with the named scenario.
    Defaults to the IGAD demo scenario. Research scenarios A/B/C are available
    but preserved untouched for the validated research evaluation.
    """
    name = scenario_name or sim_state.active_scenario or "igad"
    if name not in _SCENARIO_REGISTRY:
        name = "igad"
    sim_state.active_scenario = name
    cfg = _SCENARIO_REGISTRY[name]

    db_url = os.getenv("DATABASE_URL")
    sim_state.blackboard = Blackboard(os.getenv("REDIS_URL"), db_url=db_url)
    sim_state.blackboard.set_simulation_id(f"demo_{name}")

    dt_engine = [
        CycloneDT(cfg["cyclone"], 101),
        InfraDT(cfg["routes"], 101),
        PopDT(cfg["district"], 101),
        ShelterDT(cfg["shelters"], 101),
        ResourceDT(cfg["resources"], {"consumption_rates": {"FOOD": 0.05, "WATER": 0.25}})
    ]

    sim_state.clock = SimulationClock(sim_state.blackboard, dt_engine, recorder=None, baseline="MIRAGE", auto_approve=False)
    sim_state.tick = 0
    sim_state.is_running = False

    for dt in dt_engine:
        dt.initialize(sim_state.blackboard)

initialize_simulation()

async def run_simulation_loop():
    while sim_state.is_running and sim_state.tick < 72:
        sim_state.tick += 1
        sim_state.clock.execute_tick(sim_state.tick)
        await asyncio.sleep(1.0)
    sim_state.is_running = False


# ─── Core simulation endpoints ────────────────────────────────────────────────

@app.get("/state")
def get_state():
    if not sim_state.blackboard:
        return {}
    cyclone = sim_state.blackboard.get_cyclone() or {}
    category = cyclone.get("category", 0)
    tick = sim_state.tick

    # Derive affected zones from scenario config
    affected_zones = [z["id"] for z in DISTRICT_CONFIG.get("zones", [])
                      if z.get("type") in ("Coastal", "Urban")]

    suggested_alert = _get_suggested_alert(tick, category, affected_zones)

    return {
        "tick": tick,
        "is_running": sim_state.is_running,
        "cyclone_category": category,
        "cyclone_wind": cyclone.get("wind_speed_kmh", 0),
        "cyclone_position": cyclone.get("position"),
        "storm_surge_m": cyclone.get("storm_surge_m", 0),
        # Alert suggestion — frontend shows a "Send Alert" CTA when this is non-null
        "suggested_alert": suggested_alert,
    }

@app.get("/shelters")
def get_shelters():
    if not sim_state.blackboard:
        return []
    return sim_state.blackboard.get_shelters()

@app.get("/resources")
def get_resources():
    if not sim_state.blackboard:
        return []
    return sim_state.blackboard.get_resources()

@app.get("/allocations")
def get_allocations():
    if not sim_state.blackboard:
        return []
    plans = sim_state.blackboard.get_allocations()
    # Sort plans by tick descending
    plans.sort(key=lambda x: x.get("tick", 0), reverse=True)
    
    all_decisions = []
    for plan in plans:
        decisions = plan.get("decisions", [])
        all_decisions.extend(decisions)
        
    all_decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return all_decisions[:50]

@app.get("/approvals")
def get_approvals():
    if not sim_state.clock:
        return []
    return [req.model_dump(mode="json") for req in sim_state.clock.governance.requests.values()]


@app.post("/approvals/decision")
def decide_approval(decision: ApprovalDecision):
    if not sim_state.clock or decision.request_id not in sim_state.clock.governance.requests:
        raise HTTPException(status_code=404, detail="Approval request not found")
    try:
        sim_state.clock.governance.handle_decision(decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    req = sim_state.clock.governance.requests[decision.request_id]
    return req.model_dump(mode="json")


@app.get("/map-data")
def get_map_data():
    """
    Returns all geo-structured data needed by the Leaflet map panel:
      - cyclone: position, category, impact_radius_km
      - shelters: id, name, location, capacity, current_occupancy, status
      - routes: id, origin, destination, status
    Impact radius is a simple estimate: 20 km per category, min 30 km.
    In production this would come from a proper meteorological model.
    """
    cyclone_raw = (sim_state.blackboard.get_cyclone() or {}) if sim_state.blackboard else {}
    shelters_raw = sim_state.blackboard.get_shelters() if sim_state.blackboard else []

    category = cyclone_raw.get("category", 0)
    impact_radius_km = max(30, category * 20)  # rough estimate for demo

    cyclone_geo = None
    if cyclone_raw.get("position"):
        pos = cyclone_raw["position"]
        cyclone_geo = {
            "lat": pos.get("lat", 0),
            "lon": pos.get("lon", 0),
            "category": category,
            "wind_speed_kmh": cyclone_raw.get("wind_speed_kmh", 0),
            "storm_surge_m": cyclone_raw.get("storm_surge_m", 0),
            "impact_radius_km": impact_radius_km,
        }

    shelters_geo = []
    for s in shelters_raw:
        loc = s.get("location") or {}
        if loc.get("lat") and loc.get("lon"):
            cap = s.get("capacity", 1)
            occ = s.get("current_occupancy", 0)
            shelters_geo.append({
                "id": s.get("id"),
                "name": s.get("name", s.get("id")),
                "lat": loc["lat"],
                "lon": loc["lon"],
                "capacity": cap,
                "current_occupancy": occ,
                "occupancy_ratio": round(occ / cap, 3) if cap > 0 else 0,
                "food_days": s.get("food_days", 0),
                "water_days": s.get("water_days", 0),
                "status": s.get("status", "OPERATIONAL"),
                "zone_id": s.get("zone_id", ""),
                "overflow_risk": s.get("overflow_risk", 0),
            })

    # Routes from scenario config (static topology, status from blackboard)
    routes_geo = []
    for r in INITIAL_ROUTES:
        routes_geo.append({
            "id": r.get("id"),
            "origin": r.get("origin"),
            "destination": r.get("destination"),
            "status": r.get("status", "CLEAR"),
            "distance_km": r.get("distance_km", 0),
        })

    return {
        "tick": sim_state.tick,
        "cyclone": cyclone_geo,
        "shelters": shelters_geo,
        "routes": routes_geo,
    }


# ─── Alert endpoints ──────────────────────────────────────────────────────────

@app.get("/alerts")
def get_alerts():
    """Return all alerts (SENT and DISMISSED), newest first."""
    return [a.model_dump() for a in reversed(_alert_store)]


@app.post("/alerts/broadcast")
def broadcast_alert(req: AlertBroadcastRequest):
    """
    Broadcast a community alert.
    Called by the EOC operator from the dashboard (either from a suggestion
    or manually). The actual send is MOCKED — see _mock_broadcast().

    To integrate a real SMS/USSD provider (e.g. Africa's Talking):
        Replace _mock_broadcast() with the provider's SDK call.
    """
    cyclone = (sim_state.blackboard.get_cyclone() or {}) if sim_state.blackboard else {}
    category = cyclone.get("category", 0)
    severity = ALERT_THRESHOLDS.get(category, AlertSeverity.INFO)

    message = req.message or _generate_alert_message(category, severity, req.affected_zones)

    alert = CommunityAlert(
        tick=sim_state.tick,
        hazard_type="CYCLONE",
        severity=severity,
        cyclone_category=category,
        affected_zones=req.affected_zones,
        message=message,
        channel=req.channel,
        status=AlertStatus.SENT,
        sent_by=req.sent_by,
        sent_at=datetime.now(),
    )

    # MOCK broadcast — logs to console; replace with real provider in production
    alert.mock_delivery_log = _mock_broadcast(alert)

    _alert_store.append(alert)
    return alert.model_dump()


@app.post("/alerts/dismiss-suggestion")
def dismiss_suggestion():
    """
    Operator explicitly dismisses the current auto-suggestion without sending.
    Records a DISMISSED entry so the same suggestion won't re-appear this tick.
    """
    cyclone = (sim_state.blackboard.get_cyclone() or {}) if sim_state.blackboard else {}
    category = cyclone.get("category", 0)
    severity = ALERT_THRESHOLDS.get(category, AlertSeverity.INFO)
    zones = [z["id"] for z in DISTRICT_CONFIG.get("zones", [])
             if z.get("type") in ("Coastal", "Urban")]

    dismissed = CommunityAlert(
        tick=sim_state.tick,
        hazard_type="CYCLONE",
        severity=severity,
        cyclone_category=category,
        affected_zones=zones,
        message="[Dismissed by operator]",
        status=AlertStatus.DISMISSED,
        sent_by="EOC_OPERATOR",
    )
    _alert_store.append(dismissed)
    return {"status": "dismissed"}


# ─── Control endpoints ────────────────────────────────────────────────────────

@app.get("/scenario")
def get_scenario():
    """Return metadata about the currently active scenario."""
    name = sim_state.active_scenario or "igad"
    cfg = _SCENARIO_REGISTRY.get(name, _SCENARIO_REGISTRY["igad"])
    return {
        "active": name,
        "label": cfg["label"],
        "map_center": cfg["map_center"],
        "map_zoom": cfg["map_zoom"],
        "available": list(_SCENARIO_REGISTRY.keys()),
    }


@app.post("/control/scenario/{scenario_name}")
def switch_scenario(scenario_name: str):
    """
    Switch the active scenario and reset the simulation.
    Valid values: igad | research_a | research_b | research_c

    NOTE: Switching to research_a/b/c will use the validated research scenario
    data. The research engine's 45-run evaluation matrix in /scripts/ is
    not affected — it manages its own simulation lifecycle.
    """
    if scenario_name not in _SCENARIO_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario_name}'. Valid: {list(_SCENARIO_REGISTRY.keys())}"
        )
    sim_state.is_running = False
    _alert_store.clear()
    initialize_simulation(scenario_name)
    return {
        "status": "switched",
        "scenario": scenario_name,
        "label": _SCENARIO_REGISTRY[scenario_name]["label"],
    }


@app.post("/control/start")
async def start_sim():
    if not sim_state.is_running:
        sim_state.is_running = True
        sim_state.task = asyncio.create_task(run_simulation_loop())
    return {"status": "started"}

@app.post("/control/pause")
def pause_sim():
    sim_state.is_running = False
    return {"status": "paused"}

@app.post("/control/reset")
def reset_sim():
    sim_state.is_running = False
    _alert_store.clear()
    initialize_simulation()  # Reinitialises with the currently active scenario
    return {"status": "reset"}
