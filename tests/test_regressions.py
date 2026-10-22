from pathlib import Path
from fastapi.testclient import TestClient
from mirage.api.main import app, sim_state
from mirage.core.allocator import ConflictResolver
from mirage.core.blackboard import Blackboard
from mirage.core.governance import GovernanceService
from mirage.dt.resource import ResourceDT
from mirage.dt.shelter import ShelterDT
from mirage.models.entities import (Allocation, AllocationPlan, ApprovalDecision,
    ApprovalStatus, ApprovalRequest, ResourceRequest, ResourceType)
import pytest


def request(rid, shelter, qty=100, risk=.5, occupancy=.5, stock=2, access=1, kind=ResourceType.WATER):
    return ResourceRequest(request_id=rid, shelter_id=shelter, resource_type=kind,
        quantity_requested=qty, risk_score=risk, occupancy_ratio=occupancy,
        stock_days_remaining=stock, accessibility_score=access)


@pytest.mark.parametrize("risk,occupancy,stock,access", [
    (r,o,s,a) for r in (.1,.9) for o in (.1,.9) for s in (.2,4.8) for a in (.1,1.0)
])
def test_priority_score_is_bounded_and_deterministic(risk, occupancy, stock, access):
    resolver = ConflictResolver()
    req = request("r", "s", risk=risk, occupancy=occupancy, stock=stock, access=access)
    assert resolver._calculate_priority_score(req) == resolver._calculate_priority_score(req)
    assert 0 <= resolver._calculate_priority_score(req) <= 1


def test_same_inputs_produce_identical_allocation_plan():
    resolver = ConflictResolver()
    reqs = [request("b", "s2"), request("a", "s1")]
    first = resolver.resolve(3, reqs, {ResourceType.WATER: 100})
    second = resolver.resolve(3, reqs, {ResourceType.WATER: 100})
    assert first.model_dump() == second.model_dump()
    assert [d.reasoning for d in first.decisions] == [d.reasoning for d in second.decisions]


def test_default_strategy_is_weighted_without_llm():
    from mirage.core.engine import SimulationClock
    engine = SimulationClock(Blackboard(), [], None)
    assert engine.strategy == "WEIGHTED"
    plan = engine.allocator.resolve(1, [request("r", "s")], {ResourceType.WATER: 50})
    assert plan.allocations[0].quantity_allocated == 50


def test_legacy_ai_strategy_falls_back_to_weighted_with_warning(caplog):
    plan = ConflictResolver().resolve(1, [request("r", "s")],
        {ResourceType.WATER: 100}, strategy="AI")
    assert plan.decisions[0].strategy_used == "WEIGHTED"
    assert "using deterministic WEIGHTED" in caplog.text


def test_pro_rata_shortage_shares_equally_for_equal_requests():
    resolver = ConflictResolver()
    plan = resolver.resolve(1, [request("a", "a"), request("b", "b")],
                            {ResourceType.WATER: 50}, strategy="PRO_RATA")
    assert {a.quantity_allocated for a in plan.allocations} == {25}

@pytest.mark.parametrize("dimension,high,low", [
    ("risk", .9, .1), ("occupancy", .9, .1), ("stock", .2, 4.8), ("access", 1, 0)
])
def test_each_priority_dimension_can_break_a_tie(dimension, high, low):
    kwargs_high, kwargs_low = {}, {}
    field = {"risk":"risk", "occupancy":"occupancy", "stock":"stock", "access":"access"}[dimension]
    kwargs_high[field], kwargs_low[field] = high, low
    plan = ConflictResolver().resolve(1, [request("high", "high", **kwargs_high),
        request("low", "low", **kwargs_low)], {ResourceType.WATER: 100})
    quantities = {a.request_id: a.quantity_allocated for a in plan.allocations}
    assert quantities["high"] == 100 and quantities["low"] == 0


