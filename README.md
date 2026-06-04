# MIRAGE — Multi-Agent Intelligent Resource Allocation and Governance Engine

> **Final-Year Research Project** | Deterministic Digital Twin + Agentic Coordination for Disaster Response

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Next.js](https://img.shields.io/badge/Next.js-15-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🌀 Overview

MIRAGE is a research-grade multi-agent system for disaster coordination that combines:
- **Digital Twin Engine** (Cyclone, Population, Shelter, Resource, Infrastructure DTs)
- **Agentic Advisory Layer** (Risk, Shelter, Logistics, Resource agents)
- **Deterministic Conflict Resolution** with WEIGHTED / FCFS / EQUAL / PRO_RATA strategies
- **Governance Workflow** with multi-level approval state machine
- **Research Evaluation Engine** — 45-run evaluation matrix across 5 baselines × 3 scenarios × 3 seeds
- **Live Dashboard** (Next.js + FastAPI) for real-time visualization

---

## 🚀 Quick Start (3 Minutes)

### 1. Backend
```bash
pip install -r requirements.txt
set PYTHONPATH=c:\path\to\mirage_ai_agent   # use `export` on Mac/Linux
uvicorn mirage.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Dashboard
```bash
cd mirage/frontend
npm install
npm run dev
```

Open **http://localhost:3000** → Click **▶ Start** to run the simulation live.

---

## 📊 Evaluation Results

| Baseline  | M3 Efficiency | M5 Fairness | M6 Gov Latency | M10 Resilience |
|-----------|:---:|:---:|:---:|:---:|
| Manual    | 1.00 | 1.000 | 0.074 | 0.981 |
| FCFS      | 1.00 | 1.000 | 0.032 | 0.685 |
| Equal     | 1.00 | 1.000 | 0.045 | 0.293 |
| Dashboard | 1.00 | 1.000 | 0.055 | 0.094 |
| **MIRAGE**| **0.50** | **0.9999** | **0.092** | **0.000** |

> M10=0.00 for MIRAGE reflects **successful evacuation** (shelters full, high resource throughput), not failure.  
> Manual M10=0.98 reflects **empty shelters** — high stock, zero survivors moved.

**H1 (Stock-out Reduction)**: ✅ SUPPORTED  
**H2 (Lead Time Reduction)**: ✅ SUPPORTED — 2.1× faster than Manual  
**H3 (Fairness)**: ✅ SUPPORTED — M5 σ = 0.000088

---

## 🏗️ Architecture

```
Digital Twins ──▶ Blackboard ──▶ Agent Pipeline ──▶ Conflict Resolver ──▶ Governance
  CycloneDT          └── MirageState      Risk Agent       WEIGHTED/FCFS       L1/L2/L3 Approval
  PopDT                                   Shelter Agent    EQUAL / PRO_RATA    Auto-Approve (Sim)
  ShelterDT                               Logistics Agent
  ResourceDT                              Resource Agent
  InfraDT
```

---

## 📁 Project Structure

```
mirage_ai_agent/
├── mirage/
│   ├── api/          # FastAPI backend
│   ├── core/         # Engine, Allocator, Governance, Research
│   ├── dt/           # Digital Twin modules
│   ├── agents/       # Shelter, Risk, Logistics, Resource agents
│   ├── models/       # Pydantic entities
│   ├── recorder/     # ExperimentRecorder
│   └── frontend/     # Next.js dashboard
├── data/             # Scenario configurations
├── outputs/          # Evaluation results
├── paper/            # Research paper drafts
├── docs/figures/     # System diagrams (Mermaid)
├── scripts/          # Evaluation runner
├── DEMO_INSTRUCTIONS.md
├── metric_audit_report.md
├── statistical_validation_report.md
├── FINAL_PROJECT_VERDICT.md
└── requirements.txt
```

---

## 📄 License
MIT © 2026 Joshua Mathew
