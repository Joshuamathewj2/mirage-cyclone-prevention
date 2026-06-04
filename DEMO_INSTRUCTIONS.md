# MIRAGE Local Demonstration Guide

This guide allows project examiners to evaluate the **MIRAGE Agentic Governance Engine** visually within 3 minutes.

## Prerequisites
1. **Python 3.10+** (Ensure `pip install -r requirements.txt` has been run)
2. **Node.js v18+**

## Part 1: Start the Backend (FastAPI / Simulation Engine)
The backend loads the MIRAGE Digital Twin engine in the background and sets up the Scenario A (Seed 101) configuration.

Open a terminal in the project root:
```bash
set PYTHONPATH=c:\mirage_ai_agent
uvicorn mirage.api.main:app --host 0.0.0.0 --port 8000
```

*Note for Mac/Linux users: `export PYTHONPATH=$(pwd)`*

## Part 2: Start the Frontend (Next.js Dashboard)
Open a **new** terminal in the project root and navigate to the frontend:
```bash
cd mirage/frontend
npm run dev
```

## Part 3: Using the Dashboard
1. Open your browser and navigate to `http://localhost:3000`
2. You will see the **MIRAGE OS** Dashboard in a paused state at Tick 000.
3. Click the **Play Button** (Blue) to start the simulation.
4. The simulation operates at **1 Tick per Second**, allowing you to observe:
   - Cyclone wind intensity updates
   - Dynamic movement of population into shelters (Evacuation & Occupancy Curve)
   - Real-time stock consumption and replenishment (Food/Water drop-offs)
   - Allocator Agent decisions based on priority heuristics.

Use the **Pause** or **Reset** buttons at any time to freeze or restart the scenario.
