import random
from typing import Dict, Any, List
from mirage.dt.base import DigitalTwin

class InfraDT(DigitalTwin):
    def __init__(self, routes_data: List[Dict[str, Any]], seed: int):
        super().__init__("InfraDT")
        self.routes = routes_data
        self.rng = random.Random(seed)

    def update(self, tick: int, blackboard: Any) -> Dict[str, Any]:
        cyclone = blackboard.get_cyclone() if hasattr(blackboard, "get_cyclone") else None
        updates = []
        
        if not cyclone:
            return {"status": "waiting_for_cyclone"}
            
        wind_speed = cyclone.get("wind_speed_kmh", 0)
        rainfall = cyclone.get("rainfall_mm", 0)
        
        for route in self.routes:
            if route.get("status") == "CLEAR":
                # Probability of failure based on DSS Section 8
                p_fail = 0.0
                if wind_speed > 150 or rainfall > 200:
                    p_fail = 0.1
                
                if self.rng.random() < p_fail:
                    route["status"] = "BLOCKED"
                    route["blockage_reason"] = "Extreme weather (Wind/Rain)"
                    updates.append({
                        "id": route["id"],
                        "status": "BLOCKED",
                        "reason": route["blockage_reason"]
                    })
                    
        return {"infra_updates": updates}
