## Section 6 — Digital Twin Design

A Digital Twin (DT) in MIRAGE is a continuously-updated computational replica of a real-world entity. Agents do not act on the real world — they act on the Digital Twin, whose state is updated by the simulation engine each tick.

---

### 6.1 Cyclone Digital Twin

**State Variables:**

| Variable | Type | Description |
|---|---|---|
| category | Integer [1–5] | Saffir-Simpson category |
| position | GeoPoint | Eye location (lat, lon) |
| wind_speed_kmh | Float | Sustained wind at eye wall |
| storm_surge_m | Float | Predicted coastal surge height |
| rainfall_mm_hr | Float | Rainfall rate at current position |
| predicted_path | LineString | Forecast track for next 24 sim-hours |
| landfall_tick | Integer | Expected landfall simulation tick |
| weakening_rate | Float | Category decay per tick post-landfall |

**Events:**
- `CYCLONE_POSITION_UPDATED` (every tick)
- `CYCLONE_CATEGORY_CHANGED` (if |Δcategory| ≥ 1)
- `CYCLONE_LANDFALL` (when position crosses coastline geometry)
- `CYCLONE_DISSIPATED` (when category < 1)

**Update Rules:**
```
position(t+1) = interpolate(control_points, t+1)
category(t+1) = category(t) + intensity_delta(t)
    where intensity_delta = +1 if t < landfall_tick, else −weakening_rate
wind_speed(t+1) = f(category(t+1))   [Saffir-Simpson table]
storm_surge(t+1) = g(wind_speed, bathymetry_constant)
```

**Agent Interactions:**
- Risk Assessment Agent reads all cyclone DT variables each tick.
- Logistics Agent reads predicted_path to assess route exposure.
- Shelter Agent reads storm_surge_m and position to predict coastal shelter impact.

---

### 6.2 Population Digital Twin

**State Variables:**

| Variable | Type | Description |
|---|---|---|
| zone_id | String | Geographic zone identifier |
| total_population | Integer | Zone resident count |
| evacuated_count | Integer | Cumulative evacuees departed |
| sheltered_count | Integer | Persons in shelters from this zone |
| remaining_at_risk | Integer | total - evacuated - sheltered |
| evacuation_rate | Float | Fraction evacuating per tick |
| injury_rate | Float | Injuries per tick (cyclone intensity function) |

**Events:**
- `EVACUATION_SURGE` (when remaining_at_risk drops > 20% in one tick)
- `INJURY_THRESHOLD_BREACHED` (when cumulative injuries > zone threshold)

**Update Rules:**
```
evacuated(t+1) = evacuated(t) + round(remaining_at_risk(t) × evacuation_rate(t))
evacuation_rate(t) = base_rate × RS(zone, t)   [scales with risk score]
injury_rate(t) = 0.002 × wind_speed(t) / 100   [empirical approximation]
```

**Agent Interactions:**
- Shelter Agent reads zone sheltered_count to compute shelter demand.
- Resource Agent uses zone remaining_at_risk to project medical kit demand.
- Conflict Agent uses zone remaining_at_risk as L_i component for priority scoring.

---

### 6.3 Shelter Digital Twin

**State Variables:**

| Variable | Type | Description |
|---|---|---|
| shelter_id | UUID | Identifier |
| capacity | Integer | Maximum occupancy |
| current_occupancy | Integer | Current count |
| food_stock_kg | Float | Food inventory |
| water_stock_L | Float | Water inventory |
| medical_kits | Integer | Kit count |
| blankets | Integer | Blanket count |
| status | Enum | OPERATIONAL / FULL / DAMAGED / CLOSED |
| overflow_risk | Float [0,1] | Predicted overflow probability next 2 ticks |

**Events:**
- `SHELTER_FULL` (occupancy ≥ capacity)
- `SHELTER_OVERFLOW_PREDICTED` (overflow_risk > 0.7)
- `SHELTER_FOOD_CRITICAL` (food_stock_kg / occupancy < 1 day)
- `SHELTER_WATER_CRITICAL` (water_stock_L / occupancy < 3 L)
- `SHELTER_DAMAGED` (infrastructure failure sim)

