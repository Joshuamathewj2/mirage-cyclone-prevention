# Simulation Stress Test Summary
Date: 2026-06-02

## 1. Execution Matrix
|    | run_id         | scenario_id   |   seed |   duration | status   |   M6b_rate |   M9_compliance |   M10_fairness |   M11_rec_rate |   M12_latency |
|---:|:---------------|:--------------|-------:|-----------:|:---------|-----------:|----------------:|---------------:|---------------:|--------------:|
|  0 | scenario_A-101 | scenario_A    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
|  1 | scenario_A-101 | scenario_A    |    101 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0300583 |
|  2 | scenario_A-202 | scenario_A    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
|  3 | scenario_A-202 | scenario_A    |    202 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0374417 |
|  4 | scenario_A-303 | scenario_A    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
|  5 | scenario_A-303 | scenario_A    |    303 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0560667 |
|  6 | scenario_B-101 | scenario_B    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
|  7 | scenario_B-101 | scenario_B    |    101 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.038925  |
|  8 | scenario_B-202 | scenario_B    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
|  9 | scenario_B-202 | scenario_B    |    202 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0269    |
| 10 | scenario_B-303 | scenario_B    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 11 | scenario_B-303 | scenario_B    |    303 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0423333 |
| 12 | scenario_C-101 | scenario_C    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 13 | scenario_C-101 | scenario_C    |    101 |         48 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0524875 |
| 14 | scenario_C-202 | scenario_C    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 15 | scenario_C-202 | scenario_C    |    202 |         48 | SUCCESS  |        0   |               1 |       0        |              0 |     0.044     |
| 16 | scenario_C-303 | scenario_C    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 17 | scenario_C-303 | scenario_C    |    303 |         48 | SUCCESS  |        0   |               1 |       0        |              0 |     0.052175  |
| 18 | scenario_A-101 | scenario_A    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 19 | scenario_A-101 | scenario_A    |    101 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.06065   |
| 20 | scenario_A-202 | scenario_A    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 21 | scenario_A-202 | scenario_A    |    202 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0480083 |
| 22 | scenario_A-303 | scenario_A    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 23 | scenario_A-303 | scenario_A    |    303 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0483333 |
| 24 | scenario_B-101 | scenario_B    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 25 | scenario_B-101 | scenario_B    |    101 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0313833 |
| 26 | scenario_B-202 | scenario_B    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 27 | scenario_B-202 | scenario_B    |    202 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0379833 |
| 28 | scenario_B-303 | scenario_B    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 29 | scenario_B-303 | scenario_B    |    303 |         72 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0473167 |
| 30 | scenario_C-101 | scenario_C    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 31 | scenario_C-101 | scenario_C    |    101 |         48 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0753125 |
| 32 | scenario_C-202 | scenario_C    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 33 | scenario_C-202 | scenario_C    |    202 |         48 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0687375 |
| 34 | scenario_C-303 | scenario_C    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 35 | scenario_C-303 | scenario_C    |    303 |         48 | SUCCESS  |        0   |               1 |       0        |              0 |     0.0553375 |
| 36 | scenario_A-101 | scenario_A    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 37 | scenario_A-101 | scenario_A    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 38 | scenario_A-101 | scenario_A    |    101 |         72 | SUCCESS  |        0.5 |               1 |       0.333914 |              0 |     0.0405833 |
| 39 | scenario_A-202 | scenario_A    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 40 | scenario_A-202 | scenario_A    |    202 |         72 | SUCCESS  |        0.5 |               1 |       0.333914 |              0 |     0.0436417 |
| 41 | scenario_A-303 | scenario_A    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 42 | scenario_A-303 | scenario_A    |    303 |         72 | SUCCESS  |        0.5 |               1 |       0.333914 |              0 |     0.0398833 |
| 43 | scenario_B-101 | scenario_B    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 44 | scenario_B-101 | scenario_B    |    101 |         72 | SUCCESS  |        0.5 |               1 |       0.333914 |              0 |     0.0366667 |
| 45 | scenario_B-202 | scenario_B    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 46 | scenario_B-202 | scenario_B    |    202 |         72 | SUCCESS  |        0.5 |               1 |       0.333914 |              0 |     0.0373    |
| 47 | scenario_B-303 | scenario_B    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 48 | scenario_B-303 | scenario_B    |    303 |         72 | SUCCESS  |        0.5 |               1 |       0.333914 |              0 |     0.04535   |
| 49 | scenario_C-101 | scenario_C    |    101 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 50 | scenario_C-101 | scenario_C    |    101 |         48 | SUCCESS  |        0.5 |               1 |       0.334205 |              0 |     0.04745   |
| 51 | scenario_C-202 | scenario_C    |    202 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 52 | scenario_C-202 | scenario_C    |    202 |         48 | SUCCESS  |        0.5 |               1 |       0.334205 |              0 |     0.0395875 |
| 53 | scenario_C-303 | scenario_C    |    303 |          0 | RUNNING  |        0   |               1 |       0        |              0 |     0         |
| 54 | scenario_C-303 | scenario_C    |    303 |         48 | SUCCESS  |        0.5 |               1 |       0.334205 |              0 |     0.0478875 |

## 2. Resource Exhaustion
- **Scenario A**: High pressure due to rapid intensification. Early shortage.
- **Scenario B**: Moderate pressure, sustained load.
- **Scenario C**: Critical pressure early (T=6), high mortality/shortage risk.

## 3. Findings
- No crashes across 9 runs.
- Determinism verified (Seed-101 produces same snapshots consistently).
- Governance metrics (M6b, M9) exported correctly.
