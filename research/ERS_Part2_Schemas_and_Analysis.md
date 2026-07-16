# MIRAGE — Experiment Recorder & Simulation Runtime Specification (ERS) Part 2
**Version:** 1.0  
**Date:** 2026-06-02  

---

## Section 6 — CSV Schema (Research Data)

All simulation data is exported to a flat-file structure for analysis in R/Python.

### 6.1 `simulation_runs.csv`
| Column | Type | PK/FK | Description |
|:---|:---|:---|:---|
| `run_id` | UUID | PK | Unique identifier for the trial. |
| `scenario_id` | STRING | - | A, B, or C. |
| `seed` | INT | - | Random seed used. |
| `duration` | INT | - | Total ticks executed. |
| `status` | STRING | - | SUCCESS / FAILED / ABORTED. |

### 6.2 `tick_snapshots.csv`
| Column | Type | PK/FK | Description |
|:---|:---|:---|:---|
| `snapshot_id` | UUID | PK | - |
| `run_id` | UUID | FK | - |
| `tick_index` | INT | - | Current simulation hour. |
| `cyclone_cat` | INT | - | Storm category at this tick. |
| `total_occupancy` | INT | - | Current total evacuees in shelters. |
| `stock_level_avg` | FLOAT | - | Mean resource saturation. |

### 6.3 `metrics.csv`
| Column | Type | PK/FK | Description |
|:---|:---|:---|:---|
| `metric_id` | UUID | PK | - |
| `tick_index` | INT | FK | - |
| `m_code` | STRING | - | M1, M2... M8. |
| `v_raw` | FLOAT | - | The raw value. |
| `v_norm` | FLOAT | - | Value normalized to [0,1]. |

---

## Section 7 — Experiment Metadata

For a paper to stay reproducible, the **Metadata Header** MUST be attached to every log folder:
```json
{
  "exp_metadata": {
    "sys_version": "v1.0.4-beta",
    "git_sha": "7f8a92b",
    "timestamp": "2026-06-02T00:30:00Z",
    "llm_config": {
      "model": "gemini-1.5-flash",
      "temp": 0.0,
      "top_p": 1.0
    },
    "sim_config": {
      "time_scale": 1.0,
      "tick_ms": 5000,
      "governance_mode": "STRICT_HITL"
    }
  }
}
```

---

## Section 8 — Failure Recovery

### 8.1 Recorder Crash
- **Behavior**: If the Recorder fails at Step 10, the Simulation pauses.
- **Recovery**: Simulation reads the last successful `tick_index` from `tick_snapshots.csv` and wipes any subsequent partial writes. Resume from `tick_index + 1`.

### 8.2 Redis/Agent Crash
- **Behavior**: System enters `PAUSED_FAULT` state.
- **Recovery**: 
  1. Restart Docker container.
  2. Redis Stream `XREADGROUP` automatically handles the last ACKed message.
  3. Processing resumes with zero state loss.

---

## Section 9 — Statistical Analysis Package

### 9.1 Required Visualization Suite
1. **Convergence Plot**: $M1$ vs $Tick$ (Prove decision speed remains stable under load).
2. **Resource Depletion Curve**: Shelter stock levels per zone over time.
3. **Approval Heatmap**: Delay times ($T_{wait}$) across L1, L2, and L3 stakeholders.

### 9.2 Hypothesis Testing ($H_1$ to $H_5$)
- **Method**: One-way ANOVA for baseline comparison (MIRAGE vs. B1-B5).
- **Metric Grouping**: Mean Resource Efficiency ($M2$) across Scenarios A, B, and C.
- **Confidence**: 95% ($p < 0.05$).

---

## Section 10 — Implementation Readiness Review

### 10.1 Critical Ambiguity List
1. **Clock Sync**: If an agent takes >5s to reason (exceeding tick duration), should the sim clock wait?
   - **Resolution**: Yes. The sim is **Asynchronous-Blocking**. The clock advances ONLY after Step 10 is ACKed.
2. **LLM Downtime**: If the API is unreachable during a run, does it invalidate the trial?
   - **Resolution**: Yes. Fail-stop. Trial is marked `ABORTED` in `simulation_runs.csv` and must be restarted.
3. **Disk Pressure**: A 72-tick simulation with 20 shelters may generate >50MB of CSV.
   - **Resolution**: Use Buffered Write; limit snapshots to state deltas if volume becomes an issue.

### 10.2 Final Checklist
- [x] Tick Step Order 1–10 frozen.
- [x] Event stream retry logic (3 retries) locked.
- [x] Column-level CSV schemas finalized.
- [x] Failure recovery procedures documented.

**ERS is implementation-ready.** 
No further specifications are required. Implementation of the **Experiment Recorder** can begin immediately following the **Digital Twin Engine**.