**Update Rules:**
```
incoming(t) = f(zone_evacuation_rate, zone_population, distance_to_shelter, road_status)
occupancy(t+1) = min(capacity × 1.20, occupancy(t) + incoming(t))
food_stock(t+1) = food_stock(t) − occupancy(t) × 0.5
water_stock(t+1) = water_stock(t) − occupancy(t) × 3.0
overflow_risk(t) = sigmoid(occupancy(t) / capacity − 0.85, steepness=10)
```

**Agent Interactions:**
- Shelter Agent reads and writes shelter DT each tick.
- Resource Agent reads food/water stocks to trigger shortage forecasts.
- Logistics Agent writes to stock variables when delivery tasks complete.

---

### 6.4 Resource Digital Twin

**State Variables:**

| Variable | Type | Description |
|---|---|---|
| resource_id | UUID | Identifier |
| type | Enum | FOOD / WATER / MEDICAL_KIT / FUEL / BLANKET |
| quantity | Float | Current stock |
| location | GeoPoint | Storage location |
| consumption_rate | Float | Units consumed per tick |
| days_remaining | Float | quantity / (consumption_rate × ticks_per_day) |
| shortage_predicted | Boolean | days_remaining < threshold |
| reorder_threshold | Float | Trigger reorder below this quantity |

**Events:**
- `RESOURCE_SHORTAGE_DETECTED` (days_remaining < 2)
- `RESOURCE_DEPLETED` (quantity = 0)
- `RESOURCE_DELIVERED` (Logistics Agent completes delivery)

**Update Rules:**
```
quantity(t+1) = quantity(t) − consumption_simulated(t) + deliveries_completed(t)
consumption_simulated(t) = Σ_shelters [occupancy_s × per_capita_rate_k]
days_remaining(t) = quantity(t) / (avg_daily_consumption × 1.0)
```

**Agent Interactions:**
- Resource Agent is the sole write agent for resource DT.
- Conflict Agent reads quantity to compute available stock for allocation.
- Logistics Agent reads quantity at origin and destination to plan delivery.

---

### 6.5 Transportation Network Digital Twin

**State Variables:**

| Variable | Type | Description |
|---|---|---|
| route_id | UUID | Identifier |
| origin | GeoPoint | Start node |
| destination | GeoPoint | End node |
| path | LineString | Full route geometry |
| distance_km | Float | Route length |
| status | Enum | CLEAR / BLOCKED / DEGRADED |
| blockage_reason | String | Flooding / Debris / Bridge failure |
| estimated_clear_tick | Integer | When route expected to reopen |
| vehicles_en_route | Integer | Count of active deliveries on route |
| travel_time_ticks | Float | Current estimated transit time |

**Events:**
- `ROUTE_BLOCKED` (status → BLOCKED)
- `ROUTE_DEGRADED` (status → DEGRADED, travel_time_ticks increased)
- `ROUTE_CLEARED` (status → CLEAR)

**Update Rules:**
```
status(t+1) = infrastructure_failure_sim.get_status(route_id, t+1)
travel_time_ticks(t+1):
    if status = CLEAR:    base_travel_time
    if status = DEGRADED: base_travel_time × 2.5
    if status = BLOCKED:  inf (route unusable)
```

**Agent Interactions:**
- Logistics Agent is the primary reader; plans delivery routes using route status.
- Logistics Agent writes vehicles_en_route on task assignment.
- Simulation Engine writes status and blockage_reason on infrastructure failures.

---

### 6.6 How Agents Operate on the Digital Twin

