import time
from typing import List, Dict, Any
from mirage.models.state import MirageState
from mirage.models.agents import Recommendation, BaseAgent
from mirage.agents.risk import RiskAssessmentAgent
from mirage.agents.resource import ResourceAdvisorAgent
from mirage.agents.approval import GovernanceAdvisorAgent
from mirage.agents.communication import RuleBasedCommunicationAgent
from mirage.agents.shelter import ShelterAgent
from mirage.agents.logistics import LogisticsAgent

from mirage.models.entities import (
    Cyclone, Shelter, Resource, Route, ResourceRequest, ApprovalRequest, AllocationPlan
)

class AgentPipeline:
    """Graph-ready Agent Orchestration Pipeline."""
    
    def __init__(self, recorder: Any = None):
        self.agents: List[BaseAgent] = [
            RiskAssessmentAgent(),
            ResourceAdvisorAgent(),
            GovernanceAdvisorAgent(),
            RuleBasedCommunicationAgent(),
            ShelterAgent(),
            LogisticsAgent()
        ]
        self.recorder = recorder

    def build_state(self, tick: int, blackboard: Any) -> MirageState:
        """State Builder Node: Collects data from Blackboard."""
        
        cyclone_data = blackboard.get_cyclone()
        # Ensure we have minimum data before creating Cyclone object
        cyclone = None
        if cyclone_data and "category" in cyclone_data:
            cyclone = Cyclone(**cyclone_data)
        
        shelters = [Shelter(**s) for s in blackboard.get_shelters()]
        resources = [Resource(**r) for r in blackboard.get_resources()]
        approvals = [ApprovalRequest(**a) for a in (blackboard.get_approvals() if hasattr(blackboard, "get_approvals") else [])]
        allocations = [AllocationPlan(**p) for p in (blackboard.get_allocations() if hasattr(blackboard, "get_allocations") else [])]

        state = MirageState(
            simulation_tick=tick,
            cyclone=cyclone,
            shelters=shelters,
            resources=resources,
            conflicts=[], 
            approval_records=approvals,
            allocation_history=allocations
        )
        return state

    def run_agents(self, state: MirageState) -> List[Recommendation]:
        """Agent Nodes: Run agents in parallel/sequence."""
        all_recommendations = []
        
        for agent in self.agents:
            start_time = time.perf_counter()
            try:
                # Evaluation pass
                eval_data = agent.evaluate(state)
                if agent.name == "ShelterAgent" and self.recorder:
                    for assessment in eval_data.get("assessments", []):
                        self.recorder.log_shelter_assessment(assessment)
                
                # Recommendation pass
                recs = agent.generate_recommendation(state)
                latency = (time.perf_counter() - start_time) * 1000 # ms
                
                for rec in recs:
                    all_recommendations.append(rec)
                    if self.recorder:
                        self.recorder.log_recommendation(rec, latency)
                        
                        # Phase 7: Operational Action Recording
                        action = rec.proposed_action.get("action")
                        if action == "REQUEST_RESOURCES":
                            self.recorder.log_resource_request(state.simulation_tick, rec.proposed_action)
                        elif action == "CREATE_DELIVERY_PLAN":
                            self.recorder.log_delivery_plan(state.simulation_tick, rec.proposed_action)
                        elif action == "LOGISTICS_EVENT":
                            self.recorder.log_logistics_event(
                                state.simulation_tick, 
                                rec.proposed_action.get("type"),
                                rec.proposed_action.get("route_id"),
                                rec.proposed_action.get("status")
                            )
            except Exception as e:
                print(f"Error running agent {agent.name}: {e}")
                
        return all_recommendations

    def aggregate_recommendations(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Recommendation Aggregator Node: Deduplicate and prioritize."""
        # Simple aggregation for v1
        summary = {
            "total": len(recommendations),
            "categories": {},
            "top_priority": []
        }
        
        for rec in recommendations:
            cat = str(rec.category)
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1
            
        # Sort by priority
        sorted_recs = sorted(recommendations, key=lambda x: x.priority, reverse=True)
        summary["top_priority"] = [r.recommendation_id for r in sorted_recs[:5]]
        
        return summary
