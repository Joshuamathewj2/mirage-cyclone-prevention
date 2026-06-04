import csv
import os
import uuid
import statistics
from typing import Any, List, Dict
from datetime import datetime
from mirage.models.entities import AllocationPlan

class ExperimentRecorder:
    def __init__(self, output_dir: str, run_id: str, scenario_id: str, seed: int):
        self.output_dir = output_dir
        self.run_id = run_id
        self.scenario_id = scenario_id
        self.seed = seed
        self.metrics = {
            "M6b_approval_rate": 0.0,
            "M9_compliance": 1.0,
            "M10_fairness": 0.0,
            "M11_rec_acceptance": 0.0,
            "M12_agent_latency_avg": 0.0,
            "violations": 0,
            "total_actions": 0,
            "approvals_total": 0,
            "approvals_granted": 0,
            "fairness_ratios": [],
            "recs_total": 0,
            "recs_accepted": 0,
            "agent_latencies": []
        }
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Initialize CSVs
        self.init_csv("simulation_runs.csv", ["run_id", "scenario_id", "seed", "duration", "status", "M6b_rate", "M9_compliance", "M10_fairness", "M11_rec_rate", "M12_latency"])
        self.init_csv("tick_snapshots.csv", ["snapshot_id", "run_id", "tick_index", "cyclone_cat", "total_occupancy", "stock_level_avg"])
        self.init_csv("events.csv", ["event_id", "run_id", "tick_index", "event_type", "payload"])
        self.init_csv("conflicts.csv", ["conflict_id", "run_id", "tick_index", "resource_type", "total_requested", "available_inventory"])
        self.init_csv("allocations.csv", ["allocation_id", "run_id", "tick_index", "request_id", "shelter_id", "resource_type", "allocated_qty", "explanation"])
        self.init_csv("approvals.csv", ["approval_id", "run_id", "request_id", "status", "required_level", "current_level", "latency_sec"])
        self.init_csv("recommendations.csv", ["rec_id", "run_id", "tick", "agent", "category", "confidence", "priority", "latency_ms", "accepted", "rationale"])
        self.init_csv("bulletins.csv", ["bulletin_id", "run_id", "tick", "provider_model", "severity", "headline", "completeness", "consistency", "ease", "grade", "tokens", "cost", "latency_ms"])
        self.init_csv("shelter_assessments.csv", ["assessment_id", "run_id", "tick", "shelter_id", "occupancy_rate", "infra_status", "isolation_risk", "score"])
        self.init_csv("shelter_requests.csv", ["request_id", "run_id", "tick", "shelter_id", "resource_type", "quantity"])
        self.init_csv("delivery_plans.csv", ["plan_id", "run_id", "tick", "source", "target", "resource_type", "quantity", "eta_tick"])
        self.init_csv("logistics_events.csv", ["event_id", "run_id", "tick", "event_type", "route_id", "status"])

        # Log the start of the run
        self.write_csv("simulation_runs.csv", [
            self.run_id, self.scenario_id, self.seed, 0, "RUNNING", 0.0, 1.0, 0.0, 0.0, 0.0
        ])

    def init_csv(self, filename: str, headers: List[str]):
        filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def write_csv(self, filename: str, row: List[Any]):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def snapshot(self, tick: int, blackboard: Any):
        cyclone = blackboard.get_cyclone() or {}
        shelters = blackboard.get_shelters()
        resources = blackboard.get_resources() if hasattr(blackboard, "get_resources") else []
        
        total_occ = sum(s.get("current_occupancy", 0) for s in shelters)
        
        # Calculate avg stock level relative to some baseline (e.g. 100k units total)
        # For simplicity, we just sum the quantities to show the trend
        total_stock = sum(r.get("quantity", 0.0) for r in resources)
        avg_stock = total_stock / 100000.0 # Normalized for trend visibility
        
        snapshot_id = str(uuid.uuid4())
        self.write_csv("tick_snapshots.csv", [
            snapshot_id, 
            self.run_id, 
            tick, 
            cyclone.get("category", 0), 
            total_occ, 
            avg_stock
        ])

    def log_event(self, tick: int, event_type: str, payload: Dict[str, Any]):
        event_id = str(uuid.uuid4())
        self.write_csv("events.csv", [event_id, self.run_id, tick, event_type, str(payload)])

    def log_allocation_plan(self, tick: int, plan: AllocationPlan):
        for alc in plan.allocations:
            alc_id = str(uuid.uuid4())
            self.write_csv("allocations.csv", [
                alc_id, self.run_id, tick, alc.request_id, alc.shelter_id, 
                alc.resource_type, alc.quantity_allocated, alc.explanation
            ])
            
    def log_conflict(self, tick: int, resource_type: str, total_requested: float, available: float):
        con_id = str(uuid.uuid4())
        self.write_csv("conflicts.csv", [
            con_id, self.run_id, tick, resource_type, total_requested, available
        ])

    def log_approval_update(self, req: Any, decision: Any):
        latency = (decision.processed_at - req.created_at).total_seconds()
        self.write_csv("approvals.csv", [
            str(uuid.uuid4()), self.run_id, req.id, req.status, req.required_level, req.current_level, round(latency, 2)
        ])
        
        self.metrics["approvals_total"] += 1
        if "APPROVED" in str(req.status):
            self.metrics["approvals_granted"] += 1

    def log_governance_violation(self, tick: int, payload: Dict[str, Any]):
        self.metrics["violations"] += 1
        self.log_event(tick, "GOVERNANCE_VIOLATION", payload)

    def log_allocation_plan(self, tick: int, plan: AllocationPlan):
        for alc in plan.allocations:
            alc_id = str(uuid.uuid4())
            self.write_csv("allocations.csv", [
                alc_id, self.run_id, tick, alc.request_id, alc.shelter_id, 
                alc.resource_type, alc.quantity_allocated, alc.explanation
            ])
            
            # For fairness: Ratio of (Allocated / Requested)
            if alc.quantity_requested > 0:
                ratio = alc.quantity_allocated / alc.quantity_requested
                self.metrics["fairness_ratios"].append(ratio)

    def log_recommendation(self, rec: Any, latency_ms: float):
        self.write_csv("recommendations.csv", [
            rec.recommendation_id, self.run_id, rec.tick, rec.agent_name, 
            rec.category, rec.confidence, rec.priority, round(latency_ms, 2), 
            rec.accepted, rec.rationale
        ])
        self.metrics["recs_total"] += 1
        if rec.accepted:
            self.metrics["recs_accepted"] += 1
        self.metrics["agent_latencies"].append(latency_ms)

    def log_bulletin(self, tick: int, bulletin: Any, llm_metadata: Dict[str, Any], evaluation: Dict[str, Any]):
        self.write_csv("bulletins.csv", [
            bulletin.bulletin_id, self.run_id, tick, 
            bulletin.model_info, bulletin.severity, bulletin.headline,
            evaluation.get("completeness", 0), evaluation.get("consistency", 0),
            evaluation.get("ease", 0), evaluation.get("grade", 0),
            llm_metadata.get("tokens", 0), llm_metadata.get("cost", 0),
            llm_metadata.get("latency_ms", 0)
        ])

    def log_shelter_assessment(self, assessment: Any):
        self.write_csv("shelter_assessments.csv", [
            assessment.id, self.run_id, assessment.tick, assessment.shelter_id,
            round(assessment.occupancy_rate, 2), assessment.infrastructure_status,
            round(assessment.isolation_risk, 2), round(assessment.assessment_score, 2)
        ])

    def log_resource_request(self, tick: int, req: Any):
        self.write_csv("shelter_requests.csv", [
            str(uuid.uuid4()), self.run_id, tick, req.get("shelter_id"),
            req.get("resource_type"), req.get("quantity")
        ])

    def log_delivery_plan(self, tick: int, plan: Any):
        self.write_csv("delivery_plans.csv", [
            str(uuid.uuid4()), self.run_id, tick, plan.get("source_depot_id", "DEPOT_01"),
            plan.get("shelter_id"), plan.get("resource_type"), plan.get("quantity"), 
            tick + 4 # ETA placeholder
        ])

    def log_logistics_event(self, tick: int, event_type: str, route_id: str, status: str):
        self.write_csv("logistics_events.csv", [
            str(uuid.uuid4()), self.run_id, tick, event_type, route_id, status
        ])

    def finalize(self, duration: int, status: str = "SUCCESS"):
        # Calculate final metrics
        if self.metrics["approvals_total"] > 0:
            self.metrics["M6b_approval_rate"] = self.metrics["approvals_granted"] / self.metrics["approvals_total"]
        
        if self.metrics["total_actions"] > 0:
            self.metrics["M9_compliance"] = 1.0 - (self.metrics["violations"] / self.metrics["total_actions"])
            
        if len(self.metrics["fairness_ratios"]) > 1:
            mean = statistics.mean(self.metrics["fairness_ratios"])
            stdev = statistics.stdev(self.metrics["fairness_ratios"])
            self.metrics["M10_fairness"] = stdev / mean if mean > 0 else 0.0
            
        if self.metrics["recs_total"] > 0:
            self.metrics["M11_rec_acceptance"] = self.metrics["recs_accepted"] / self.metrics["recs_total"]
        if self.metrics["agent_latencies"]:
            self.metrics["M12_agent_latency_avg"] = statistics.mean(self.metrics["agent_latencies"])

        # Update simulation_runs.csv
        self.write_csv("simulation_runs.csv", [
            self.run_id, self.scenario_id, self.seed, duration, status, 
            self.metrics["M6b_approval_rate"], self.metrics["M9_compliance"], self.metrics["M10_fairness"],
            self.metrics["M11_rec_acceptance"], self.metrics["M12_agent_latency_avg"]
        ])
