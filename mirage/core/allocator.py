import uuid
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from mirage.models.entities import ResourceRequest, Allocation, AllocationPlan, ResourceType, AllocationDecision

def generate_reasoning(agent_name: str, resource_type: str, requested: float,
                       allocated: float, strategy: str) -> str:
    import google.generativeai as genai
    import os
    import time
    from dotenv import load_dotenv
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dotenv_path = os.path.join(project_root, ".env")
    load_dotenv(dotenv_path)
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return f"{strategy} strategy allocated {allocated}/{requested} units of {resource_type} to {agent_name}."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.5-flash")
        prompt = (
            f"In one short sentence, explain why the '{strategy}' allocation "
            f"strategy gave {allocated} units of {resource_type} to {agent_name}, "
            f"who requested {requested}. Be concise and factual, no fluff."
        )
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                raise e
    except Exception as e:
        print(f"Gemini reasoning generation failed: {e}")
        return f"{strategy} strategy allocated {allocated}/{requested} units of {resource_type} to {agent_name}."


def derive_decision_metadata(req: ResourceRequest, allocated: float, strategy: str):
    if not req:
        return "Resource Request", "Decision made by allocator.", f"Dispatch {allocated:.0f} units of resource.", "Medium"
        
    res_name = req.resource_type.value if hasattr(req.resource_type, "value") else str(req.resource_type)
    problem = f"{res_name.title()} Shortage"
    if req.occupancy_ratio > 0.85:
        problem = "Shelter Overcrowding"
        
    reason = f"Shelter has {req.stock_days_remaining:.1f} days of {res_name} remaining at {req.occupancy_ratio*100:.0f}% occupancy."
    if req.risk_score > 0.7:
        reason += f" High regional risk score ({req.risk_score:.2f})."
        
    recommended_action = f"Dispatch {allocated:.0f} units of {res_name} to Shelter {req.shelter_id}."
    if allocated == 0:
        recommended_action = f"Decline resource dispatch to Shelter {req.shelter_id} due to depot inventory constraints."
    elif allocated < req.quantity_requested:
        recommended_action = f"Partially dispatch {allocated:.0f} units of {res_name} (requested {req.quantity_requested:.0f}) to Shelter {req.shelter_id}."
        
    score = req.risk_score * 0.4 + req.occupancy_ratio * 0.3 + (1.0 - min(1.0, req.stock_days_remaining / 5.0)) * 0.3
    if score > 0.8:
        priority = "Critical"
    elif score > 0.6:
        priority = "High"
    elif score > 0.3:
        priority = "Medium"
    else:
        priority = "Low"
        
    return problem, reason, recommended_action, priority


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
        Strategies: AI, WEIGHTED (MIRAGE), FCFS, EQUAL, PRO_RATA
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
                elif strategy == "AI":
                    allocations = self._allocate_ai(req_list, available)
                else: # WEIGHTED / MIRAGE
                    allocations = self._allocate_conflicted(req_list, available)
            else:
                if strategy == "AI":
                    allocations = self._allocate_ai(req_list, available)
                else:
                    allocations = self._allocate_full(req_list)

            all_allocations.extend(allocations)

        decisions = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for alloc in all_allocations:
                req = next((r for r in requests if r.request_id == alloc.request_id), None)
                agent_name = req.agent_name if req and hasattr(req, "agent_name") else "Unknown Agent"
                
                future = executor.submit(
                    generate_reasoning,
                    agent_name=agent_name,
                    resource_type=str(alloc.resource_type),
                    requested=alloc.quantity_requested,
                    allocated=alloc.quantity_allocated,
                    strategy=strategy
                )
                futures.append((alloc, agent_name, req, future))
                
            for alloc, agent_name, req, future in futures:
                try:
                    reasoning = future.result(timeout=15.0)
                except Exception as e:
                    print(f"Failed to fetch reasoning: {e}")
                    reasoning = f"{strategy} strategy allocated {alloc.quantity_allocated}/{alloc.quantity_requested} units of {alloc.resource_type} to {agent_name}."
                
                problem, reason, recommended_action, priority = derive_decision_metadata(
                    req, alloc.quantity_allocated, strategy
                )
                
                decisions.append(
                    AllocationDecision(
                        agent_name=agent_name,
                        shelter_id=alloc.shelter_id,
                        resource_type=str(alloc.resource_type),
                        requested=alloc.quantity_requested,
                        allocated=alloc.quantity_allocated,
                        strategy_used=strategy,
                        timestamp=datetime.now(),
                        reasoning=reasoning,
                        problem=problem,
                        reason=reason,
                        recommended_action=recommended_action,
                        priority=priority
                    )
                )

        summary = f"Processed {len(requests)} requests using {strategy}. Conflicts: {total_conflicts}."
        
        return AllocationPlan(
            tick=tick,
            allocations=all_allocations,
            decisions=decisions,
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

    def _allocate_ai(self, requests: List[ResourceRequest], available: float) -> List[Allocation]:
        """AI-based allocation using Gemini with the provided API key."""
        import json
        import os
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        dotenv_path = os.path.join(project_root, ".env")
        load_dotenv(dotenv_path)
        
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"You are an AI Resource Allocator for disaster management. We have {available} units available.\n"
        prompt += "Requests:\n"
        for i, req in enumerate(requests):
            prompt += f"[{i}] RequestID: {req.request_id}, Shelter: {req.shelter_id}, Requested: {req.quantity_requested}, Risk: {req.risk_score:.2f}, Occupancy: {req.occupancy_ratio:.2f}\n"
        
        prompt += """
Allocate the available inventory among the requests optimally.
If available inventory is sufficient, grant all requests in full.
Otherwise, prioritize based on Risk and Occupancy.
Total allocated must not exceed the available amount.
Return ONLY a JSON array of objects. Each object must have:
- "request_id" (string, matching the input RequestID)
- "quantity_allocated" (number)
- "explanation" (string, max 10 words)
Do not use markdown formatting like ```json, just output the raw JSON array.
"""
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text)
            allocations = []
            for item in data:
                req = next((r for r in requests if r.request_id == item.get("request_id")), None)
                if req:
                    allocations.append(
                        Allocation(
                            request_id=req.request_id,
                            shelter_id=req.shelter_id,
                            resource_type=req.resource_type,
                            quantity_requested=req.quantity_requested,
                            quantity_allocated=float(item.get("quantity_allocated", 0.0)),
                            explanation=f"AI: {item.get('explanation', 'Optimal decision.')}"
                        )
                    )
            # Fill in any missing requests with 0 allocation
            processed_ids = {a.request_id for a in allocations}
            for req in requests:
                if req.request_id not in processed_ids:
                    allocations.append(self._create_allocation(req, 0.0, 0.0, "AI: Request not selected."))
            return allocations
        except Exception as e:
            print(f"AI Allocation failed: {e}. Falling back to WEIGHTED.")
            if available >= sum(r.quantity_requested for r in requests):
                return self._allocate_full(requests)
            return self._allocate_conflicted(requests, available)

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
