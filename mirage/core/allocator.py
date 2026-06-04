import uuid
from typing import List, Dict, Any
from mirage.models.entities import ResourceRequest, Allocation, AllocationPlan, ResourceType

class ConflictResolver:
    def __init__(self, weights: Dict[str, float] = None):
        # Default weights from Research Blueprint / ADR-008
        self.weights = weights or {
            "risk": 0.3,
            "occupancy": 0.2,
            "urgency": 0.4,
            "accessibility": 0.1
        }

    def resolve(self, tick: int, requests: List[ResourceRequest], inventory: Dict[ResourceType, float], strategy: str = "WEIGHTED") -> AllocationPlan:
        """
        Resolve competing resource requests based on specified strategy.
        Strategies: WEIGHTED (MIRAGE), FCFS, EQUAL, PRO_RATA
        """
        # 1. Group requests by resource type
        by_type = {}
        for req in requests:
            if req.resource_type not in by_type:
                by_type[req.resource_type] = []
            by_type[req.resource_type].append(req)

        all_allocations = []
        total_conflicts = 0

        # 2. Iterate each resource type
        for r_type, req_list in by_type.items():
            available = inventory.get(r_type, 0.0)
            total_requested = sum(r.quantity_requested for r in req_list)

            # Check for conflict
            if total_requested > available:
                total_conflicts += 1
                if strategy == "EQUAL":
                    allocations = self._allocate_equal(req_list, available)
                elif strategy == "FCFS":
                    allocations = self._allocate_fcfs(req_list, available)
                elif strategy == "PRO_RATA":
                    allocations = self._allocate_pro_rata(req_list, available)
                else: # WEIGHTED / MIRAGE
                    allocations = self._allocate_conflicted(req_list, available)
            else:
                allocations = self._allocate_full(req_list)

            all_allocations.extend(allocations)

        summary = f"Processed {len(requests)} requests using {strategy}. Conflicts: {total_conflicts}."
        
        return AllocationPlan(
            tick=tick,
            allocations=all_allocations,
            summary=summary
        )

    def _allocate_equal(self, requests: List[ResourceRequest], available: float) -> List[Allocation]:
        """Baseline: Everyone gets the same amount (capped by request)."""
        count = len(requests)
        share = available / count
        allocations = []
        for req in requests:
            qty = min(req.quantity_requested, share)
            allocations.append(self._create_allocation(req, qty, 0.0, "Baseline (Equal)."))
        return allocations

    def _allocate_fcfs(self, requests: List[ResourceRequest], available: float) -> List[Allocation]:
        """Baseline: First-come-first-served based on memory order (simulated timestamp)."""
        remaining = available
        allocations = []
        for req in requests:
            qty = min(req.quantity_requested, remaining)
            remaining -= qty
            allocations.append(self._create_allocation(req, qty, 0.0, "Baseline (FCFS)."))
        return allocations

    def _allocate_pro_rata(self, requests: List[ResourceRequest], available: float) -> List[Allocation]:
        """Baseline: Divide according to request volume proportions."""
        total_req = sum(r.quantity_requested for r in requests)
        allocations = []
        for req in requests:
            share = (req.quantity_requested / total_req) * available
            allocations.append(self._create_allocation(req, share, 0.0, "Baseline (Pro-rata)."))
        return allocations

    def _allocate_full(self, requests: List[ResourceRequest]) -> List[Allocation]:
        """All requests are granted in full."""
        return [
            Allocation(
                request_id=req.request_id,
                shelter_id=req.shelter_id,
                resource_type=req.resource_type,
                quantity_requested=req.quantity_requested,
                quantity_allocated=req.quantity_requested,
                explanation="Inventory sufficient for full allocation."
            )
            for req in requests
        ]

    def _allocate_conflicted(self, requests: List[ResourceRequest], available: float) -> List[Allocation]:
        """Allocate based on priority scores. Handles equal scores via pro-rata."""
        scored_reqs = []
        for req in requests:
            score = self._calculate_priority_score(req)
            scored_reqs.append({"req": req, "score": score})

        # Sort by score descending
        scored_reqs.sort(key=lambda x: x["score"], reverse=True)

        allocations = []
        remaining_inventory = available
        
        # Process in groups of equal scores
        i = 0
        while i < len(scored_reqs):
            current_score = scored_reqs[i]["score"]
            # Find all items with this score (within epsilon)
            group = []
            while i < len(scored_reqs) and abs(scored_reqs[i]["score"] - current_score) < 1e-6:
                group.append(scored_reqs[i])
                i += 1
            
            # Total requested by this group
            group_requested = sum(item["req"].quantity_requested for item in group)
            
            if remaining_inventory <= 0:
                for item in group:
                    allocations.append(self._create_allocation(item["req"], 0.0, 0.0, "Inventory exhausted."))
            elif remaining_inventory >= group_requested:
                # Everyone in group gets 100%
                for item in group:
                    allocations.append(self._create_allocation(item["req"], item["req"].quantity_requested, item["score"], "Priority allocation (Full)."))
                remaining_inventory -= group_requested
            else:
                # Pro-rata distribution of remaining inventory within the group
                for item in group:
                    share = (item["req"].quantity_requested / group_requested) * remaining_inventory
                    # Floating point safety
                    share = min(share, item["req"].quantity_requested)
                    allocations.append(self._create_allocation(item["req"], share, item["score"], "Priority allocation (Pro-rata)."))
                remaining_inventory = 0

        return allocations

    def _create_allocation(self, req: ResourceRequest, allocated: float, score: float, prefix: str) -> Allocation:
        reason = f"{prefix} Score: {score:.2f}. " + self._explain_score(req)
        return Allocation(
            request_id=req.request_id,
            shelter_id=req.shelter_id,
            resource_type=req.resource_type,
            quantity_requested=req.quantity_requested,
            quantity_allocated=round(allocated, 2), # Round for cleaner outputs
            explanation=reason
        )

    def _calculate_priority_score(self, req: ResourceRequest) -> float:
        """Deterministic weighted scoring model."""
        # Urgency: inverse of stock days remaining (mapped 0.0 to 1.0)
        # Assuming 5 days is the peak window
        urgency = max(0.0, min(1.0, 1.0 - (req.stock_days_remaining / 5.0)))
        
        score = (
            self.weights["risk"] * req.risk_score +
            self.weights["occupancy"] * req.occupancy_ratio +
            self.weights["urgency"] * urgency +
            self.weights["accessibility"] * req.accessibility_score
        )
        return score

    def _explain_score(self, req: ResourceRequest) -> str:
        urgency = max(0.0, min(1.0, 1.0 - (req.stock_days_remaining / 5.0)))
        return (f"Factors: Risk={req.risk_score:.2f}, "
                f"Occupancy={req.occupancy_ratio*100:.0f}%, "
                f"Urgency={urgency:.2f}, "
                f"Access={req.accessibility_score:.2f}")
