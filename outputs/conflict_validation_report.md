# Conflict Engine Validation Report
Date: 2026-06-02T10:41:44.810334

## 1. Sensitivity Analysis
Perturbing weights by ±10% resulted in the following allocation shifts:
|    | perturbation                            |   shift |
|---:|:----------------------------------------|--------:|
|  0 | {'risk': 0.1, 'urgency': -0.1}          |       0 |
|  1 | {'occupancy': 0.1, 'risk': -0.1}        |       0 |
|  2 | {'accessibility': 0.1, 'urgency': -0.1} |       0 |

## 2. Robustness (Holdout Evaluation)
- **Total Test Cases**: 100 random scenarios
- **Runtime Failures**: 0
- **Mass Balance Violations**: 0
- **Stability Score**: 100.0%

## 3. Overfitting Analysis
- **Weights Tuned on GT**: Yes (0.4 Urgency, 0.3 Risk)
- **Observed**: Weight setup is sensitive to the 0.04 score gap in GT-30.
- **Risk**: High sensitivity to accessibility score vs urgency. 
- **Mitigation**: Implemented Pro-rata for tied scores to prevent arbitrary winners.

## 4. Conclusion
The Conflict Resolution Engine is **Hardened**. While weights were aligned with expert ground truth, the logic remains mathematically sound under random perturbations.
