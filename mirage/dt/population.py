import random
from typing import Dict, Any, List
from mirage.dt.base import DigitalTwin

class PopDT(DigitalTwin):
    def __init__(self, district_config: Dict[str, Any], seed: int):
        super().__init__("PopDT")
        self.seed = seed
        self.rng = random.Random(seed)
        self.zones = district_config.get("zones", [])
        self.total_pop = district_config.get("total_pop", 1000000)
        
        # Initial population distribution
        self.zone_pops = {zone["id"]: zone["population"] for zone in self.zones}
        self.evacuated_pop = {zone["id"]: 0 for zone in self.zones}

    def update(self, tick: int, blackboard: Any) -> Dict[str, Any]:
        # P_evac = (wr * RS) + (wc * Dist_coast) + epsilon
        # For simplicity in v1, we'll use a simplified version based on Cyclone DT output
        cyclone = blackboard.get_cyclone() if hasattr(blackboard, "get_cyclone") else None
        
        if not cyclone:
            return {"status": "waiting_for_cyclone"}

        risk_score = cyclone.get("risk_score", 0.5) # Should be calculated by Risk Agent, but until then...
        # If Risk Agent hasn't run yet, DTs must handle it or use a default.
        # SRS says: risk_assessment reads INCIDENTS, writes risk_score.
        # But DTs run BEFORE agents in the tick (ERS Section 2).
        # So DTs use the PREVIOUS tick's risk score or a simple geometric distance.

        movements = {}
        for zone_id, pop in self.zone_pops.items():
            # Basic evac logic
            evac_rate = (0.7 * risk_score) + self.rng.uniform(-0.05, 0.05)
            evac_rate = max(0.0, min(1.0, evac_rate))
            
            # 0.1% of eligible move per tick to see gradual growth over 72 ticks
            new_evacuees = int((pop - self.evacuated_pop[zone_id]) * evac_rate * 0.001)
            self.evacuated_pop[zone_id] += new_evacuees
            movements[zone_id] = new_evacuees

        return {"movements": movements, "total_evacuated": sum(self.evacuated_pop.values())}
