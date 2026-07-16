# MIRAGE Research Blueprint (RB)
**Version:** 1.0  
**Date:** 2026-06-01  
**Document Type:** Research Blueprint  
**Status:** Finalized for evaluation and paper writing

---

## Section 1 — Research Positioning

### 1.1 Research Domain

MIRAGE sits at the intersection of four established research domains:

| Domain | Contribution to MIRAGE |
|---|---|
| Multi-Agent Systems (MAS) | Autonomous agent coordination, Blackboard architecture |
| Explainable Artificial Intelligence (XAI) | Decision transparency, evidence-backed recommendations |
| Human-Computer Interaction (HCI) | Approval workflows, stakeholder-facing governance |
| Disaster Informatics | Cyclone response operations, resource logistics |

The specific subdomain is: **Explainable Approval-Aware Multi-Agent Coordination for Crisis Response**.

---

### 1.2 Research Problem

Current disaster management systems—including NASA DRCS, FEMA platforms, GDACS, ReliefWeb, HDX, and Copernicus EMS—excel at one or more of the following:

- Geospatial data aggregation
- Satellite imagery processing
- Early warning dissemination
- Post-event damage assessment

**None of these systems address the operational coordination layer**: the moment after an alert has been issued and before field execution begins, when multiple competing operational decisions must be made under time pressure, resource scarcity, and incomplete information.

The specific problem is:

> *During active cyclone response, Emergency Operations Centers must simultaneously allocate scarce resources, resolve competing requests from multiple stakeholders, obtain approvals for high-stakes decisions, and replan operations as field conditions change—all without an integrated computational framework to assist, coordinate, or audit these processes.*

This coordination gap results in:
- Delayed decisions due to manual information aggregation
- Suboptimal resource allocation due to first-come-first-served practices
- Unresolved stakeholder conflicts
- Incomplete audit trails for post-event accountability

---

### 1.3 Research Gap

Analysis of literature from 2023–2026 identifies the following convergent gap:

| Capability | Existing Systems | MIRAGE |
|---|---|---|
| Situation awareness / alerting | Well-covered | Provided via simulation |
| Geospatial visualization | Well-covered | Partial (not core contribution) |
| Multi-agent coordination | Partial (academic prototypes) | Full 6-agent framework |
| Conflict resolution with scoring | Not found in operational systems | Weighted priority model |
| Human approval workflow with escalation | Absent | 3-level FSM |
| Explainable recommendations | Rare, not formalized | Evidence + reasoning per decision |
| Governance layer (audit + override) | Absent | Immutable audit log |
| Dynamic replanning on condition change | Manual in practice | Automated trigger + LangGraph replan |

The gap is not any single capability—it is the **absence of an integrated, explainable, approval-aware coordination framework** that handles recommendation, conflict, approval, execution, and audit in a unified operational system.

---

### 1.4 Research Motivation

Three convergent motivations justify MIRAGE:

**Operational**: Post-disaster reviews consistently identify coordination failures—conflicting resource allocations, delayed approvals, absent audit trails—as key contributors to inadequate response.

**Technical**: LangGraph-based multi-agent orchestration with LLM-generated explainability is emerging but has not been applied to structured approval-aware disaster coordination at the operational level.

**Accountability**: The rise of AI-assisted decision-making in emergency contexts demands traceable, overridable, human-in-the-loop systems. MIRAGE operationalizes this as a governance requirement, not an afterthought.

---

### 1.5 Research Contribution

| ID | Contribution | Type |
|---|---|---|
| C1 | Formalized 5-dimension priority scoring model for multi-party resource conflict resolution | Algorithmic / Mathematical |
| C2 | 3-level approval state machine with configurable escalation integrated into a multi-agent execution graph | Systems Design |
| C3 | Explainability layer separating deterministic allocation from LLM post-hoc evidence summaries | XAI Architecture |
| C4 | Governance layer providing immutable audit trails of all agent decisions, human approvals, and overrides | Systems Design |
| C5 | Parameterized Digital Twin simulation environment for reproducible cyclone response evaluation | Evaluation Methodology |

**What MIRAGE is NOT:**
- It is not a forecasting system.
- It is not a geospatial dashboard.
- It is not fully autonomous. Human approval is a hard constraint.
- It is not a general-purpose disaster platform. Cyclone response only.

---

### 1.6 Traditional Systems vs. MIRAGE

