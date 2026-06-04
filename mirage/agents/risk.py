from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState

class RiskAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskAssessmentAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        if not state.cyclone:
            return {"risk_level": "LOW", "message": "No active cyclone"}
        
        cat = state.cyclone.category
        wind = state.cyclone.wind_speed_kmh
        
        risk = "LOW"
        if cat >= 4 or wind > 200: risk = "CRITICAL"
        elif cat >= 3 or wind > 150: risk = "HIGH"
        elif cat >= 2: risk = "MODERATE"
        
        return {"risk_level": risk, "cat": cat}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        eval_res = self.evaluate(state)
        if eval_res["risk_level"] in ["HIGH", "CRITICAL"]:
            return [Recommendation(
                tick=state.simulation_tick,
                agent_name=self.name,
                category=RecommendationCategory.RISK,
                priority=0.9 if eval_res["risk_level"] == "CRITICAL" else 0.7,
                confidence=1.0,
                rationale=f"Cyclone intensity {eval_res['cat']} exceeds safety thresholds.",
                proposed_action={"action": "MANDATORY_EVACUATION", "zones": ["Coastal"]}
            )]
        return []
