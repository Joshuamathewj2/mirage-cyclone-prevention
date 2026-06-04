from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

from mirage.core.engine import SimulationClock
from mirage.dt.cyclone import CycloneDT
from mirage.dt.shelter import ShelterDT
from mirage.dt.population import PopDT
from mirage.dt.resource import ResourceDT
from mirage.dt.infra import InfraDT
from mirage.core.blackboard import Blackboard
from data.scenarios import SCENARIO_A, INITIAL_SHELTERS, INITIAL_RESOURCES, DISTRICT_CONFIG, INITIAL_ROUTES

app = FastAPI(title="MIRAGE Operational Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationState:
    def __init__(self):
        self.is_running = False
        self.tick = 0
        self.blackboard = None
        self.clock = None
        self.task = None

sim_state = SimulationState()

def initialize_simulation():
    # Use in-memory or a local SQLite db
    db_url = "sqlite:///mirage_demo.db"
    # Ensure fresh state
    if os.path.exists("mirage_demo.db"):
        os.remove("mirage_demo.db")
        
    sim_state.blackboard = Blackboard("redis://localhost:6379", db_url=db_url)
    sim_state.blackboard.set_simulation_id("demo_run")
    
    dt_engine = [
        CycloneDT(SCENARIO_A, 101),
        InfraDT(INITIAL_ROUTES, 101),
        PopDT(DISTRICT_CONFIG, 101),
        ShelterDT(INITIAL_SHELTERS, 101),
        ResourceDT(INITIAL_RESOURCES, {"consumption_rates": {"FOOD": 0.05, "WATER": 0.25}})
    ]
    
    sim_state.clock = SimulationClock(sim_state.blackboard, dt_engine, recorder=None, baseline="MIRAGE")
    sim_state.tick = 0
    sim_state.is_running = False
    
    # Initialize the DTs into Blackboard
    for dt in dt_engine:
        dt.initialize(sim_state.blackboard)

initialize_simulation()

async def run_simulation_loop():
    while sim_state.is_running and sim_state.tick < 72:
        sim_state.tick += 1
        # Synchronous tick
        sim_state.clock.execute_tick(sim_state.tick)
        await asyncio.sleep(1.0) # 1 update per second
    
    sim_state.is_running = False

@app.get("/state")
def get_state():
    if not sim_state.blackboard: return {}
    cyclone = sim_state.blackboard.get_cyclone() or {}
    return {
        "tick": sim_state.tick,
        "is_running": sim_state.is_running,
        "cyclone_category": cyclone.get("category", 0),
        "cyclone_wind": cyclone.get("wind_speed_kmh", 0)
    }

@app.get("/shelters")
def get_shelters():
    if not sim_state.blackboard: return []
    return sim_state.blackboard.get_shelters()

@app.get("/resources")
def get_resources():
    if not sim_state.blackboard: return []
    return sim_state.blackboard.get_resources()

@app.get("/allocations")
def get_allocations():
    if not sim_state.blackboard: return []
    plan = sim_state.blackboard.get_allocation_plan() or {}
    return plan.get("allocations", [])

@app.get("/approvals")
def get_approvals():
    return [] # Since simulated governance automatically approves, we could query SQLite, but simpler to skip or use allocations.

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
    initialize_simulation()
    return {"status": "reset"}