```
TRADITIONAL DISASTER MANAGEMENT SYSTEMS
─────────────────────────────────────────
Input:   Sensor feeds, satellite imagery, weather models
Process: Rule-based alert generation, threshold monitoring
Output:  Alerts, maps, visualizations, reports
Human:   Receives output, makes ALL coordination decisions manually
Audit:   Often absent or spreadsheet-based
Conflict: Resolved by phone call or seniority

MIRAGE
──────────────────────────────────────────
Input:   Simulation state, stakeholder requests, agent reasoning
Process: Multi-agent coordination → conflict scoring → approval gate → execution
Output:  Explainable recommendations, approval workflows, execution plans, audit log
Human:   Reviews recommendations, approves/rejects/overrides
Audit:   Immutable PostgreSQL log of every decision, approval, and override
Conflict: Resolved by formalized weighted scoring model
```

---

## Section 2 — Research Questions

### 2.1 Primary Research Question

> **RQ:** Does an explainable approval-aware multi-agent coordination framework (MIRAGE) reduce operational decision latency and improve resource allocation efficiency compared to manual coordination, while maintaining full decision auditability during simulated cyclone response?

---

### 2.2 Secondary Research Questions

| ID | Question |
|---|---|
| SRQ1 | Does the formalized conflict resolution model produce allocations that align with expert-defined priority judgements? |
| SRQ2 | Does the explainability layer improve stakeholder comprehension of agent recommendations compared to recommendation-only output? |
| SRQ3 | Does the approval workflow reduce unapproved decision execution compared to systems without governance constraints? |
| SRQ4 | How quickly does MIRAGE generate revised plans following unplanned infrastructure failure? |
| SRQ5 | Does the multi-agent framework maintain operational continuity under single-agent failure? |

---

### 2.3 Research Objectives

| ID | Objective |
|---|---|
| O1 | Design and implement a 6-agent coordination system for cyclone disaster response |
| O2 | Formalize a weighted priority scoring model for resource conflict resolution |
| O3 | Implement a 3-level approval workflow with escalation and immutable audit logging |
| O4 | Build a Digital Twin–based simulation environment with three reproducible evaluation scenarios |
| O5 | Evaluate MIRAGE against five baselines across six experiments using eight quantitative metrics |
| O6 | Assess explainability outputs via structured human evaluation |

---

### 2.4 Research Scope

- **Disaster type:** Cyclone response only
- **Phase:** Post-alert operational coordination
- **Stakeholders:** EOC, Shelter Manager, Logistics Officer, Medical Coordinator
- **Evaluation mode:** Simulation-based (no live field deployment)
- **Agent architecture:** LangGraph-orchestrated, Blackboard-based, 6 agents fixed

---

### 2.5 Research Boundaries

| In Scope | Out of Scope |
|---|---|
| Operational coordination decisions | Cyclone forecasting or early warning |
| Resource allocation conflict resolution | Field execution tracking |
| Approval workflow governance | Real-world RCT at scale |
| Digital Twin simulation | Real-time satellite/sensor integration |
| Explainability of agent recommendations | Full NLP generation |
| Single-region cyclone response | Multi-disaster coordination |

---

## Section 3 — Novelty Statement

### 3.1 Component-by-Component Novelty Evaluation

| Component | Novel? | Assessment |
|---|---|---|
| Multi-Agent Systems for disaster response | No | Studied extensively since 1990s |
| Blackboard Architecture | No | Classic 1986 architecture (Nii) |
| LangGraph as orchestration | Partially | New framework (2024); disaster coordination application not yet published |
| Digital Twin for disaster simulation | Partially | Exists for infrastructure; not for multi-agent coordination evaluation |
| Conflict Resolution in MAS | No | Standard MAS topic |
| Approval Workflow in MAS | Partially | Human-in-the-loop approval in operational disaster MAS is rare |
| Explainability Layer (XAI) | Partially | Applied to forecasting, not operational coordination |
| Governance Layer (audit + override) | Yes | Formalized governance in disaster coordination MAS is absent in literature |

---

### 3.2 What Is Truly Novel

No single component is individually novel. The novelty is compositional:

**Novel Contribution 1 — Coordination–Governance Coupling:**  
Integration of a multi-agent recommendation engine with a formalized approval state machine, escalation rules, and immutable audit logging within a single operational coordination framework has not been published in disaster informatics literature.

**Novel Contribution 2 — Explainability Without LLM Decision Authority:**  
MIRAGE separates algorithmic decision-making (deterministic priority scoring) from LLM-generated explanation (post-hoc rationale). The LLM cannot alter allocation outcomes. This addresses a critical accountability concern not explicitly resolved in existing XAI systems.

