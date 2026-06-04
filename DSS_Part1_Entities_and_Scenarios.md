# MIRAGE — Dataset & Scenario Specification (DSS)
**Version:** 1.0  
**Date:** 2026-06-02  
**Status:** Implementation-Ready  
**Document Owner:** Principal Systems Architect

---

## Section 1 — Dataset Philosophy

### 1.1 Synthetic + Digital Twin Utility
MIRAGE utilizes **synthetic environments driven by Digital Twin dynamics** rather than static historical datasets. This choice is mandatory for three reasons:
1. **Controllability**: Evaluation requires injecting failures (e.g., bridge collapse) at specific ticks to measure agent response times ($M1$, $M5$). Historical data lacks this granular control.
2. **Causality**: The population's evacuation behavior must respond dynamically to the cyclone's category shift as predicted by the Risk Agent. A static CSV cannot model this feedback loop.
3. **Sparsity**: Real disaster data is notoriously incomplete, fragmented, and noisy. Implementation-ready testing requires a "Gold Standard" environment where every variable is observable.

### 1.2 Relationship: Simulation vs. Evaluation
The simulation generates the **exogenous world state** (weather, road status). The evaluation measures the **endogenous agent response** (allocation efficiency, decision speed). The "Dataset" is the starting seed + the accumulated state-changes over $N$ ticks.

### 1.3 Reproducibility Requirements
Every simulation run MUST be strictly deterministic given:
- The **Scenario Choice** (A, B, or C)
- The **Simulation Seed** (e.g., Seed-101)
- The **Model Versions** (LLM and Code)

---

## Section 2 — Entity Catalog

Every entity in MIRAGE follows a strict schema to ensure Redis/PostgreSQL interoperability.

### 2.1 Core Entities

| Entity | Field | Type | Constraint | Example |
|:---|:---|:---|:---|:---|
| **Cyclone** | `id` | UUID | PK | `cyc-7890` |
| | `category` | INT | [1, 5] | `4` |
| | `pos` | POINT | SRID 4326 | `(18.9, 84.4)` |
| | `wind_speed` | FLOAT | ≥ 0 | `210.5` |
| | `track` | LINESTRING | SRID 4326 | `LINESTRING(...)` |
| **Shelter** | `id` | UUID | PK | `sh-101` |
| | `capacity` | INT | > 0 | `500` |
| | `occupancy` | INT | [0, cap*1.2] | `420` |
| | `food_stock` | FLOAT | kg, ≥ 0 | `1200.0` |
| | `water_stock` | FLOAT | L, ≥ 0 | `3000.0` |
| **Resource** | `id` | UUID | PK | `res-food-01` |
| | `type` | ENUM | {FOOD, WATER, FUEL, MED, BLK} | `FOOD` |
| | `quantity` | FLOAT | ≥ 0 | `5000.0` |
| | `depot_id` | UUID | FK -> Depot | `depot-north` |
| **Task** | `id` | UUID | PK | `task-123` |
| | `type` | ENUM | {DELIVER, EVACUATE, REPAIR} | `DELIVER` |
| | `status` | ENUM | {PENDING, APPROVED, EXECUTING, ...} | `PENDING` |
| | `priority` | FLOAT | [0, 1] | `0.85` |
| **Decision** | `id` | UUID | PK | `dec-456` |
| | `rec` | TEXT | Non-empty | "Allocate 500L water to Sh-101" |
| | `reason` | TEXT | Explainable | "Predicted shortage in 6hrs..." |
| | `evidence` | JSONB | Data-backed | `{"shortage_tick": 24}` |

---

## Section 3 — Cyclone Dataset

Scenarios are parameterized to test specific agent stresses.

| Parameter | Scenario A (The Sprint) | Scenario B (The Siege) | Scenario C (The Pivot) |
|:---|:---|:---|:---|
| **Behavior** | Rapid Intensification | Prolonged Stagnation | Tracking Shift |
| **Start Cat** | 2 | 4 | 3 |
| **Peak Cat** | 5 (at Landfall) | 4 (sustained) | 4 |
| **Wind (Avg)** | 220 km/h | 180 km/h | 190 km/h |
| **Rainfall** | 100 mm/tick | 250 mm/tick | 150 mm/tick |
| **Surge** | 4.5 m | 3.0 m | 3.5 m |
| **Duration** | 24 Ticks | 72 Ticks | 48 Ticks |
| **Key Stress** | Decision Latency ($M1$) | Resource Scarcity ($M3$) | Dynamic Replanning ($M5$) |

---

## Section 4 — Population Model

### 4.1 Distribution
- **District Size**: 50km x 50km
- **Total Pop**: 1,000,000 across 5 zones
- **Density**: Rural (100/km²), Suburban (1,000/km²), Urban (5,000/km²)

### 4.2 Evacuation Behavior ($P_{evac}$)
Calculated per tick for individuals in Risk Zones:
$$P_{evac} = (w_r \cdot RS) + (w_c \cdot Dist_{coast}) + \epsilon$$
Where:
- $RS$: Risk Score [0,1]
- $w_r$: Risk Sensitivity (0.7)
- $\epsilon$: Stochastic jitter (±0.05)

### 4.3 Shelter Selection Logic
Evacuees choose shelters based on a weighted utility:
$$U_s = \frac{1}{Distance} \cdot (1 - \frac{Occupancy}{Capacity}) \cdot Status_{road}$$
- If $Occupancy > Capacity$, utility drops by 80%.

---

## Section 5 — Shelter Dataset (N=20)

Shelters are generated across the district with varied capacities to create hotspots.

### 5.1 Generation Rules
- **Coastal Zones (1-5)**: Capacity 200 - 500 (High Risk)
- **Central Zones (6-15)**: Capacity 500 - 1000 (Primary Hubs)
- **Inland Zones (16-20)**: Capacity 1000 - 2000 (Safe Havens)

### 5.2 Initial State Table (Subset)

| ID | Zone | Capacity | Food (kg) | Water (L) | Med | Notes |
|:---|:---|:---|:---|:---|:---|:---|
| SH-01 | Coastal | 400 | 800 | 1200 | 10 | Immediate inundation risk |
| SH-05 | Central | 800 | 2400 | 4800 | 30 | Primary logistics node |
| SH-20 | Inland | 2000 | 10000 | 20000 | 100 | Final destination hub |

---

## Section 6 — Resource Dataset

### 6.1 Consumption Rates (Per Person / Per Tick)
- **Food**: 0.2 kg
- **Water**: 1.0 L
- **Medical**: 0.05 units
- **Fuel**: 2.0 L (per active vehicle)

### 6.2 Restocking Rules
- **Shortage Threshold**: Stock < (Consumption_Rate * 5 ticks)
- **Restocking Lead Time**: 2 Ticks (Simulated transit time)
- **Source**: Depot-1 (Main Stockpile) -> Targeted Shelter

### 6.3 Initial Depot Quantities
| Depot | Food (kg) | Water (L) | Fuel (L) | Med Kits |
|:---|:---|:---|:---|:---|
| **MAIN_DEPOT** | 100,000 | 250,000 | 10,000 | 5,000 |
| **SATELLITE_A** | 20,000 | 50,000 | 2,000 | 1,000 |
