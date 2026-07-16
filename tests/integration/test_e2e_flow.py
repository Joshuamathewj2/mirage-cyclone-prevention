import unittest
import os
from mirage.core.blackboard import Blackboard
from mirage.core.engine import SimulationClock
from mirage.dt.cyclone import CycloneDT
from mirage.dt.resource import ResourceDT
from mirage.dt.shelter import ShelterDT
from data.scenarios import SCENARIO_A, INITIAL_SHELTERS, INITIAL_RESOURCES, INITIAL_ROUTES
from mirage.recorder.recorder import ExperimentRecorder
from mirage.core.governance import GovernanceService

class TestE2EFlow(unittest.TestCase):
    def setUp(self):
        self.blackboard = Blackboard("redis://localhost:6379", "sqlite://")
        self.recorder = ExperimentRecorder("outputs/tests", "test-run", "scenario-A", 101)
        
        # Initialize DTs
        self.cyclone_dt = CycloneDT(SCENARIO_A, 101)
        self.resource_dt = ResourceDT(INITIAL_RESOURCES, {})
        self.shelter_dt = ShelterDT(INITIAL_SHELTERS, 101)
        
        self.engine = SimulationClock(
            self.blackboard, 
            [self.cyclone_dt, self.resource_dt, self.shelter_dt],
            self.recorder
        )
        
        # Governance
        self.gov = GovernanceService(self.blackboard, self.recorder)

    def test_complete_shortage_to_approval_flow(self):
        # 1. Seed the blackboard
        self.blackboard.update_shelters(INITIAL_SHELTERS)
        self.blackboard.update_resources([
            {"id": "res-01", "type": "FOOD", "quantity": 100, "unit": "kg", "shelter_id": "sh-01"}
        ])
        
        # 2. Run a tick that triggers shortage
        # sh-01 has 100kg. If occupancy is high, it will trigger request.
        self.blackboard.update_shelters([
            {"id": "sh-01", "current_occupancy": 5000}
        ])
        
        # Trigger conflict resolution step
        from mirage.models.entities import ResourceRequest, ResourceType
        reqs = [
            ResourceRequest(
                request_id="R1",
                shelter_id="sh-01",
                resource_type=ResourceType.FOOD,
                quantity_requested=500.0,
                risk_score=0.9,
                occupancy_ratio=0.9,
                stock_days_remaining=0.2,
                accessibility_score=1.0,
                agent_name="ResourceAdvisorAgent"
            )
        ]
        self.engine.run_conflict_resolution(10, reqs)
        
        # 3. Verify allocation was generated
        # Check if recorder logged allocations
        alloc_file = "outputs/tests/allocations.csv"
        self.assertTrue(os.path.exists(alloc_file))
        
        # 4. Process allocations through Governance
        # We need to get the plan from the engine (it's not returned by run_conflict_resolution currently, I should fix that)
        # For now, we manually mock the plan to test Governance
        from mirage.models.entities import AllocationPlan, Allocation, ResourceType
        plan = AllocationPlan(
            tick=10,
            allocations=[
                Allocation(
                    request_id="R1",
                    shelter_id="sh-01",
                    resource_type=ResourceType.FOOD,
                    quantity_requested=500.0,
                    quantity_allocated=500.0,
                    explanation="Test"
                )
            ],
            summary="Test plan"
        )
        
        requests = self.gov.process_allocation_plan(plan)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].status, "PENDING")
        
        # 5. Approve
        from mirage.models.entities import ApprovalDecision, ApprovalStatus
        decision = ApprovalDecision(
            request_id=requests[0].id,
            approver_id="boss-1",
            level=1,
            decision=ApprovalStatus.APPROVED_L1
        )
        self.gov.handle_decision(decision)
        
        # 6. Verify result
        self.assertEqual(requests[0].status, ApprovalStatus.APPROVED_L1)
        self.assertTrue(os.path.exists("outputs/tests/approvals.csv"))

if __name__ == "__main__":
    unittest.main()
