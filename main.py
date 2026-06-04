import os
import uuid
from dotenv import load_dotenv
from mirage.core.blackboard import Blackboard
from mirage.core.engine import SimulationClock
from mirage.dt.cyclone import CycloneDT
from mirage.dt.infra import InfraDT
from mirage.dt.population import PopDT
from mirage.dt.shelter import ShelterDT
from mirage.dt.resource import ResourceDT
from mirage.recorder.recorder import ExperimentRecorder
from data.scenarios import SCENARIO_A, DISTRICT_CONFIG, INITIAL_SHELTERS, INITIAL_RESOURCES, INITIAL_ROUTES

load_dotenv()

def main():
    # Configuration
    seed = 101
    scenario = SCENARIO_A
    run_id = str(uuid.uuid4())
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:mirage_dev@localhost:5432/mirage")
    
    print(f"Initializing MIRAGE Simulation [Run ID: {run_id}]")
    
    # 1. Initialize Blackboard
    blackboard = Blackboard(redis_url, db_url)
    blackboard.set_simulation_id(run_id)
    
    # Pre-seed blackboard with initial data
    blackboard.update_shelters(INITIAL_SHELTERS)
    blackboard.update_resources(INITIAL_RESOURCES)
    # blackboard.update_infra(INITIAL_ROUTES) # Need to implement this in blackboard.py or handle it
    
    # 2. Initialize Recorder
    recorder = ExperimentRecorder(output_dir="outputs", run_id=run_id, scenario_id="Scenario A", seed=seed)
    
    # 3. Initialize Digital Twins
    dt_engine = [
        CycloneDT(scenario, seed),
        InfraDT(INITIAL_ROUTES, seed),
        PopDT(DISTRICT_CONFIG, seed),
        ShelterDT(INITIAL_SHELTERS, seed),
        ResourceDT(INITIAL_RESOURCES, {"consumption_rates": {"FOOD": 0.2, "WATER": 1.0, "MEDICAL_KIT": 0.05}})
    ]
    
    # 4. Initialize Simulation Engine
    engine = SimulationClock(blackboard, dt_engine, recorder)
    
    # 5. Run Simulation
    try:
        engine.run(max_ticks=72, speed_multiplier=10.0)
        recorder.finalize(duration=72, status="SUCCESS")
    except Exception as e:
        print(f"Simulation failed: {e}")
        recorder.finalize(duration=engine.current_tick, status="FAILED")
        raise e

    print(f"Results generated in 'outputs/' folder.")

if __name__ == "__main__":
    main()
