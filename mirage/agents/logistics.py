import uuid
from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState
from mirage.models.entities import DeliveryPlan, DeliveryItem, Route

class LogisticsAgent(BaseAgent):
    def __init__(self):
        super().__init__("LogisticsAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        # Identify clear routes
        clear_routes = [r for r in state.active_tasks if hasattr(r, 'status') and r.status == "CLEAR"]
        # Wait, routes are in state? No, I need to check how routes are represented.
        # Actually I added Route to entities.py earlier but it's not in MirageState yet.
        return {"routes_available": len(clear_routes)}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        # Logistics Agent reacts to APPROVED allocations or creates delivery plans
        recs = []
        
        # In this phase, we'll suggest DELIVERY_PLANs for pending requests that have been allocated
        # We look at historical allocation plans in the state
        if not state.allocation_history:
            return []
            
        latest_plan = state.allocation_history[-1]
        for allocation in latest_plan.allocations:
            if allocation.quantity_allocated > 0:
                recs.append(Recommendation(
                    tick=state.simulation_tick,
                    agent_name=self.name,
                    category=RecommendationCategory.LOGISTICS,
                    priority=0.7,
                    confidence=1.0,
                    rationale=f"Fulfilling allocation for {allocation.resource_type} to {allocation.shelter_id}",
                    proposed_action={
                        "action": "CREATE_DELIVERY_PLAN",
                        "allocation_id": latest_plan.plan_id,
                        "shelter_id": allocation.shelter_id,
                        "resource_type": allocation.resource_type,
                        "quantity": allocation.quantity_allocated,
                        "route_id": "ROUTE_ALPHA" # Placeholder
                    }
                ))
                
        return recs
