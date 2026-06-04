from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation
from mirage.models.state import MirageState
from mirage.models.bulletin import CommunicationBulletin

class RuleBasedCommunicationAgent(BaseAgent):
    def __init__(self):
        super().__init__("RuleBasedCommunicationAgent", "COMMUNICATION")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        return {"status": "analyzing"}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        return []

    def generate_bulletin(self, state: MirageState, scenario_id: str) -> CommunicationBulletin:
        # Rule-based logic
        severity = "LOW"
        if not state.cyclone:
            return CommunicationBulletin(
                scenario=scenario_id,
                severity="LOW",
                headline="Preliminary Report",
                executive_summary="No active cyclone data available.",
                affected_shelters=[],
                recommended_public_actions=[],
                governance_notes="Baseline",
                confidence=0.5
            )

        if state.cyclone.category >= 4:
             severity = "CRITICAL"
        elif state.cyclone.category >= 3:
             severity = "HIGH"
        elif state.cyclone.category >= 2:
             severity = "MEDIUM"
             
        headline = f"CATEGORY {state.cyclone.category} CYCLONE ALERT - TICK {state.simulation_tick}"
        summary = f"The cyclone {state.cyclone.name} is currently a Category {state.cyclone.category}. "
        summary += f"Position: lat {state.cyclone.position.lat}, lon {state.cyclone.position.lon}. "
        
        shelter_names = [s.name for s in state.shelters if s.current_occupancy > 0]
        
        return CommunicationBulletin(
            scenario=scenario_id,
            severity=severity,
            headline=headline,
            executive_summary=summary,
            affected_shelters=shelter_names,
            recommended_public_actions=["Seek shelter immediately.", "Follow local guidance."],
            governance_notes="Deterministic rule-based output.",
            confidence=1.0,
            model_info="RuleBased/Baseline"
        )
