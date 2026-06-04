from typing import Dict, Any, List
from mirage.dt.base import DigitalTwin

class ShelterDT(DigitalTwin):
    def __init__(self, shelters_data: List[Dict[str, Any]], seed: int):
        super().__init__("ShelterDT")
        self.shelters = shelters_data  # List of dicts representing initial state

    def initialize(self, blackboard: Any) -> None:
        """Seed initial shelter state into Blackboard before tick 1."""
        blackboard.update_shelters(self.shelters)

    def update(self, tick: int, blackboard: Any) -> Dict[str, Any]:
        pop_movement = blackboard.get_pop_movement() if hasattr(blackboard, "get_pop_movement") else {}
        total_arrivals = sum(pop_movement.values()) if pop_movement else 0

        # Distribute arrivals among shelters based on Utility score
        # Simplified: Distribute equally among operational shelters
        operational_shelters = [s for s in self.shelters if s.get("status") == "OPERATIONAL"]
        if not operational_shelters:
            return {"shelter_updates": []}

        arrivals_per_shelter = total_arrivals // max(1, len(operational_shelters))

        updates = []
        for shelter in self.shelters:
            if shelter.get("status") == "OPERATIONAL":
                new_occ = shelter.get("current_occupancy", 0) + arrivals_per_shelter
                max_cap = shelter["capacity"] * 1.2  # 20% overflow buffer per DSS spec
                shelter["current_occupancy"] = min(int(max_cap), new_occ)

                if shelter["current_occupancy"] >= shelter["capacity"]:
                    shelter["overflow_risk"] = 1.0

                updates.append(shelter.copy())

        # Write updated state back to Blackboard
        if updates:
            blackboard.update_shelters(updates)

        return {"shelter_updates": updates}
