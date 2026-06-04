import random
from typing import List, Dict, Any
from mirage.dt.base import DigitalTwin
from mirage.models.entities import Cyclone, GeoPoint

class CycloneDT(DigitalTwin):
    def __init__(self, scenario_config: Dict[str, Any], seed: int):
        super().__init__("CycloneDT")
        self.config = scenario_config
        self.seed = seed
        self.rng = random.Random(seed)
        self.sim_id = scenario_config.get("id", "SIM_001")
        self.cyclone_name = scenario_config.get("name", "ALFA")
        
        # Initial state from config
        self.current_cat = scenario_config.get("start_cat", 3)
        self.peak_cat = scenario_config.get("peak_cat", 4)
        self.landfall_tick = scenario_config.get("landfall_tick", 20)
        self.duration = scenario_config.get("duration", 72)
        
        self.current_pos = scenario_config.get("start_pos", {"lat": 18.0, "lon": 85.0})
        self.target_pos = scenario_config.get("landfall_pos", {"lat": 19.0, "lon": 84.0})
        
        self.avg_wind = scenario_config.get("avg_wind", 180.0)
        self.avg_rain = scenario_config.get("avg_rain", 150.0)
        self.avg_surge = scenario_config.get("avg_surge", 3.0)

    def initialize(self, blackboard: Any) -> None:
        """Seed initial cyclone state (category = start_cat) before tick 1."""
        init_data = {
            "id": f"CYC_{self.sim_id}",
            "simulation_id": self.sim_id,
            "name": self.cyclone_name,
            "category": self.current_cat,
            "position": self.current_pos,
            "wind_speed_kmh": self.avg_wind,
            "storm_surge_m": 0.0,
            "rainfall_mm": 0.0,
            "risk_score": self.current_cat / 5.0
        }
        if hasattr(blackboard, "update_cyclone"):
            blackboard.update_cyclone(init_data)

    def update(self, tick: int, blackboard: Any) -> Dict[str, Any]:
        # Intensity model: ramp up to peak at landfall, then weaken
        if tick <= self.landfall_tick:
            progress = tick / self.landfall_tick
            self.current_cat = round(self.config["start_cat"] + (self.peak_cat - self.config["start_cat"]) * progress)
        else:
            # Post-landfall weakening
            progress = (tick - self.landfall_tick) / (self.duration - self.landfall_tick)
            self.current_cat = max(1, round(self.peak_cat - (self.peak_cat - 1) * progress))

        # Position interpolation
        progress_pos = min(1.0, tick / self.landfall_tick)
        lat = self.current_pos["lat"] + (self.target_pos["lat"] - self.current_pos["lat"]) * progress_pos
        lon = self.current_pos["lon"] + (self.target_pos["lon"] - self.current_pos["lon"]) * progress_pos
        
        # Jitter for realism (Seed-based)
        wind_jitter = self.rng.uniform(0.95, 1.05)
        wind_speed = self.avg_wind * wind_jitter
        
        cyclone_data = {
            "id": f"CYC_{self.sim_id}",
            "simulation_id": self.sim_id,
            "name": self.cyclone_name,
            "category": self.current_cat,
            "position": {"lat": lat, "lon": lon},
            "wind_speed_kmh": wind_speed,
            "storm_surge_m": self.avg_surge if tick >= self.landfall_tick - 5 else 0.0,
            "rainfall_mm": self.avg_rain * (self.current_cat / 3.0),
            "risk_score": self.current_cat / 5.0
        }
        
        # Update blackboard (In a real implementation, this would be a Redis write)
        if hasattr(blackboard, "update_cyclone"):
            blackboard.update_cyclone(cyclone_data)
            
        return cyclone_data
