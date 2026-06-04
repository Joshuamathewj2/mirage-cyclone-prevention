from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState

class ResourceAdvisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResourceAdvisorAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        shortages = []
        for res in state.resources:
            if res.quantity < 1000: # Simple threshold
                shortages.append(res.model_dump())
        return {"shortages_count": len(shortages), "items": shortages}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        eval_res = self.evaluate(state)
        recs = []
        for item in eval_res["items"]:
            recs.append(Recommendation(
                tick=state.simulation_tick,
                agent_name=self.name,
                category=RecommendationCategory.LOGISTICS,
                priority=0.8,
                confidence=1.0,
                rationale=f"Low stock detected for {item['type']} at shelter {item['shelter_id']}.",
                proposed_action={"action": "RESTOCK", "resource": item['type'], "target": item['shelter_id']}
            ))
        return recs