@pytest.mark.parametrize("quantity,resource,level", [
    (100, ResourceType.WATER, 1), (2001, ResourceType.WATER, 3),
    (10, ResourceType.MEDICAL_KIT, 2), (2001, ResourceType.MEDICAL_KIT, 2)
])
def test_governance_approval_levels(quantity, resource, level):
    gov = GovernanceService(Blackboard(), None)
    plan = AllocationPlan(tick=1, allocations=[Allocation(request_id="r", shelter_id="s",
        resource_type=resource, quantity_requested=quantity, quantity_allocated=quantity, explanation="test")], summary="test")
    req = gov.process_allocation_plan(plan)[0]
    assert req.required_level == level
    for n in range(1, level + 1):
        gov.handle_decision(ApprovalDecision(request_id=req.id, approver_id="human", level=n,
            decision=ApprovalStatus(f"APPROVED_L{n}")))
        if n < level:
            assert req.status == ApprovalStatus.PENDING
    assert req.status == ApprovalStatus(f"APPROVED_L{level}")


def test_governance_veto_stops_pending_approval():
    gov = GovernanceService(Blackboard(), None)
    plan = AllocationPlan(tick=1, allocations=[Allocation(request_id="r", shelter_id="s",
        resource_type=ResourceType.WATER, quantity_requested=50, quantity_allocated=50, explanation="test")], summary="test")
    req = gov.process_allocation_plan(plan)[0]
    gov.handle_decision(ApprovalDecision(request_id=req.id, approver_id="human", level=1,
        decision=ApprovalStatus.REJECTED))
    assert req.status == ApprovalStatus.REJECTED


def test_shelter_never_exceeds_capacity_or_goes_negative():
    shelter = {"id":"s", "capacity":10, "current_occupancy":9, "status":"OPERATIONAL"}
    board = Blackboard(); twin = ShelterDT([shelter], seed=1); twin.initialize(board)
    board.set_pop_movement({"zone":1000})
    twin.update(1, board)
    state = board.get_shelters()[0]
    assert 0 <= state["current_occupancy"] <= state["capacity"]


def test_resource_twin_never_creates_negative_inventory():
    shelter = {"id":"s", "capacity":10, "current_occupancy":10, "status":"OPERATIONAL"}
    resource = {"id":"w", "shelter_id":"s", "type":"WATER", "quantity":1}
    board=Blackboard(); ShelterDT([shelter],1).initialize(board)
    twin=ResourceDT([resource], {"consumption_rates":{"WATER":1}}); twin.initialize(board)
    twin.update(1, board)
    assert all(x["quantity"] >= 0 for x in board.get_resources())


def test_api_state_and_scenario_endpoints_work_in_memory():
    client=TestClient(app)
    assert client.get("/state").status_code == 200
    assert client.get("/scenario").json()["active"]
    assert isinstance(client.get("/shelters").json(), list)


def test_api_alert_broadcast_and_control_reset_work():
    client=TestClient(app)
    result=client.post("/alerts/broadcast", json={"affected_zones":["zone-1"], "message":"Test warning"})
    assert result.status_code == 200 and result.json()["status"] == "SENT"
    assert client.post("/control/reset").status_code == 200



def test_full_demo_runs_without_gemini_key_and_writes_report(monkeypatch):
    import os
    import tempfile
    import main as demo
    original_cwd = Path.cwd()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with tempfile.TemporaryDirectory(dir=original_cwd) as temp_dir:
        monkeypatch.chdir(temp_dir)
        demo.main()
        report = Path("outputs/run_report.html")
        assert report.exists()
        assert "MIRAGE Disaster Response Run" in report.read_text(encoding="utf-8")
        os.chdir(original_cwd)


def test_api_operator_can_approve_or_veto_pending_request():
    client = TestClient(app)
    client.post("/control/reset")
    req = ApprovalRequest(parent_plan_id="plan", target_action={"dispatch": 4}, required_level=1,
        deadline=__import__("datetime").datetime.now() + __import__("datetime").timedelta(hours=1))
    sim_state.clock.governance.requests[req.id] = req
    assert client.get("/approvals").json()[0]["id"] == req.id
    result = client.post("/approvals/decision", json={"request_id":req.id, "approver_id":"operator",
        "level":1, "decision":"REJECTED", "reason":"unsafe route"})
    assert result.status_code == 200 and result.json()["status"] == "REJECTED"
    assert client.post("/approvals/decision", json={"request_id":req.id, "approver_id":"operator",
        "level":1, "decision":"APPROVED_L1"}).status_code == 400
