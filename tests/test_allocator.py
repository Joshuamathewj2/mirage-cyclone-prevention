import unittest
from datetime import datetime
from mirage.models.entities import ResourceRequest, ResourceType
from mirage.core.allocator import ConflictResolver

class TestConflictResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = ConflictResolver()

    def test_case_1_full_allocation(self):
        """Inventory sufficient for all."""
        reqs = [
            ResourceRequest(shelter_id="S1", resource_type=ResourceType.FOOD, quantity_requested=100, 
                            risk_score=0.5, occupancy_ratio=0.5, stock_days_remaining=3, accessibility_score=1.0)
        ]
        inventory = {ResourceType.FOOD: 500}
        plan = self.resolver.resolve(1, reqs, inventory)
        self.assertEqual(plan.allocations[0].quantity_allocated, 100)
        self.assertIn("sufficient", plan.allocations[0].explanation)

    def test_case_2_simple_shortage(self):
        """Shortage: High risk vs Low risk."""
        reqs = [
            ResourceRequest(request_id="R1", shelter_id="S_HIGH", resource_type=ResourceType.WATER, quantity_requested=1000, 
                            risk_score=0.9, occupancy_ratio=0.8, stock_days_remaining=1, accessibility_score=1.0),
            ResourceRequest(request_id="R2", shelter_id="S_LOW", resource_type=ResourceType.WATER, quantity_requested=1000, 
                            risk_score=0.1, occupancy_ratio=0.1, stock_days_remaining=4, accessibility_score=1.0)
        ]
        inventory = {ResourceType.WATER: 1000}
        plan = self.resolver.resolve(1, reqs, inventory)
        
        # S_HIGH should get the 1000, S_LOW should get 0
        allocations = {a.request_id: a.quantity_allocated for a in plan.allocations}
        self.assertEqual(allocations["R1"], 1000)
        self.assertEqual(allocations["R2"], 0)

    def test_case_3_equal_priority(self):
        """Equal priority: First come first served (deterministic via input order or we could add secondary tie-break)."""
        reqs = [
            ResourceRequest(request_id="R1", shelter_id="S1", resource_type=ResourceType.FOOD, quantity_requested=500, 
                            risk_score=0.5, occupancy_ratio=0.5, stock_days_remaining=2, accessibility_score=1.0),
            ResourceRequest(request_id="R2", shelter_id="S2", resource_type=ResourceType.FOOD, quantity_requested=500, 
                            risk_score=0.5, occupancy_ratio=0.5, stock_days_remaining=2, accessibility_score=1.0)
        ]
        inventory = {ResourceType.FOOD: 500}
        plan = self.resolver.resolve(1, reqs, inventory)
        # One gets it all, others 0.
        allocations = [a.quantity_allocated for a in plan.allocations]
        self.assertIn(500, allocations)
        self.assertIn(0, allocations)

    def test_case_4_inaccessible_route(self):
        """Inaccessible route (Accessibility Score = 0)."""
        reqs = [
            ResourceRequest(request_id="R1", shelter_id="S_BLOCKED", resource_type=ResourceType.FOOD, quantity_requested=100, 
                            risk_score=0.8, occupancy_ratio=0.8, stock_days_remaining=1, accessibility_score=0.0),
            ResourceRequest(request_id="R2", shelter_id="S_CLEAR", resource_type=ResourceType.FOOD, quantity_requested=100, 
                            risk_score=0.7, occupancy_ratio=0.7, stock_days_remaining=1, accessibility_score=1.0)
        ]
        inventory = {ResourceType.FOOD: 100}
        plan = self.resolver.resolve(1, reqs, inventory)
        # S_CLEAR should beat S_BLOCKED despite slightly lower internal metrics because it is reachable.
        allocations = {a.request_id: a.quantity_allocated for a in plan.allocations}
        self.assertEqual(allocations["R2"], 100)

    def test_case_5_urgent_stock_depletion(self):
        """Urgent stock depletion takes priority."""
        reqs = [
            ResourceRequest(request_id="R_LOW_STOCK", shelter_id="S1", resource_type=ResourceType.WATER, quantity_requested=100, 
                            risk_score=0.5, occupancy_ratio=0.5, stock_days_remaining=0.2, accessibility_score=1.0),
            ResourceRequest(request_id="R_HIGH_STOCK", shelter_id="S2", resource_type=ResourceType.WATER, quantity_requested=100, 
                            risk_score=0.5, occupancy_ratio=0.5, stock_days_remaining=4.5, accessibility_score=1.0)
        ]
        inventory = {ResourceType.WATER: 100}
        plan = self.resolver.resolve(1, reqs, inventory)
        allocations = {a.request_id: a.quantity_allocated for a in plan.allocations}
        self.assertEqual(allocations["R_LOW_STOCK"], 100)

    def test_case_6_partial_allocation(self):
        """Partial allocation when inventory is between max and min."""
        reqs = [
            ResourceRequest(request_id="R1", shelter_id="S1", resource_type=ResourceType.FOOD, quantity_requested=1000, 
                            risk_score=0.9, occupancy_ratio=0.9, stock_days_remaining=0, accessibility_score=1.0)
        ]
        inventory = {ResourceType.FOOD: 450}
        plan = self.resolver.resolve(1, reqs, inventory)
        self.assertEqual(plan.allocations[0].quantity_allocated, 450)
        self.assertIn("Partial", plan.allocations[0].explanation)

    def test_case_7_medical_emergency(self):
        """Medical kits competition."""
        reqs = [
            ResourceRequest(request_id="M1", shelter_id="S_MED", resource_type=ResourceType.MEDICAL_KIT, quantity_requested=50, 
                            risk_score=1.0, occupancy_ratio=1.0, stock_days_remaining=0, accessibility_score=1.0),
            ResourceRequest(request_id="M2", shelter_id="S_NORM", resource_type=ResourceType.MEDICAL_KIT, quantity_requested=50, 
                            risk_score=0.2, occupancy_ratio=0.2, stock_days_remaining=5, accessibility_score=1.0)
        ]
        inventory = {ResourceType.MEDICAL_KIT: 50}
        plan = self.resolver.resolve(1, reqs, inventory)
        allocations = {a.request_id: a.quantity_allocated for a in plan.allocations}
        self.assertEqual(allocations["M1"], 50)

    def test_case_8_multiple_shelter_competition(self):
        """Three shelters competing for limited stock."""
        reqs = [
            ResourceRequest(request_id="R1", shelter_id="S1", resource_type=ResourceType.WATER, quantity_requested=500, 
                            risk_score=0.9, occupancy_ratio=0.9, stock_days_remaining=0.5, accessibility_score=1.0),
            ResourceRequest(request_id="R2", shelter_id="S2", resource_type=ResourceType.WATER, quantity_requested=500, 
                            risk_score=0.6, occupancy_ratio=0.6, stock_days_remaining=2.0, accessibility_score=1.0),
            ResourceRequest(request_id="R3", shelter_id="S3", resource_type=ResourceType.WATER, quantity_requested=500, 
                            risk_score=0.3, occupancy_ratio=0.3, stock_days_remaining=4.0, accessibility_score=1.0)
        ]
        inventory = {ResourceType.WATER: 750}
        plan = self.resolver.resolve(1, reqs, inventory)
        allocations = {a.request_id: a.quantity_allocated for a in plan.allocations}
        self.assertEqual(allocations["R1"], 500)
        self.assertEqual(allocations["R2"], 250)
        self.assertEqual(allocations["R3"], 0)

    def test_case_9_no_inventory(self):
        """Inventory is zero."""
        reqs = [
            ResourceRequest(request_id="R1", shelter_id="S1", resource_type=ResourceType.FOOD, quantity_requested=100, 
                            risk_score=1.0, occupancy_ratio=1.0, stock_days_remaining=0, accessibility_score=1.0)
        ]
        inventory = {ResourceType.FOOD: 0}
        plan = self.resolver.resolve(1, reqs, inventory)
        self.assertEqual(plan.allocations[0].quantity_allocated, 0)
        self.assertIn("exhausted", plan.allocations[0].explanation)

    def test_case_10_high_occupancy_priority(self):
        """High occupancy ratio priority."""
        reqs = [
            ResourceRequest(request_id="R_EMPTY", shelter_id="S1", resource_type=ResourceType.FOOD, quantity_requested=100, 
                            risk_score=0.5, occupancy_ratio=0.1, stock_days_remaining=2, accessibility_score=1.0),
            ResourceRequest(request_id="R_FULL", shelter_id="S2", resource_type=ResourceType.FOOD, quantity_requested=100, 
                            risk_score=0.5, occupancy_ratio=1.2, stock_days_remaining=2, accessibility_score=1.0)
        ]
        inventory = {ResourceType.FOOD: 100}
        plan = self.resolver.resolve(1, reqs, inventory)
        allocations = {a.request_id: a.quantity_allocated for a in plan.allocations}
        self.assertEqual(allocations["R_FULL"], 100)

if __name__ == '__main__':
    unittest.main()
