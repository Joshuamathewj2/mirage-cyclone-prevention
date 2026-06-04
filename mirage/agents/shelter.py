import uuid
from typing import List, Dict, Any
from mirage.models.agents import BaseAgent, Recommendation, RecommendationCategory
from mirage.models.state import MirageState
from mirage.models.entities import ShelterAssessment, ResourceRequest, ResourceType

class ShelterAgent(BaseAgent):
    def __init__(self):
        super().__init__("ShelterAgent", "1.0.0")

    def evaluate(self, state: MirageState) -> Dict[str, Any]:
        assessments = []
        for shelter in state.shelters:
            occupancy_rate = shelter.current_occupancy / shelter.capacity if shelter.capacity > 0 else 0
            
            # Simplified logic for Phase 7
            infra_status = "OPERATIONAL"
            if state.cyclone and state.cyclone.category >= 4:
                infra_status = "DAMAGED"
                
            isolation_risk = 0.0
            if state.cyclone and state.cyclone.category >= 3:
                isolation_risk = 0.5
                
            gap = {
                "FOOD": max(0, 7 - shelter.food_days),
                "WATER": max(0, 7 - shelter.water_days)
            }
            
            score = (occupancy_rate * 0.4) + (isolation_risk * 0.3) + (sum(gap.values()) / 14 * 0.3)
            
            assessment = ShelterAssessment(
                shelter_id=shelter.id,
                tick=state.simulation_tick,
                occupancy_rate=occupancy_rate,
                infrastructure_status=infra_status,
                isolation_risk=isolation_risk,
                resource_gap=gap,
                assessment_score=score
            )
            assessments.append(assessment)
            
        return {"assessments": assessments}

    def generate_recommendation(self, state: MirageState) -> List[Recommendation]:
        eval_res = self.evaluate(state)
        recs = []
        
        for assessment in eval_res["assessments"]:
            if assessment.assessment_score > 0.1:
                # Generate a resource request if gap exists
                for r_type, gap_val in assessment.resource_gap.items():
                    if gap_val > 0:
                        recs.append(Recommendation(
                            tick=state.simulation_tick,
                            agent_name=self.name,
                            category=RecommendationCategory.SHELTER,
                            priority=assessment.assessment_score,
                            confidence=0.9,
                            rationale=f"High assessment score ({assessment.assessment_score:.2f}) for {assessment.shelter_id}. Gap: {r_type}",
                            proposed_action={
                                "action": "REQUEST_RESOURCES",
                                "shelter_id": assessment.shelter_id,
                                "resource_type": r_type,
                                "quantity": gap_val * 100 # Scaling factor
                            }
                        ))
                        
        return recs
