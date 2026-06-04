import json
import time
from typing import Dict, Any, List
from mirage.models.agents import BaseAgent, Recommendation
from mirage.models.state import MirageState
from mirage.models.bulletin import CommunicationBulletin
from mirage.core.llm_adapters import BaseLLMAdapter, MockAdapter
from mirage.core.prompts import TEMPLATES

class LLMCommunicationAgent(BaseAgent):
    def __init__(self, adapter: BaseLLMAdapter = None):
        super().__init__("LLMCommunicationAgent", "COMMUNICATION")
        self.adapter = adapter or MockAdapter("mock-v1")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        return {"status": "analyzing"}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        # This agent primarily generates bulletins, but can also recommend communication actions
        recommendations = []
        
        # Every 6 ticks, generate a summary recommendation (actual bulletin is generated via separate method for benchmarking)
        if state.simulation_tick % 6 == 0:
            recommendations.append(Recommendation(
                agent_name=self.name,
                category=self.category,
                confidence=1.0,
                priority=0.5,
                rationale="Scheduled state summary bulletin.",
                action_payload={"type": "GENERATE_BULLETIN"}
            ))
            
        return recommendations

    def generate_bulletin(self, state: MirageState, scenario_id: str) -> CommunicationBulletin:
        template = TEMPLATES["emergency_bulletin"]
        
        cyclone_info = state.cyclone.model_dump() if state.cyclone else {"name": "Unknown", "category": 0, "position": {"lat": 0, "lon": 0}}
        
        user_prompt = template["user"].format(
            tick=state.simulation_tick,
            cyclone=cyclone_info,
            shelters=[s.model_dump() for s in state.shelters],
            resources=[r.model_dump() for r in state.resources],
            governance={"pending_approvals": len(state.approval_records)},
            scenario=scenario_id
        )
        
        response = self.adapter.generate(template["system"], user_prompt)
        
        if not response.success:
            # Fallback to a basic template
            return CommunicationBulletin(
                scenario=scenario_id,
                severity="HIGH",
                headline="Communication Error",
                executive_summary=f"Failed to generate bulletin: {response.error}",
                affected_shelters=[],
                recommended_public_actions=["Please wait for further updates."],
                governance_notes="LLM Failure.",
                confidence=0.0
            )
            
        try:
            # Attempt to parse JSON
            data = json.loads(response.output_text)
            return CommunicationBulletin(
                scenario=scenario_id,
                severity=data.get("severity", "MEDIUM"),
                headline=data.get("headline", "Emergency Bulletin"),
                executive_summary=data.get("executive_summary", ""),
                affected_shelters=data.get("affected_shelters", []),
                recommended_public_actions=data.get("recommended_public_actions", []),
                governance_notes=data.get("governance_notes", ""),
                confidence=data.get("confidence", 1.0),
                model_info=f"{response.provider}/{response.model}"
            )
        except Exception:
            # Fallback for malformed JSON
            return CommunicationBulletin(
                scenario=scenario_id,
                severity="HIGH",
                headline="Report from " + scenario_id,
                executive_summary=response.output_text[:500],
                affected_shelters=[],
                recommended_public_actions=[],
                governance_notes="Parsing error.",
                confidence=0.5,
                model_info=f"{response.provider}/{response.model}"
            )
