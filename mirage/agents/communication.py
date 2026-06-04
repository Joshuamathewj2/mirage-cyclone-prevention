from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState

class RuleBasedCommunicationAgent(BaseAgent):
    def __init__(self):
        super().__init__("RuleBasedCommunicationAgent", "1.0.0")

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
