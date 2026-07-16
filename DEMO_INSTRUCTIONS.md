# MIRAGE Local Demonstration Guide

This guide allows project evaluators and hackathon judges to experience the **MIRAGE Early Warning & Early Action Dashboard** within 3 minutes.

---

## 📋 Prerequisites
1. **Python 3.10+** (Install dependencies: `pip install -r requirements.txt`)
2. **Node.js v18+**

---

## ⚡ Step-by-Step Execution

### 1. Start the API Backend (FastAPI)
The backend coordinates the Digital Twins, updates the blackboard, hosts REST endpoints, and manages the simulation loop.

Open a terminal in the project root:
```powershell
# Windows
set PYTHONPATH=c:\mirage_ai_agent
uvicorn mirage.api.main:app --host 0.0.0.0 --port 8000 --reload

# Mac/Linux
export PYTHONPATH=$(pwd)
uvicorn mirage.api.main:app --host 0.0.0.0 --port 8000 --reload
```

*Note: The backend automatically falls back to in-memory mode if Redis is not running locally. No database installation is required.*

### 2. Start the Frontend Dashboard (Next.js)
Open a **new** terminal window and run:
```bash
cd mirage/frontend
npm run dev
```

### 3. Open the Interactive Console
Open your web browser and navigate to: **[http://localhost:3000](http://localhost:3000)**

---

## 🕹️ Interactive Features to Demo

### Part A: Early Warning & Evacuation Simulation
1. You will see the **MIRAGE OS** Dashboard at **Tick 000** loading the custom **Cyclone DEMO-GATI** (IGAD Horn of Africa Regional Scenario).
2. Click the **▶ Play (Blue)** button to run. 
3. Observe:
   - **Intensity Growth**: Wind speed and category scale.
   - **Population Movement**: Shelter occupancies rise dynamically as coastal communities evacuate.
   - **Resource Consumption**: Stockpiles of food and water drop steadily to mimic real-world usage.

### Part B: Community Alert Broadcast (New Early Action Module)
1. Let the simulation run to **Tick 008** (Cyclone intensifies to Category 3).
2. The **Risk Agent** detects that threat level has crossed the severity threshold.
3. A **pulsing red alert suggestion banner** appears at the top of the screen: *"⚡ CYCLONE WARNING — Category 3 cyclone approaching. Prepare to evacuate..."*
4. Click **Broadcast Alert** to dispatch this warning to local communities. The broadcast is logged in the right-hand **Community Alerts** feed.
5. In your backend terminal, you will see a printed dispatch log simulating transmission:
   `[MOCK-BROADCAST] Channel=ALL | Zones=zone_bosaso_coast,...`
6. You can also trigger custom/manual warnings by clicking **+ Manual Broadcast** at any time.

### Part C: Live GIS Map (New Geospatial Module)
1. Click the **Live Map** tab in the top navigation switcher.
2. Watch the live layout update:
   - **Cyclone Tracker**: The eye is marked with an animated, pulsing radar circle showing its category.
   - **Impact Zones**: Dashed circles show the wind hazard boundary and internal storm-surge flood zone.
   - **Shelter Pins**: Color-coded dynamically by capacity (Green <70%, Amber 70-90%, Red >90% overflow risk). Hover/click any shelter to inspect its food/water days and populations.
   - **Supply Routes**: Green lines denote clear access roads. Red dashed lines denote blocked corridors. (Notice the *Coastal Evacuation Corridor* flood blockade as landfall nears).

### Part D: Switch Scenarios (Academic Research Compatibility)
1. On the **Live Map** tab, locate the **Scenario** switcher at the top right.
2. Click **RES-A**, **RES-B**, or **RES-C** to reset the environment and run the academic evaluation baselines (Bay of Bengal scenarios).
3. Click **IGAD** to switch back to the East African demo.
