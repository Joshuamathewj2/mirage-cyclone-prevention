import copy
from typing import Dict, Any, List
from mirage.dt.base import DigitalTwin

class ResourceDT(DigitalTwin):
    def __init__(self, resources_data: List[Dict[str, Any]], config: Dict[str, Any]):
        super().__init__("ResourceDT")
        self.resources = copy.deepcopy(resources_data)
        self.rates = config.get("consumption_rates", {
            "FOOD": 0.05,        # kg/person/tick
            "WATER": 0.25,       # L/person/tick
            "FUEL": 0.1,
            "MEDICAL_KIT": 0.001
        })

    def initialize(self, blackboard: Any) -> None:
        """Seed initial resource state into Blackboard before tick 1."""
        blackboard.update_resources(self.resources)

    def update(self, tick: int, blackboard: Any) -> Dict[str, Any]:
        shelters = blackboard.get_shelters() if hasattr(blackboard, "get_shelters") else []
        updates = []

        # Step 1: Process Deliveries (arriving in the current tick)
        deliveries = blackboard.get_delivery_plans() if hasattr(blackboard, "get_delivery_plans") else []
        for delivery in deliveries:
            if delivery.get("tick") == tick: # Simplified: current tick delivery
                for item in delivery.get("allocation", []):
                    # Find our local resource object and update quantity
                    sid = item.get("shelter_id")
                    rtype = item.get("resource_type")
                    qty = item.get("quantity_allocated", 0)
                    for res in self.resources:
                        if res.get("shelter_id") == sid and res.get("type") == rtype:
                            res["quantity"] += qty

        # Step 2: Consume resources based on occupancy
        for shelter in shelters:
            occupancy = shelter.get("current_occupancy", 0)
            shelter_resources = [r for r in self.resources if r.get("shelter_id") == shelter["id"]]

            for res in shelter_resources:
                rate = self.rates.get(res["type"], 0.0)
                consumed = occupancy * rate
                res["quantity"] = max(0.0, res["quantity"] - consumed)
                updates.append(res.copy())

        # Compute food_days / water_days for each shelter and write back
        shelter_food = {}
        shelter_water = {}
        for res in self.resources:
            sid = res.get("shelter_id")
            if not sid:
                continue
            if res["type"] == "FOOD":
                shelter_food[sid] = shelter_food.get(sid, 0.0) + res["quantity"]
            elif res["type"] == "WATER":
                shelter_water[sid] = shelter_water.get(sid, 0.0) + res["quantity"]

        shelter_updates = []
        for shelter in shelters:
            sid = shelter["id"]
            occ = max(1, shelter.get("current_occupancy", 1))
            food_rate_daily = self.rates.get("FOOD", 0.05) * 24  # ticks are hourly
            water_rate_daily = self.rates.get("WATER", 0.25) * 24
            food_days = shelter_food.get(sid, 0.0) / max(0.001, occ * food_rate_daily)
            water_days = shelter_water.get(sid, 0.0) / max(0.001, occ * water_rate_daily)
            shelter_updates.append({"id": sid, "food_days": round(food_days, 2),
                                    "water_days": round(water_days, 2)})

        if shelter_updates:
            blackboard.update_shelters(shelter_updates)

        return {"resource_updates": updates}