```
┌──────────────────────────────────────────────────────────────────┐
│  AGENT-DT INTERACTION MODEL                                      │
│                                                                  │
│  Simulation Engine (each tick):                                  │
│    → Updates all 5 DTs with new simulated state                  │
│    → Publishes update events on Redis Streams                    │
│                                                                  │
│  Agents (triggered by events, not polling):                      │
│    → Read relevant DT state from Blackboard                      │
│    → Apply domain reasoning (deterministic + LLM)                │
│    → Write outputs back to DT (recommendations, task updates)    │
│    → Publish domain events                                       │
│                                                                  │
│  Key invariant:                                                  │
│    Agents NEVER modify DT state directly.                        │
│    Only the Simulation Engine modifies DT state.                 │
│    Agents write to TASKS, DECISIONS, APPROVALS regions only.     │
│    This separation prevents agents from corrupting simulation.   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Section 7 — Evaluation Methodology

### 7.1 M1 — Decision Latency

| Attribute | Detail |
|---|---|
| **Definition** | Time elapsed from triggering event publication to actionable plan availability |
| **Formula** | DL_i = t_plan_ready_i − t_event_fired_i (seconds) |
| **Aggregate** | Mean DL = (1/N) Σ DL_i across all N decision cycles |
| **Measurement** | Automated: timestamp logged at event publish and at DECISIONS record creation |
| **Baseline comparison** | B1 (manual): Timed by researcher with stopwatch during simulation run |
| **Threat** | Manual timing introduces observer bias. Use video recording for B1 measurement. |

---

### 7.2 M2 — Approval Cycle Time

| Attribute | Detail |
|---|---|
| **Definition** | Time from ApprovalRequested to final approval state (APPROVED/REJECTED/EXPIRED) |
| **Formula** | ACT_i = t_final_state_i − t_created_i (minutes, simulation-time) |
| **Aggregate** | Mean ACT across all approval cycles; separately for L1/L2/L3 |
| **Measurement** | Automated: timestamps in approval_audit_log table |
| **Threat** | Simulation-time vs. wall-clock conflation if speed multiplier is improperly handled |

---

### 7.3 M3 — Resource Allocation Efficiency

| Attribute | Detail |
|---|---|
| **Definition** | Priority-weighted ratio of allocated to requested resources across conflict events |
| **Formula** | η = Σ_i (p_i · a_{ik}) / Σ_i (p_i · q_{ik}) ∈ [0,1] |
| **Aggregate** | Mean η across all conflict resolution cycles per scenario |
| **Measurement** | Computed post-run from resource_transactions table joined with conflict_request_links |
| **Threat** | If p_i scores are miscalibrated, η is a biased metric. Sensitivity analysis on weight vectors required. |

---

### 7.4 M4 — Conflict Resolution Accuracy

| Attribute | Detail |
|---|---|
| **Definition** | Agreement between MIRAGE allocation outcomes and expert-annotated ground truth |
| **Formula** | κ = Cohen's Kappa(MIRAGE_outcomes, expert_annotations) |
| **Aggregate** | Single κ value per scenario; overall κ across all scenarios |
| **Measurement** | Expert annotation sheet created prior to experiments. Binary per request: correct/incorrect. |
| **Threat** | Expert annotation is subjective. Use ≥2 annotators and report inter-annotator agreement (IAA). If IAA κ < 0.6, the ground truth is unreliable and M4 is invalid. |

---

### 7.5 M5 — Replanning Speed

| Attribute | Detail |
|---|---|
| **Definition** | Elapsed time from ReplanTriggered event to new DECISIONS record on Blackboard |
| **Formula** | RS_i = t_new_decision_i − t_replan_trigger_i (seconds) |
| **Aggregate** | Mean RS across all replan events; separately by trigger type |
| **Measurement** | Automated timestamp logging |
| **Threat** | LLM API latency has high variance. Report mean, median, and 95th percentile. |

---

### 7.6 M6 — Explainability Score

| Attribute | Detail |
|---|---|
| **Definition** | Human-rated comprehension of agent recommendation based on explanation quality |
| **Formula** | ES = mean Likert score across 5 items, 2 conditions (explanation / no-explanation) |
| **Aggregate** | Group means + Mann-Whitney U test p-value |
| **Measurement** | Structured questionnaire administered to participants after reviewing dashboard |
| **Questionnaire items** | (1) I understand why this decision was made. (2) The reasoning provided was clear. (3) I could explain this decision to a colleague. (4) The evidence presented was relevant. (5) I trust this recommendation. |
| **Threat** | Demand characteristics (participants guess hypothesis). Use cover story: "usability study of the dashboard layout." |

---

### 7.7 M7 — System Resilience

| Attribute | Detail |
|---|---|
| **Definition** | Fraction of critical events that received an operational response within deadline |
| **Formula** | SR = N_responded_within_deadline / N_critical_events_total |
| **Aggregate** | Per scenario; separately for agent-crash and normal operation conditions |
| **Measurement** | Automated: events with deadline logged; responses matched by event_id |
| **Threat** | Definition of "critical event" must be pre-specified. Changing post-hoc inflates SR. |

---

### 7.8 M8 — Audit Completeness

| Attribute | Detail |
|---|---|
| **Definition** | Fraction of decision lifecycle transitions captured in approval_audit_log |
| **Formula** | AC = actual_log_entries / expected_log_entries |
| **Expected entries** | For each approval: CREATED + PENDING + (ESCALATED)^e + (APPROVED/REJECTED/EXPIRED) = minimum 3 entries |
| **Aggregate** | AC across all approvals per scenario |
| **Measurement** | Post-run query: COUNT(log entries) vs. computed expected count from approvals table |
| **Threat** | If audit_write node fails silently, AC appears high but entries are missing. Add audit integrity check to simulation teardown. |

---

## Section 8 — Baselines

### B1 — Manual Coordination

| Attribute | Detail |
|---|---|
| **Description** | Human coordinator manages all decisions using scenario briefing document and spreadsheet |
| **Advantage** | Represents actual current practice; ecologically valid |
| **Weakness** | Single human introduces large individual variance; not scalable; no audit trail |
| **Why MIRAGE outperforms** | Agent reasoning completes in seconds; human deliberation takes minutes; MIRAGE maintains full audit; human coordination produces no structured conflict resolution |
| **Implementation** | Researcher acts as coordinator; decisions timed and recorded manually |

---

### B2 — First-Come-First-Served (FCFS)

| Attribute | Detail |
|---|---|
| **Description** | Requests processed in chronological arrival order; no priority scoring |
| **Advantage** | Simple; transparent; no model required |
| **Weakness** | Ignores urgency and life safety; low-priority requests can starve high-priority ones during surges |
| **Why MIRAGE outperforms** | MIRAGE's priority model allocates to highest-need requesters first; η_MIRAGE > η_FCFS in all scarcity scenarios by construction |
| **Implementation** | Replace Conflict Agent scoring with arrival-order queue; all other agents identical |

---

### B3 — Equal Allocation

| Attribute | Detail |
|---|---|
| **Description** | Available resources divided equally among all competing requesters |
| **Advantage** | Perceived fairness; easy to implement and explain |
| **Weakness** | Equal distribution may leave all requesters partially resourced; violates urgency differentiation |
| **Why MIRAGE outperforms** | Equal allocation produces η = 0.5 in a 2-party conflict with one critical/one non-critical request; MIRAGE achieves η → 1.0 |
| **Implementation** | Conflict Agent replaced with equal-split formula; no scoring |

---

### B4 — Rule-Based Coordination

| Attribute | Detail |
|---|---|
| **Description** | Pre-defined IF-THEN rules for allocation (e.g., "medical kits always go to highest-occupancy shelter first") |
| **Advantage** | Deterministic; no LLM required; explainable |
| **Weakness** | Rules cannot handle novel or compound scenarios; brittle under multi-factor conflicts |
| **Why MIRAGE outperforms** | Rule-based systems fail when two high-occupancy shelters compete simultaneously; priority scoring handles n-way conflict generically |
| **Implementation** | Conflict Agent replaced with rule engine (5 pre-specified IF-THEN rules); Approval Agent retained |

---

### B5 — Dashboard-Only Coordination

| Attribute | Detail |
|---|---|
| **Description** | MIRAGE UI is available (stakeholders see real-time DT state) but no agent recommendations are generated. Stakeholders make all decisions manually from dashboard information. |
| **Advantage** | Tests whether the dashboard visualization alone provides benefit; isolates agent contribution |
| **Weakness** | No recommendations; no conflict resolution; no approval workflow |
| **Why MIRAGE outperforms** | Agents synthesize multi-source information; human stakeholders cannot integrate 100+ shelter states simultaneously |
| **Implementation** | Disable all agents; simulation and UI remain; stakeholders use dashboard to make manual decisions |

---

## Section 9 — Experimental Design

### Scenario A — Rapid Intensification (Primary Evaluation Scenario)

| Parameter | Value |
|---|---|
| Cyclone category progression | Cat 3 → Cat 5 over 10 ticks, rapid weakening post-landfall |
| Landfall tick | 15 |
| Affected shelters | 8 shelters, 3 in high-risk zones |
| Peak shelter occupancy | 95% capacity at tick 18 |
| Resource stress | Water depletion at 2 shelters by tick 20 |
| Infrastructure failures | Route_001 blocked at tick 12 (flooding); Route_003 blocked at tick 16 |
| Conflict events | 4 multi-party resource conflicts |
| Expected agent behavior | Risk Agent: escalates priority zones at tick 8. Shelter Agent: triggers overflow prediction at tick 14. Resource Agent: triggers shortage at tick 19. Conflict Agent: resolves 4 conflicts using scoring model. Logistics Agent: reroutes via alt routes at ticks 12, 16. |
| Experiments using this scenario | E1 (B1 baseline), E2 (MIRAGE full), E3 (no conflict resolution), E4 (no explainability) |

---

### Scenario B — Slow-Moving Prolonged Impact (Stress Test Scenario)

| Parameter | Value |
|---|---|
| Cyclone category progression | Cat 4 sustained for 25 ticks, slow weakening |
| Landfall tick | 20 |
| Affected shelters | 12 shelters, sustained high demand for 15 ticks |
| Peak shelter occupancy | 110% capacity (overflow conditions) at multiple shelters |
| Resource stress | Food depletion at 5 shelters; fuel shortage affecting logistics |
| Infrastructure failures | Route_002 degraded tick 15; Route_005 blocked tick 22; partial Route_002 clearance tick 30 |
| Conflict events | 9 multi-party resource conflicts (high-frequency stress) |
| Expected agent behavior | Multiple replan cycles expected. Approval queue builds up. Escalations to EOC expected. Tests cooldown model. |
| Experiments using this scenario | E5 (stress test) |

---

### Scenario C — Sudden Direction Change (Failure Recovery Scenario)

| Parameter | Value |
|---|---|
| Cyclone category progression | Cat 3, stalls at tick 10, accelerates and changes track at tick 15 |
| Landfall tick | 22 (different zone than originally predicted) |
| Affected shelters | 6 shelters (original plan), then 4 different shelters (post-track change) |
| Resource stress | Resources pre-positioned for original zones; repositioning required |
| Infrastructure failures | Bridge failure tick 18; Power outage zone B tick 20 |
| Agent crash injection | Risk Assessment Agent crashes at tick 12; recovers at tick 17 |
| Conflict events | 3 conflicts during repositioning |
| Expected agent behavior | At track change: full replan triggered (|Δcategory| not triggered — track change is the trigger). Logistics Agent replans all deliveries. During agent crash: system continues on stale risk data; UI shows warning. |
| Experiments using this scenario | E6 (failure recovery) |

---

### Experiment Summary Table

| Experiment | Scenario | Condition | Agents | Metrics Measured |
|---|---|---|---|---|
| E1 | A | Manual (B1) | None | M1, M2, M3 (reference) |
| E2 | A | MIRAGE Full | All 6 | M1–M8 |
| E3 | A | No Conflict Resolution (B2: FCFS) | 5 (no Conflict Agent scoring) | M3, M4 ablation |
| E4 | A | No Explainability | All 6, reasoning hidden | M6 ablation |
| E5 | B | MIRAGE Full (stress) | All 6 | M1, M3, M5, M7 |
| E6 | C | MIRAGE + agent crash | All 6, Risk Agent crashes | M5, M7, M8 |

---

## Section 10 — Threats to Validity

### 10.1 Internal Validity Threats

| Threat | Description | Mitigation |
|---|---|---|
| Instrumentation bias | Metric measurement code may have bugs that inflate favourable results | Separate evaluation logger from agent code; unit-test all metric computations |
| Maturation | System performance may improve between E1 and E6 due to caching or warm-up effects | Restart system fresh for each experiment run; clear Redis between runs |
| Selection bias in conflict scenarios | Conflict scenarios chosen by developer may inadvertently favour MIRAGE scoring model | Expert annotation sheet must be created before scenario design is finalized |
| LLM output variance | Same reasoning prompt may produce different outputs across runs | Fix random seed; use temperature=0 for all LLM calls; run each experiment 3× and report mean |
| History effects | Blackboard state from one experiment may bleed into next | Enforce full state reset (Redis flush + PostgreSQL snapshot restore) between experiments |

---

### 10.2 External Validity Threats

| Threat | Description | Mitigation |
|---|---|---|
| Simulation realism | DT simulation may not accurately represent real cyclone conditions | Parameterize against documented case studies; explicitly limit generalizability claims |
| Stakeholder proxy | CS students or researchers acting as stakeholders are not real emergency managers | Clearly disclose in paper; frame as "formative evaluation" not "summative field validation" |
| Single disaster type | Results are specific to cyclone scenarios | Claims must be bounded to cyclone response; no generalization to floods, earthquakes |
| Single region | Evaluation uses one simulated coastal district | Multi-region coordination is Future Work; explicitly bounded in scope |

---

### 10.3 Construct Validity Threats

| Threat | Description | Mitigation |
|---|---|---|
| Priority score as welfare proxy | The 5-dimension scoring model may not capture actual emergency management priorities | Validate weight vector against domain expert review before experiments |
| Explainability ≠ comprehension | High Likert scores may reflect UI aesthetics, not actual understanding | Include comprehension verification questions (not just self-rated understanding) |
| Audit completeness ≠ accountability | High M8 scores do not guarantee the audit log is legally sufficient | Explicitly state M8 measures technical completeness, not legal sufficiency |
| Decision latency ≠ decision quality | Fast decisions may be low-quality | M3 (efficiency) and M4 (accuracy) must be jointly reported with M1 |

---

### 10.4 Statistical Validity Threats

| Threat | Description | Mitigation |
|---|---|---|
| Sample size (H5) | N=20 for explainability study is borderline. Effect size may be too small to detect | Conduct a priori power analysis; target 80% power for expected medium effect (d=0.5) |
| Non-normality | Decision latency distributions are likely right-skewed | Use non-parametric tests where appropriate; report median alongside mean |
| Multiple comparisons | Six experiments testing eight metrics = 48 potential comparisons | Apply Bonferroni correction; clearly distinguish confirmatory (H1–H5) from exploratory analysis |
| N=1 for B1 | Manual baseline with single human operator is not statistically valid | Frame E1 as "reference run" not "statistical baseline"; use B2–B5 (algorithmic) for statistical tests |
| Single simulation seed | Fixed-tick failure events are deterministic | Run each scenario with 3 simulation seeds (varied perturbation values); report variance |

---

## Section 11 — Publication Potential

### 11.1 Venue Assessment

| Venue Type | Suitability | Strongest Angle |
|---|---|---|
| Final Year Project (FYP) | Excellent — scope is well-bounded and implementable | Full system with simulation and evaluation |
| Workshop paper (ISCRAM, WASSA, HHAI) | Good — disaster informatics + XAI audiences | Explainability architecture + governance coupling |
| Short conference paper (AAMAS, IJCAI) | Possible — strong MAS community | Conflict resolution model + formal evaluation |
| Full conference paper (AAAI, IJCAI) | Ambitious but possible if evaluation is rigorous | Needs N≥3 human annotators and strong statistical results |
| Journal (IJDRS, IJDRR) | Long-term goal | Requires real-world validation beyond simulation |
| Startup / product | Out of scope — no commercial pathway in v1 | — |

---

### 11.2 Strongest Publication Angle

> **"An Explainable Approval-Aware Multi-Agent Framework for Cyclone Disaster Coordination with Parameterized Digital Twin Evaluation"**

This framing emphasizes:
1. The governance novelty (approval-aware)
2. The XAI contribution (explainable, separated from LLM decision authority)
3. The evaluation methodology novelty (parameterized DT with reproducible scenarios)

Target: **ISCRAM 2027** (Information Systems for Crisis Response and Management) — the premier venue for this exact combination of disaster informatics + AI.

---

### 11.3 Weakest Area

The **human evaluation of explainability (H5)** is the weakest element. With N=20 and CS-student proxies, the result will be questioned by reviewers. Options:

1. Accept the limitation and disclose explicitly (FYP-appropriate)
2. Recruit 3–5 actual emergency management professionals for a qualitative walkthrough (strengthens the paper significantly)
3. Supplement with a log-based analysis of how often approvers changed their decision after viewing explanations (does not require human subjects)

Option 3 is strongly recommended as it adds an objective behavioral measure alongside the subjective Likert score.

---

### 11.4 Research Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| LLM API cost exceeds budget | Medium | High | Fix temperature=0; cache repeat reasoning calls; use Gemini Flash (lowest cost) |
| Expert annotation unavailable | High | Critical | Pre-annotate ALL conflict scenarios yourself + one domain-adjacent reviewer (e.g., CS faculty with disaster management knowledge); disclose IAA |
| Replanning cascade makes system unusable | Medium | High | Implement cooldown (Section 5.5) before any evaluation run |
| Human subject recruitment fails | High | Medium | Fall back to Option 3 (behavioral log analysis) |
| Simulation realism criticized | High | Medium | Bound all claims to *simulated cyclone response*; never claim real-world deployment readiness |

---

## Section 12 — Research Roadmap (Dependency Order)

```
PHASE 1 — RESEARCH FOUNDATIONS
────────────────────────────────────────────────────────────────
[1.1] Finalize SRS                               (COMPLETE)
[1.2] Finalize TAD                               (COMPLETE)
[1.3] Finalize Research Blueprint (this doc)     (COMPLETE)
[1.4] Create expert annotation sheet             (PREREQUISITE for M4)
      └─ Define all conflict scenarios
      └─ Record expert-assigned correct allocations
      └─ Compute IAA with 2 annotators