**Novel Contribution 3 — Evaluation via Parameterized Digital Twin:**  
A parameterized cyclone Digital Twin generates reproducible, controlled evaluation scenarios allowing comparison across baselines with identical conditions—a methodological improvement over prior work relying on historical case studies.

---

### 3.3 What Must Not Be Claimed Novel

- The Blackboard architecture itself
- Multi-agent coordination in general
- LLM-generated text explanations
- Disaster resource allocation algorithms in isolation
- Approval workflows in software engineering (BPMN, workflow engines)

---

### 3.4 Final Novelty Statement

> MIRAGE contributes a novel **Explainable Approval-Aware Multi-Agent Coordination Framework** for cyclone disaster response in which: (1) resource conflict resolution is governed by a formalized weighted priority scoring model; (2) every recommendation passes through a legally auditable, human-in-the-loop approval state machine; and (3) explainability is provided via architectural separation between deterministic allocation algorithms and LLM-generated post-hoc evidence summaries. The framework is evaluated using a parameterized Digital Twin simulation environment with three controlled scenarios and five baselines, enabling reproducible experimental comparison—a methodological contribution to disaster informatics evaluation practice.

---

## Section 4 — Hypotheses

### H1 — Decision Latency

> **H1:** MIRAGE reduces mean operational decision latency compared to manual coordination.

- **H1₀:** No significant difference in decision latency.
- **Operationalization:** Latency = elapsed time from event trigger to actionable plan generation.
- **Expected direction:** MIRAGE (≤5s) vs. Manual (≥5 min).
- **Statistical test:** Welch's t-test on latency distributions (MIRAGE vs. B1).

---

### H2 — Resource Allocation Efficiency

> **H2:** MIRAGE achieves higher priority-weighted resource allocation efficiency than first-come-first-served allocation during resource scarcity.

- **H2₀:** No significant efficiency difference vs. FCFS.
- **Operationalization:** η = Σ(p_i · a_{ik}) / Σ(p_i · q_{ik}). See Section 5.3.
- **Expected direction:** MIRAGE > FCFS because priority scoring allocates to highest-need requesters first.

---

### H3 — Conflict Resolution Accuracy

> **H3:** The priority scoring model produces allocations agreeing with expert-defined judgements at rate ≥ 80%.

- **H3₀:** Expert agreement ≤ 50% (random chance).
- **Operationalization:** Cohen's Kappa between MIRAGE outcomes and pre-annotated expert solutions.
- **Expected direction:** κ ≥ 0.75 (substantial agreement).

---

### H4 — Replanning Speed

> **H4:** MIRAGE generates revised plans within 10 seconds of a replanning trigger event.

- **H4₀:** Mean replanning latency ≥ 10 seconds.
- **Operationalization:** Time from ReplanTriggered event to new DECISIONS record on Blackboard.
- **Note:** Performance hypothesis. Falsification implies engineering failure, not research failure.

---

### H5 — Explainability Comprehension

> **H5:** Stakeholders with explainability outputs demonstrate higher comprehension of allocation decisions than stakeholders with recommendation-only outputs.

- **H5₀:** No significant comprehension difference.
- **Operationalization:** Structured questionnaire (Likert 1–5, 5 items) in explanation-present vs. explanation-absent conditions.
- **Statistical test:** Mann-Whitney U test.
- **Minimum participants:** 10 per condition (20 total).

---

## Section 5 — Mathematical Models

### Notation

| Symbol | Definition |
|---|---|
| *i* | Request index |
| *k* | Resource type index |
| *t* | Simulation tick |
| *R_k* | Available quantity of resource type *k* |
| *q_{ik}* | Quantity of resource *k* requested by *i* |
| *p_i* | Priority score of request *i* |
| *a_{ik}* | Quantity of resource *k* allocated to *i* |

---

### 5.1 Risk Score Model

**Purpose:** Normalized risk score for each zone given cyclone state.

**Variables:**

| Symbol | Definition | Unit | Max |
|---|---|---|---|
| v | Wind speed | km/h | 300 |
| σ | Storm surge | m | 15 |
| ρ | Rainfall | mm/hr | 200 |
| d | Distance to cyclone eye | km | — |
| P | Zone population density | persons/km² | P_max |

**Formula:**

```
RS = [ w_v·(v/300) + w_σ·(σ/15) + w_ρ·(ρ/200) + w_P·(P/P_max) ] · exp(−λd)

λ = 0.01  (distance decay constant)
RS ∈ [0, 1]
```

**Default weights:** w_v = 0.40, w_σ = 0.25, w_ρ = 0.15, w_P = 0.20

