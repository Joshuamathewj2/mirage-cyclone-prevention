import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from mirage.models.entities import (
    AllocationPlan, ApprovalRequest, ApprovalDecision, 
    ApprovalStatus, Allocation
)

class GovernanceService:
    def __init__(self, blackboard: Any, recorder: Any):
        self.blackboard = blackboard
        self.recorder = recorder
        self.requests: Dict[str, ApprovalRequest] = {}

    def process_allocation_plan(self, plan: AllocationPlan) -> List[ApprovalRequest]:
        """Convert an AllocationPlan into one or more ApprovalRequests."""
        new_requests = []
        for allocation in plan.allocations:
            if allocation.quantity_allocated <= 0:
                continue

            # Task 2: Rejection of unauthorized actions (placeholder check)
            if not self._is_authorized(allocation):
                self._log_governance_violation(allocation, "Unauthorized allocation")
                continue

            # Determine required approval level based on risk/quantity
            level = self._determine_required_level(allocation)
            
            req = ApprovalRequest(
                parent_plan_id=plan.plan_id,
                target_action=allocation.model_dump(),
                required_level=level,
                current_level=0,
                status=ApprovalStatus.PENDING,
                deadline=datetime.now() + timedelta(hours=1) # Escalation timer
            )
            self.requests[req.id] = req
            
            # Persist to Blackboard
            if hasattr(self.blackboard, "update_approval"):
                self.blackboard.update_approval(req.model_dump())
            
            new_requests.append(req)
            
            # Audit log
            if self.recorder:
                self.recorder.log_event(plan.tick, "APPROVAL_REQUESTED", {
                    "request_id": req.id,
                    "shelter_id": allocation.shelter_id,
                    "level": level
                })
        
        return new_requests

    def handle_decision(self, decision: ApprovalDecision):
        """Update request state based on a decision."""
        req = self.requests.get(decision.request_id)
        if not req:
            return

        if req.status != ApprovalStatus.PENDING:
            raise ValueError("Approval request is no longer pending")
        if decision.decision == ApprovalStatus.REJECTED:
            req.status = ApprovalStatus.REJECTED
        elif "APPROVED" in decision.decision:
            expected_level = req.current_level + 1
            if decision.level != expected_level or decision.decision != ApprovalStatus(f"APPROVED_L{expected_level}"):
                raise ValueError(f"Expected approval at level {expected_level}")
            req.current_level += 1
            if req.current_level >= req.required_level:
                # Fully approved
                if req.required_level == 3: req.status = ApprovalStatus.APPROVED_L3
                elif req.required_level == 2: req.status = ApprovalStatus.APPROVED_L2
                else: req.status = ApprovalStatus.APPROVED_L1
            else:
                # Needs higher level
                pass # Still PENDING but current_level updated

        req.updated_at = datetime.now()
        
        # Persist update to Blackboard
        if hasattr(self.blackboard, "update_approval"):
            self.blackboard.update_approval(req.model_dump())
        
        if self.recorder:
            self.recorder.log_event(0, "APPROVAL_DECISION", decision.model_dump())
            # For Task 1 logic, we write to approvals.csv via recorder
            self.recorder.log_approval_update(req, decision)

    def check_escalations(self, current_time: datetime):
        """Task 1: Escalation timer support."""
        for req in self.requests.values():
            if req.status == ApprovalStatus.PENDING and current_time > req.deadline:
                req.status = ApprovalStatus.EXPIRED
                if self.recorder:
                    self.recorder.log_event(0, "APPROVAL_EXPIRED", {"request_id": req.id})

    def _determine_required_level(self, allocation: Allocation) -> int:
        # Business logic for levels:
        # Medical Kits or high quantity (> 1000) require L2+
        if "MEDICAL" in str(allocation.resource_type):
            return 2
        if allocation.quantity_allocated > 2000:
            return 3
        return 1

    def _is_authorized(self, allocation: Allocation) -> bool:
        # Task 2: Track unauthorized actions
        # For now, all deterministic engine actions are authorized
        return True

    def _log_governance_violation(self, allocation: Allocation, reason: str):
        if self.recorder:
            self.recorder.log_event(0, "GOVERNANCE_VIOLATION", {
                "shelter_id": allocation.shelter_id,
                "reason": reason
            })
