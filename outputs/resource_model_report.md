# Resource Model Report
Date: 2026-06-02

## 1. Depletion Analysis
- **Observed Bug**: Stock was hitting zero at Tick 1-2 due to unrealistic 1.0L/hr consumption and low initial stock (10k).
- **Corrected Parameters**:
  - Water: 0.25 L/person/hr (aligned with 6L/day emergency standard).
  - Food: 0.05 kg/person/hr (aligned with 1.2kg/day emergency standard).
- **Corrected Stock**: 100k L for 10k capacity (approx 33-hour buffer at max load).

## 2. Mathematical Correctness
Verified via mass balance: `Stock_Initial - (Occupancy * Rate * T) = 0`
For sh-01: `100,000 - (12,000 * 0.25 * T) = 0` => `T = 33.3`
This ensures resource pressure triggers mid-run (T=12 is landfall), forcing the Conflict Engine to activate between T=30 and T=72.

## 3. Realism Verdict
The model is now **Realistic and Balanced**. 
It provides enough buffer for the initial evacuation phase but creates critical shortages during the peak storm period (T=33 to T=72), providing a robust evaluation environment for agent coordination.