[1.5] Define simulation scenarios A, B, C        (PREREQUISITE for DT)
      └─ Fix all event tick numbers
      └─ Fix all parameter values

PHASE 2 — DIGITAL TWIN AND SIMULATION ENGINE
────────────────────────────────────────────────────────────────
[2.1] Implement 5 Digital Twin state models
      └─ Cyclone, Population, Shelter, Resource, Transport
[2.2] Implement simulation tick dispatcher
[2.3] Implement cyclone track model (3 scenarios)
[2.4] Implement shelter, resource, infrastructure simulators
[2.5] Implement probabilistic failure injection
      └─ MUST complete before evaluation
[2.6] Validate DT outputs against scenario specifications
      └─ Sanity check: shelter overflow at expected ticks

PHASE 3 — DATA LAYER
────────────────────────────────────────────────────────────────
[3.1] Deploy PostgreSQL + PostGIS schema (TAD Section 10)
      └─ DEPENDS ON: [1.5] for fixed scenario data
[3.2] Deploy Redis with Streams and keyspace notifications
[3.3] Implement Blackboard R/W protocol with optimistic locking
[3.4] Implement PostgreSQL sync worker (Redis → PostgreSQL every 5s)

PHASE 4 — AGENT LAYER
────────────────────────────────────────────────────────────────
[4.1] Implement Risk Assessment Agent
      └─ DEPENDS ON: [2.6] DT validated, [3.3] Blackboard ready
