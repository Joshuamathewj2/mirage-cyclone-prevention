import os
import json
import uuid
from typing import List, Dict, Any
from mirage.core.engine import SimulationClock
from mirage.core.blackboard import Blackboard
from mirage.recorder.recorder import ExperimentRecorder
from mirage.dt.cyclone import CycloneDT
from mirage.dt.infra import InfraDT
from mirage.dt.population import PopDT
from mirage.dt.shelter import ShelterDT
from mirage.dt.resource import ResourceDT
from mirage.core.pipeline import AgentPipeline
from data.scenarios import SCENARIO_A, SCENARIO_B, SCENARIO_C, DISTRICT_CONFIG, INITIAL_SHELTERS, INITIAL_RESOURCES

def run_snapshot(scenario_config, seed):
    sim_id = str(uuid.uuid4())[:8]
    blackboard = Blackboard("redis://localhost:6379", "sqlite:///mirage.db")
    recorder = None # We don't need the full recorder for benchmarks
    
    # Init DTs
    cyclone = CycloneDT(scenario_config, seed)
    infra = InfraDT(DISTRICT_CONFIG, seed)
    pop = PopDT(DISTRICT_CONFIG, seed)
    shelter = ShelterDT(INITIAL_SHELTERS, seed)
    resource = ResourceDT(INITIAL_RESOURCES, DISTRICT_CONFIG)
    
    dt_engine = [cyclone, infra, pop, shelter, resource]
    clock = SimulationClock(blackboard, dt_engine, recorder)
    pipeline = AgentPipeline(None)
    
    # Run for a few ticks and capture states
    captured_states = []
    ticks_to_capture = [6, 12, 24, 48]
    
    for tick in range(1, 73):
        clock.execute_tick(tick)
        if tick in ticks_to_capture:
            state = pipeline.build_state(tick, blackboard)
            captured_states.append({
                "tick": tick,
                "scenario_id": scenario_config["id"],
                "seed": seed,
                "state": state.model_dump()
            })
            
    return captured_states

def main():
    scenarios = [SCENARIO_A, SCENARIO_B, SCENARIO_C]
    seeds = [101, 202, 303]
    
    all_benchmarks = []
    
    for sc in scenarios:
        for seed in seeds:
            print(f"Generating benchmarks for {sc['id']} - {seed}")
            states = run_snapshot(sc, seed)
            all_benchmarks.extend(states)
            
    output_path = "data/benchmark_inputs.json"
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_benchmarks, f, indent=2, default=str)
    
    print(f"Exported {len(all_benchmarks)} benchmark inputs to {output_path}")

if __name__ == "__main__":
    main()
