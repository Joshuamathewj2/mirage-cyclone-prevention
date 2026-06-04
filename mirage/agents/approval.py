from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState

class GovernanceAdvisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("GovernanceAdvisorAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        pending = [r for r in state.approval_records if r.status == "PENDING" or r.status.value == "PENDING"]
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