[4.2] Implement Shelter Agent
      └─ DEPENDS ON: [4.1]
[4.3] Implement Resource Agent
      └─ DEPENDS ON: [4.1]
[4.4] Implement Logistics Agent
      └─ DEPENDS ON: [4.2], [4.3]
[4.5] Implement Conflict Resolution Agent
      └─ DEPENDS ON: [4.2], [4.3] (consumes their outputs)
      └─ Implement Section 5.3 scoring model (deterministic)
      └─ Implement LLM explanation layer (post-hoc, separate)
[4.6] Implement LangGraph graph (TAD Section 6)
      └─ DEPENDS ON: all agents complete
      └─ Implement checkpoints, approval gate timeout interrupt

PHASE 5 — GOVERNANCE LAYER
────────────────────────────────────────────────────────────────
[5.1] Implement Approval Agent (state machine)
      └─ DEPENDS ON: [4.6]
[5.2] Implement approval escalation (Redis keyspace expiry)
[5.3] Implement immutable audit log writer
[5.4] Implement replanning engine
      └─ DEPENDS ON: [4.6], [5.1]
      └─ Implement cooldown constraint

PHASE 6 — FRONTEND AND API
────────────────────────────────────────────────────────────────
[6.1] Implement FastAPI endpoints (TAD Section 2)
      └─ DEPENDS ON: [3.1], [4.6]
