import time
from typing import List, Dict, Any
from mirage.core.blackboard import Blackboard
from mirage.dt.base import DigitalTwin
from mirage.core.allocator import ConflictResolver
from mirage.core.governance import GovernanceService
from mirage.core.pipeline import AgentPipeline
from mirage.models.entities import ResourceRequest, ResourceType

class SimulationClock:
    def __init__(self, blackboard: Blackboard, dt_engine: List[DigitalTwin], recorder: Any, baseline: str = "MIRAGE"):
        self.blackboard = blackboard
        self.dt_engine = dt_engine
        self.recorder = recorder
        self.allocator = ConflictResolver()
        self.governance = GovernanceService(blackboard, recorder)
        self.agent_pipeline = AgentPipeline(recorder)
        self.current_tick = 0
        self.is_running = False
        self.baseline = baseline
        
        # Configure baseline behavior
        if self.baseline == "Manual":
            self.strategy = "FCFS"
            self.gov_latency_ticks = 4
            self.use_agents = False
        elif self.baseline == "FCFS":
            self.strategy = "FCFS"
            self.gov_latency_ticks = 0
            self.use_agents = False
        elif self.baseline == "Equal":
            self.strategy = "EQUAL"
            self.gov_latency_ticks = 0
            self.use_agents = False
        elif self.baseline == "Dashboard":
            self.strategy = "PRO_RATA"
            self.gov_latency_ticks = 2
            self.use_agents = False
        else: # MIRAGE / Rule-Based
            self.strategy = "AI"
            self.gov_latency_ticks = 0
            self.use_agents = True

    def run(self, max_ticks: int, speed_multiplier: float = 1.0):
        self.is_running = True
        print(f"Simulation started: {max_ticks} ticks at {speed_multiplier}x speed.")

        # Seed initial Blackboard state from all DTs before tick 1
        for dt in self.dt_engine:
            dt.initialize(self.blackboard)

        for tick in range(1, max_ticks + 1):
            if not self.is_running:
                break

            self.current_tick = tick
            self.execute_tick(tick)

        print("Simulation completed.")

    def execute_tick(self, tick: int):
        print(f"--- TICK {tick} ---")

        # Step 1: Cyclone DT — update intensity and position
        cyclone_dt = self.get_dt("CycloneDT")
        if cyclone_dt:
            cyclone_dt.update(tick, self.blackboard)

        # Step 2: Infra DT — road/route blockage from storm damage
        infra_dt = self.get_dt("InfraDT")
        if infra_dt:
            infra_res = infra_dt.update(tick, self.blackboard)
            infra_updates = infra_res.get("infra_updates", []) if isinstance(infra_res, dict) else []
            if infra_updates:
                self.blackboard.update_infra(infra_updates)
            for update in infra_updates:
                if update.get("status") == "BLOCKED" and self.recorder:
                    self.recorder.log_event(tick, "INFRA_FAILURE", update)

        # Step 3: Population DT — compute evacuation movement driven by cyclone risk
        pop_dt = self.get_dt("PopDT")
        if pop_dt:
            pop_res = pop_dt.update(tick, self.blackboard)
            self.blackboard.set_pop_movement(pop_res.get("movements", {}))

        # Step 4: Shelter DT — distribute arrivals and update occupancy
        shelter_dt = self.get_dt("ShelterDT")
        if shelter_dt:
            shelter_dt.update(tick, self.blackboard)
            # ShelterDT writes directly to blackboard internally; no extra call needed

        # Step 5: Resource DT — consume resources based on occupancy; compute food/water days
        resource_dt = self.get_dt("ResourceDT")
        if resource_dt:
            res_res = resource_dt.update(tick, self.blackboard)
            self.blackboard.update_resources(res_res.get("resource_updates", []))

        # Step 6: Event bus sync
        self.blackboard.publish_event("system", {"event": "WORLD_STATE_UPDATED", "tick": tick})

        # Step 7: Agent Loop (Skipped if baseline is non-agentic)
        recommendations = []
        if self.use_agents:
            state = self.agent_pipeline.build_state(tick, self.blackboard)
            recommendations = self.agent_pipeline.run_agents(state)
            self.agent_pipeline.aggregate_recommendations(recommendations)
        
        # Step 8: Collect Resource Requests from Agents (or simulate manual requests for baselines)
        agent_requests = []
        if self.use_agents:
            for rec in recommendations:
                if rec.proposed_action.get("action") == "REQUEST_RESOURCES":
                    payload = rec.proposed_action
                    req = ResourceRequest(
                        shelter_id=payload.get("shelter_id"),
                        resource_type=payload.get("resource_type"),
                        quantity_requested=payload.get("quantity", 1000),
                        risk_score=rec.priority,
                        occupancy_ratio=0.5, 
                        stock_days_remaining=2.0,
                        accessibility_score=1.0,
                        agent_name=rec.agent_name
                    )
                    agent_requests.append(req)
        else:
            # Baseline Simulation: Simple periodic requests from all shelters 
            # representing "Manual" polling/requests
            if tick % 6 == 0:
                shelters = self.blackboard.get_shelters()
                for s in shelters:
                    req = ResourceRequest(
                        shelter_id=s["id"],
                        resource_type=ResourceType.WATER,
                        quantity_requested=1000,
                        risk_score=0.5,
                        occupancy_ratio=s.get("current_occupancy", 0)/s.get("capacity", 1),
                        stock_days_remaining=s.get("water_days", 2.0),
                        accessibility_score=1.0,
                        agent_name="Manual Dispatch"
                    )
                    agent_requests.append(req)
        
        # Step 9: Conflict Resolution (using agent-driven requests and baseline strategy)
        if self.recorder and agent_requests:
            for req in agent_requests:
                # Log for metric consistency
                self.recorder.log_resource_request(tick, {
                    "shelter_id": req.shelter_id,
                    "resource_type": str(req.resource_type),
                    "quantity": req.quantity_requested
                })
        
        self.run_conflict_resolution(tick, agent_requests)
        
        # Step 10: Recorder Snap
        if self.recorder:
            self.recorder.snapshot(tick, self.blackboard)

    def run_conflict_resolution(self, tick: int, requests: List[ResourceRequest]):
        if not requests:
            return
            
        # Updated Depot Inventory for Phase 7
        depot_inventory = {
            ResourceType.FOOD: 500000, # Large capacity to allow flow
            ResourceType.WATER: 500000,
            ResourceType.MEDICAL_KIT: 10000,
            ResourceType.FUEL: 20000
        }
        
        # Log detected conflicts (detected when total requested > depot stock)
        by_type = {}
        for r in requests:
            r_type = r.resource_type if isinstance(r.resource_type, ResourceType) else ResourceType(r.resource_type)
            by_type[r_type] = by_type.get(r_type, 0) + r.quantity_requested
            
        for r_type, total_req in by_type.items():
            if total_req > depot_inventory.get(r_type, 0):
                if self.recorder:
                    self.recorder.log_conflict(tick, r_type, total_req, depot_inventory.get(r_type, 0))

        plan = self.allocator.resolve(tick, requests, depot_inventory, strategy=self.strategy)
        
        # Persist to blackboard
        self.blackboard.update_allocation_plan(plan.model_dump())
        
        if self.recorder:
            self.recorder.log_allocation_plan(tick, plan)

        # Step 10: Governance Processing (with baseline latency)
        if hasattr(self, "pending_plans"):
            # Process plans that have finished their latency period
            ready_to_process = [p for p in self.pending_plans if p["ready_at"] <= tick]
            for p_dict in ready_to_process:
                approval_reqs = self.governance.process_allocation_plan(p_dict["plan"])
                # Auto-approve for simulation baseline tracking
                from mirage.models.entities import ApprovalDecision, ApprovalStatus
                for req in approval_reqs:
                    for level in range(1, req.required_level + 1):
                        decision = ApprovalDecision(
                            request_id=req.id,
                            approver_id="SIM_GOV_BOT",
                            level=level,
                            decision=ApprovalStatus(f"APPROVED_L{level}")
                        )
                        self.governance.handle_decision(decision)
            
            # Keep remaining
            self.pending_plans = [p for p in self.pending_plans if p["ready_at"] > tick]
        else:
            self.pending_plans = []

        # Queue the new plan from this tick
        if plan:
            self.pending_plans.append({
                "plan": plan,
                "ready_at": tick + self.gov_latency_ticks
            })

        # Step 11: Recorder Snap
        if self.recorder:
            self.recorder.snapshot(tick, self.blackboard)

    def get_dt(self, name: str) -> DigitalTwin:
        for dt in self.dt_engine:
            if dt.name == name:
                return dt
        return None
