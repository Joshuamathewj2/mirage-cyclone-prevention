from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState
from mirage.models.entities import ResourceType
import uuid

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

class GovernanceAdvisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("GovernanceAdvisorAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        pending = [r for r in state.approval_records if r.status == "PENDING"]
        return {"pending_approvals": len(pending)}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        eval_res = self.evaluate(state)
        if eval_res["pending_approvals"] > 5:
            return [Recommendation(
                tick=state.simulation_tick,
                agent_name=self.name,
                category=RecommendationCategory.GOVERNANCE,
                priority=0.6,
                confidence=1.0,
                rationale=f"Detected {eval_res['pending_approvals']} pending approvals. Risk of logistics bottleneck.",
                proposed_action={"action": "ESCALATE_APPROVALS", "level": 2}
            )]
        return []

class CommunicationAgent(BaseAgent):
    def __init__(self):
        super().__init__("CommunicationAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        return {"tick": state.simulation_tick, "status": "ACTIVE"}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        # Generate periodic bulletins
        if state.simulation_tick % 6 == 0:
            return [Recommendation(
                tick=state.simulation_tick,
                agent_name=self.name,
                category=RecommendationCategory.COMMUNICATION,
                priority=0.5,
                confidence=1.0,
                rationale="Scheduled state summary bulletin.",
                proposed_action={
                    "action": "BROADCAST_BULLETIN", 
                    "content": f"Status Update at Tick {state.simulation_tick}. Cyclone category: {state.cyclone.category if state.cyclone else 'N/A'}"
                }
            )]
        return []