[6.2] Implement EOC Dashboard (React/Next.js)
      └─ Blackboard state panel
      └─ Approval queue panel
      └─ Audit log panel
      └─ Explainability panel (explanation-present condition)
[6.3] Implement Stakeholder Portals (4 roles)
[6.4] Implement experiment recorder
      └─ Logs M1–M8 values per tick to CSV
      └─ MUST BE COMPLETE BEFORE EVALUATION BEGINS

PHASE 7 — EVALUATION
────────────────────────────────────────────────────────────────
[7.1] Run E1 (Baseline B1 — manual coordination, Scenario A)
      └─ DEPENDS ON: [6.4] recorder complete, [2.6] validated
[7.2] Run E2 (MIRAGE Full, Scenario A)
      └─ 3× with different simulation seeds
[7.3] Run E3 (No Conflict Resolution, Scenario A)
[7.4] Run E4 (No Explainability, Scenario A)
[7.5] Run H5 human study (explainability comprehension)
      └─ Recruit participants independently of evaluation run
[7.6] Run E5 (MIRAGE Full, Scenario B — stress test)
[7.7] Run E6 (MIRAGE + agent crash, Scenario C)
[7.8] Compute M1–M8 from recorded CSV + database query
[7.9] Statistical analysis (Welch t-test, Mann-Whitney U, Cohen's Kappa)
[7.10] Sensitivity analysis on priority weight vector (±20% perturbation)

PHASE 8 — PAPER WRITING
────────────────────────────────────────────────────────────────
[8.1] Write Abstract + Introduction
      └─ DEPENDS ON: [7.8] preliminary results available
[8.2] Write Related Work
      └─ CAN START IN PARALLEL with Phase 3
[8.3] Write System Design section (TAD → paper form)
[8.4] Write Evaluation section (RB Section 7 → paper form)
[8.5] Write Results section
      └─ DEPENDS ON: [7.10]
[8.6] Write Discussion + Limitations
[8.7] Peer review / supervisor feedback
[8.8] Revision cycle
[8.9] Final submission
```

---

> **Critical dependency note**: The expert annotation sheet ([1.4]) and the experiment recorder ([6.4]) are the two elements most likely to be deferred and least likely to be forgiven if missing. Both must be treated as Phase 1 and Phase 6 hard blockers respectively, not optional enhancements.
