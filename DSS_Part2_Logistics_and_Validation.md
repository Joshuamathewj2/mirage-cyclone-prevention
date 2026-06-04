# MIRAGE — Dataset & Scenario Specification (DSS) Part 2
**Version:** 1.0  
**Date:** 2026-06-02  

---

## Section 7 — Transportation Dataset

### 7.1 Road Network
- **Topology**: Grid + Hub-and-Spoke.
- **Node Count**: 50 (Shelters, Depots, Intersections).
- **Edge Types**:
  - **Highway (Type 1)**: Speed 80 km/h, Capacity 100%.
  - **Secondary Road (Type 2)**: Speed 40 km/h, Capacity 60%.
  - **Coastal Path (Type 3)**: Speed 20 km/h, Capacity 30%.

### 7.2 Vehicle Fleet
| Vehicle Type | Capacity (kg) | Speed (km/h) | Fuel Consumption | Count |
|:---|:---|:---|:---|:---|
| Heavy Truck | 10,000 | 60 | 4.0 L/km | 5 |
| Light Van | 2,000 | 80 | 1.5 L/km | 15 |
| Marine Skiff | 500 | 30 | 0.8 L/km | 3 |

### 7.3 Travel Time Calculation
$$T_{travel} = \frac{Distance}{Speed \cdot \alpha_{weather}}$$
- $\alpha_{weather} = 1.0$ (Normal)
- $\alpha_{weather} = 0.5$ (Heavy Rain)
- $\alpha_{weather} = 0.2$ (Storm Surge/Inundation)

---

## Section 8 — Infrastructure Failure Model

Failures are probabilistic but influenced by the Cyclone DT.

### 8.1 Failure Probabilities ($P_{fail}$)
| Failure Type | Equation | Trigger Conditions |
|:---|:---|:---|
| **Road Block** | $P = 0.1$ | Wind > 150 km/h OR Rain > 200 mm |
| **Power Out** | $P = 0.4$ | Wind > 120 km/h |
| **Comms Down** | $P = 0.2$ | Lightning OR Wind > 180 km/h |
| **Shelter Damage**| $P = 0.05 \cdot (Cat-3)$ | Cat ≥ 4 |

---

## Section 9 — Scenario Seeds

To ensure the "Digital Twin" is reproducible, the following must be deterministic based on the seed.

### 9.1 Evaluation Seeds
| Seed ID | Purpose | Deterministic Variables |
|:---|:---|:---|
| **Seed-101** | Baseline Stability | Cyclone Track, Initial Stock, Failure Ticks |
| **Seed-202** | Stress Testing | Population Evac Rates, Congestion Points |
| **Seed-303** | Final Validation | Random Failure Injection Ticks (T=12, T=25, T=40) |

---

## Section 10 — Ground Truth Dataset (Expert Annotation)

This dataset is used to measure **Conflict Resolution Accuracy (M4)**.

### 10.1 Case Structure
Each case consists of a simultaneous request set and the "Expert Optimal" allocation.

### 10.2 Selection (Sample Cases 1-5 of 30)

| Case ID | Requests (Shelter: Item: Qty) | Ground Truth Allocation | Justification |
|:---|:---|:---|:---|
| **GT-01** | S1: Water: 500L <br> S2: Water: 500L | S1: 500L, S2: 0L | S1 is in the "High Surge" zone with 0 stock. S2 has 2-tick buffer. |
| **GT-05** | S10: Food: 200kg <br> S15: Med: 10 units | Both: 100% | No resource conflict; transport-only constraint. Prioritize Med. |
| **GT-12** | 5 Shelters: Fuel: 100L each | Pro-rata (20% each) | General shortage; no single shelter is critical. Maintain parity. |
| **GT-25** | S4: Food: 1000kg <br> S9: Food: 500kg | S9: 1000kg, S4: 500kg | S9 is a regional hub with 2000 orphans; S4 has mobile population. |
| **GT-30** | S1: Med: 5 units <br> S2: Med: 5 units | S2: 100% | S2 road is predicted to flood in 1 tick. Last chance delivery. |

---

## Section 11 — Data Validation Rules (Invariants)

The Experiment Recorder must flag any state that violates these rules:

1. **Mass Balance**: `Stock_Initial - Consumed + Restocked = Stock_Current`
2. **Capacity Ceiling**: `Occupancy <= Capacity * 1.2` (Max 20% overflow)
3. **Task Integrity**: `Task.Status == APPROVED` implies `Task.Approver_ID != NULL`
4. **Time Monotonicity**: `Current_Tick > Previous_Tick`
5. **No Negative Survival**: `Stock >= 0` (If stock = 0, 'Shortage' event must fire)

---

## Section 12 — Implementation Readiness Review

| Category | Risk/Observation | Implementation Action |
|:---|:---|:---|
| **Weak Assumption** | Evacuation behavior ($P_{evac}$) is linear. | Implement non-linear step-function for Category 4+ landfall. |
| **Missing Data** | Vehicle initial positions. | Default all vehicles to MAIN_DEPOT at T=0. |
| **Realism Risk** | Road network is a static graph. | Implement dynamic weights based on `Road_Block` probability. |
| **Critical Blocker** | Ground Truth (M4) only has 5 cases above. | **MUST complete all 30 cases before Phase 7 (Evaluation).** |

### Final Verdict:
**DSS is implementation-ready.** The schemas are defined, scenarios parameterized, and invariants locked.
The next engineering step is **Phase 2: Digital Twin Engine Implementation** using these parameters.