**Assumptions:**
- Components are linearly independent (simplification; correlation exists).
- λ = 0.01 is empirically reasonable for 100–300 km impact radii.
- All inputs available from simulation engine at each tick.

---

### 5.2 Resource Priority Model

**Purpose:** Score each resource request for conflict allocation.

**Formula:**

```
p_i = 0.40·L_i + 0.25·RS_i + 0.15·D_i + 0.10·C_k + 0.10·U_i

p_i ∈ [0, 1]
```

**Subscales:**

*Life Safety Risk (L_i):*

| Condition | L_i |
|---|---|
| Immediate life threat | 1.00 |
| < 1 day supply remaining | 0.75 |
| 1–3 day supply | 0.50 |
| Precautionary | 0.25 |
| Logistical only | 0.00 |

*Resource Criticality (C_k):*

| Type | C_k |
|---|---|
| Water | 1.0 |
| Food | 0.8 |
| Medical Kit | 0.7 |
| Fuel | 0.5 |
| Blanket | 0.2 |

*Time Urgency (U_i):*

| Time to Need | U_i |
|---|---|
| ≤ 2 sim-hours | 1.0 |
| 2–6 sim-hours | 0.6 |
| 6–12 sim-hours | 0.3 |
| > 12 sim-hours | 0.0 |

---

### 5.3 Conflict Resolution Scoring Model

**Purpose:** Allocate resource type *k* across *n* competing requests.

**Algorithm — Greedy Priority Allocation:**

```
1. Sort requests: π = argsort(p, descending=True)
2. remaining = R_k
3. For each i in π:
     if remaining ≥ q_{ik}:   a_{ik} = q_{ik};     remaining -= q_{ik}
     elif remaining > 0:       a_{ik} = remaining;   remaining = 0
     else:                     a_{ik} = 0

4. Priority-weighted efficiency:
       η_k = Σ_i (p_i · a_{ik}) / Σ_i (p_i · q_{ik})    ∈ [0, 1]
```

**Tie-breaking:** Equal p_i → earliest `created_at` timestamp wins (ensures determinism).

**Assumptions:**
- Resources are homogeneous within type.
- Partial fulfillment is preferred over zero fulfillment.
- Scoring model is a proxy for operational utility, not claimed welfare measure.

---

### 5.4 Approval Escalation Model

**Variables:**

| Symbol | Definition |
|---|---|
| L | Current approval level ∈ {0, 1, 2, 3} |
| T_L | Timeout threshold at level L |
| e | Escalation count |
| e_max | Max escalations before EXPIRED (= 2) |
| α | Simulation speed multiplier |

**Timeout values (wall-clock seconds):**

```
T_0 = 0          (auto-approve)
T_1 = 1800 / α
T_2 = 900  / α
T_3 = 600  / α
```

**State transition function:**

```
on APPROVED:                     → APPROVED;  trigger execute_plan
on REJECTED:                     → REJECTED;  trigger ReplanTriggered
on TIMEOUT and e < e_max:        → ESCALATED; L += 1; e += 1; deadline = NOW + T_L
on TIMEOUT and e >= e_max:       → EXPIRED;   trigger EOC_HARD_ALERT

Auto-approve (L=0) iff:  p_i < 0.3  AND  q_{ik} < 0.10·R_k  AND  conflicts(i) = ∅
```

---

### 5.5 Replanning Trigger Model

**Trigger condition:**

```
trigger_replan(event E, state S) → (trigger: bool, scope: Set[task_id])

if E.type = ROUTE_BLOCKED:
    scope = {t ∈ S.tasks : t.route_id = E.route_id AND t.status ∈ {PENDING,APPROVED,EXECUTING}}
    trigger = True

if E.type = RESOURCE_SHORTAGE:
    scope = {t ∈ S.tasks : t.resource_type = E.resource_type AND t.status ∈ {PENDING,APPROVED}}
    trigger = True

if E.type = CYCLONE_UPDATED AND |Δcategory| ≥ 2:
    scope = S.tasks   (full replan)
    trigger = True

if E.type = APPROVAL_REJECTED:
    scope = {d : d.decision_id = E.decision_id}
    trigger = True
```

**Cascade prevention cooldown:**

```
Replan suppressed if:  NOW − last_replan_time[scope_key] < Δ_cooldown

Δ_cooldown = 60 simulation-seconds  (configurable)
```

**Expected latency:** ≈ n_a × LLM_latency + n_t × DB_write_latency ≤ 10s for n_a=2, n_t=10.
