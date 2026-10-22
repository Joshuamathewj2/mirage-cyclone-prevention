"""Offline MIRAGE research/demo runner."""
import html
import csv
import os
import uuid
from dotenv import load_dotenv
from mirage.core.blackboard import Blackboard
from mirage.core.engine import SimulationClock
from mirage.dt.cyclone import CycloneDT
from mirage.dt.infra import InfraDT
from mirage.dt.population import PopDT
from mirage.dt.shelter import ShelterDT
from mirage.dt.resource import ResourceDT
from mirage.recorder.recorder import ExperimentRecorder
from data.scenarios import SCENARIO_A, DISTRICT_CONFIG, INITIAL_SHELTERS, INITIAL_RESOURCES, INITIAL_ROUTES

load_dotenv()


def write_report(path, run_id, seed, shelters, metrics, duration):
    rows = "".join(f"<tr><td>{html.escape(str(s.get('name', s['id'])))}</td><td>{s.get('current_occupancy', 0)}</td><td>{s.get('capacity', 0)}</td><td>{s.get('food_days', '?')}</td><td>{s.get('water_days', '?')}</td></tr>" for s in shelters)
    content = f"""<!doctype html><html><head><meta charset='utf-8'><title>MIRAGE Run {run_id}</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;color:#17212b}}h1{{color:#075985}}table{{border-collapse:collapse;width:100%;margin:20px 0}}td,th{{border:1px solid #cbd5e1;padding:10px;text-align:left}}th{{background:#e0f2fe}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}.card{{background:#f1f5f9;padding:16px;border-radius:8px}}</style></head><body>
<h1>MIRAGE Disaster Response Run</h1><p>Run <code>{run_id}</code> &middot; Scenario A &middot; seed {seed} &middot; {duration} ticks</p>
<h2>Outcome summary</h2><div class='cards'><div class='card'>Stock-outs observed: <b>{metrics['stockouts']}</b></div><div class='card'>Mean demand fulfilment: <b>{metrics['fulfilment']:.0%}</b></div><div class='card'>Governance decisions: <b>{html.escape(metrics['governance'])}</b></div><div class='card'>Allocation fairness (Gini): <b>{metrics['gini']:.3f}</b></div><div class='card'>Governance approvals: <b>{metrics['approvals']}</b></div></div>
<h2>Final shelter state</h2><table><thead><tr><th>Shelter</th><th>Occupancy</th><th>Capacity</th><th>Food days</th><th>Water days</th></tr></thead><tbody>{rows}</tbody></table>
<p>Allocation numbers were produced by the deterministic weighted conflict resolver. Advisory agents provide recommendations; governance controls approval.</p></body></html>"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    seed = int(os.getenv("MIRAGE_SEED", "101"))
    scenario = SCENARIO_A
    run_id = str(uuid.uuid4())
    print("\n=== MIRAGE | Offline disaster-response simulation ===")
    print("Agents advise | deterministic resolver allocates | humans govern")
    print("Phase 1/4: Initializing digital twins and in-memory blackboard")
    blackboard = Blackboard(os.getenv("REDIS_URL"), os.getenv("DATABASE_URL"))
    blackboard.set_simulation_id(run_id)
    recorder = ExperimentRecorder(output_dir="outputs", run_id=run_id, scenario_id="Scenario A", seed=seed)
    twins = [CycloneDT(scenario, seed), InfraDT(INITIAL_ROUTES, seed), PopDT(DISTRICT_CONFIG, seed),
             ShelterDT(INITIAL_SHELTERS, seed), ResourceDT(INITIAL_RESOURCES,
             {"consumption_rates": {"FOOD": 0.2, "WATER": 1.0, "MEDICAL_KIT": 0.05}})]
    engine = SimulationClock(blackboard, twins, recorder)
    print("Phase 2/4: Running 72 deterministic ticks")
    engine.run(max_ticks=72)
    print("Phase 3/4: Finalizing run metrics")
    recorder.finalize(duration=engine.current_tick, status="SUCCESS")
    shelters = blackboard.get_shelters()
    zero_days = [s for s in shelters if float(s.get("food_days", 1) or 0) <= 0 or float(s.get("water_days", 1) or 0) <= 0]
    ratios = sorted(recorder.metrics["fairness_ratios"])
    n = len(ratios)
    gini = (sum((2*i-n-1)*v for i,v in enumerate(ratios, 1))/(n*sum(ratios))) if n and sum(ratios) else 0.0
    # Fairness per shelter = delivered / requested, so a shelter that got nothing counts as 0
    # (per-allocation ratios skip shelters that were never allocated anything).
    def rows(name):
        try:
            with open(os.path.join("outputs", name), newline="", encoding="utf-8") as stream:
                return [r for r in csv.DictReader(stream) if r.get("run_id") == run_id]
        except OSError:
            return []
    requested, delivered = {}, {}
    for r in rows("shelter_requests.csv"):
        requested[r["shelter_id"]] = requested.get(r["shelter_id"], 0.0) + float(r["quantity"] or 0)
    for r in rows("allocations.csv"):
        delivered[r["shelter_id"]] = delivered.get(r["shelter_id"], 0.0) + float(r["allocated_qty"] or 0)
    ratios = sorted(min(1.0, delivered.get(s, 0.0) / q) for s, q in requested.items() if q > 0)
    n = len(ratios)
    gini = (sum((2*i-n-1)*v for i, v in enumerate(ratios, 1))/(n*sum(ratios))) if n and sum(ratios) else 0.0
    statuses = {}
    for r in rows("approvals.csv"):
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    governance = ", ".join(f"{k}: {v}" for k, v in sorted(statuses.items())) or "none"
    metrics = {"stockouts": len(zero_days), "governance": governance, "gini": gini,
               "fulfilment": (sum(ratios) / n) if n else 1.0, "approvals": recorder.metrics["approvals_granted"]}
    print("\n=== Final results ===")
    print(f"{'Metric':<30}Value")
    print(f"{'Stock-outs (shelters)':<30}{metrics['stockouts']}")
    print(f"{'Mean demand fulfilment':<30}{metrics['fulfilment']:.0%}")
    print(f"{'Governance decisions':<30}{metrics['governance']}")
    print(f"{'Allocation fairness (Gini)':<30}{metrics['gini']:.3f}")
    print(f"{'Governance approvals':<30}{metrics['approvals']}")
    os.makedirs("outputs", exist_ok=True)
    write_report("outputs/run_report.html", run_id, seed, shelters, metrics, engine.current_tick)
    print("Phase 4/4: Self-contained HTML report written to outputs/run_report.html")


if __name__ == "__main__":
    main()
