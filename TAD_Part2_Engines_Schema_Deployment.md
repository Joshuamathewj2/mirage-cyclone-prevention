## 8. Approval Workflow Engine

### 8.1 Approval State Machine

```
                      ┌──────────────┐
                      │   CREATED    │ ← ApprovalRequested event fired
                      └──────┬───────┘
                             │ routed to role
                             ▼
                      ┌──────────────┐
                      │   PENDING    │ ← waiting for stakeholder action
                      └──────┬───────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
   deadline expires    stakeholder        stakeholder
   (timeout interrupt)  approves           rejects
          │                  │                  │
          ▼                  ▼                  ▼
   ┌───────────┐      ┌────────────┐     ┌───────────┐
   │ ESCALATED │      │  APPROVED  │     │ REJECTED  │
   └─────┬─────┘      └─────┬──────┘     └─────┬─────┘
         │                  │                   │
   re-assigned              │             ReplanTriggered
   to EOC (L2)              ▼                   event
         │           ┌──────────────┐
         │           │  EXECUTING   │ ← execute_plan node fires
         │           └──────────────┘
         │
   ┌─────▼──────┐
   │  PENDING   │ ← L2 review cycle restarts
   └─────┬──────┘
         │
   max escalations (2) reached
         │
         ▼
   ┌───────────┐
   │  EXPIRED  │ ← EOC hard alert, no action taken, logged
   └───────────┘
```

### 8.2 Escalation Rules

| Level | Assigned To | Timeout | On Timeout |
|---|---|---|---|
| L0 (auto-approve) | None | — | Immediate execution (low-risk decisions only) |
| L1 | Domain stakeholder (Shelter Mgr / Logistics / Medical) | 30 min (sim) | Escalate to L2 |
| L2 | Emergency Operations Center | 15 min (sim) | Escalate to L3 |
| L3 | EOC Director (highest role) | 10 min (sim) | EXPIRED — log + no action |

**Auto-approve criteria** (L0):
- Resource request quantity < 10% of available stock
- Life Safety Risk score < 0.3
- No conflicting requests

> [!WARNING]
> **Weakness**: Real simulation timescales run faster than real-time. 30 minutes of simulation time may be 3 minutes of wall-clock time. The approval timeout values MUST be parameterized against the simulation speed multiplier, not hardcoded. Hardcoded timeouts will make the approval workflow untestable at 10× simulation speed.

### 8.3 Audit Logging Schema (per approval event)

```sql
-- Every state transition generates one audit_log row
CREATE TABLE approval_audit_log (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id     UUID NOT NULL REFERENCES approvals(approval_id),
    event_type      TEXT NOT NULL,  -- CREATED/PENDING/APPROVED/REJECTED/ESCALATED/EXPIRED
    from_state      TEXT,
    to_state        TEXT NOT NULL,
    actor_id        UUID,           -- NULL for system-generated transitions
    actor_role      TEXT,
    reason          TEXT,
    decision_snapshot JSONB,        -- full snapshot of DECISIONS record at this moment
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 9. Dynamic Replanning Engine

### 9.1 Trigger Conditions

| Trigger Event | Source | Replanning Scope |
|---|---|---|
| `RouteBlocked` | Simulation Engine | Logistics Agent re-plans delivery routes for all EXECUTING tasks on that route |
| `ResourceShortageDetected` | Resource Agent | Conflict Agent re-runs allocation for all affected TASKS |
| `ShelterFull` | Shelter Agent | Shelter Agent + Logistics Agent re-plan evacuation routing |
| `ApprovalRejected` | Approval Agent | Originating agent re-generates recommendation with rejection reason as constraint |
| `CycloneUpdated` (category jump ≥2) | Simulation Engine | Full graph re-run from `risk_assessment` node |
| `AgentCrashed` | Health Monitor | Orchestrator assigns surviving agents to cover crashed agent's TASKS |

### 9.2 Replanning Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                     REPLANNING WORKFLOW                          │
│                                                                  │
│  1. TRIGGER DETECTED                                             │
│     └─→ ReplanTriggered event published on ch:replan            │
│                                                                  │
│  2. IDENTIFY AFFECTED TASKS                                      │
│     └─→ Query TASKS where status=PENDING or APPROVED            │
│         filtered by trigger scope (route_id / resource_type /   │
│         shelter_id)                                              │
│                                                                  │
│  3. FREEZE AFFECTED TASKS                                        │
│     └─→ Set TASKS.status = REPLANNING (prevents race conditions) │
│                                                                  │
│  4. AGENT RE-RUN (scoped)                                        │
│     └─→ LangGraph re-enters at appropriate node (not full       │
│         restart) with updated constraints injected into state   │
│                                                                  │
│  5. GENERATE NEW DECISIONS                                       │
│     └─→ New DECISIONS records created                           │
│         Old DECISIONS marked status=SUPERSEDED                  │
│                                                                  │
│  6. APPROVAL RE-ROUTING                                          │
│     └─→ If original decision was already APPROVED,              │
│         new decision requires fresh approval                    │
│         If original was PENDING, replace in-place               │
│                                                                  │
│  7. NOTIFY STAKEHOLDERS                                          │
│     └─→ WebSocket push to affected portals                      │
│         Summary of what changed and why                         │
│                                                                  │
│  8. AUDIT                                                        │
│     └─→ Replan event + old/new decision diff written to log     │
└──────────────────────────────────────────────────────────────────┘
```

> [!CAUTION]
> **Cascade risk**: If a RouteBlocked triggers a replan that triggers a ResourceShortageDetected (because rerouting now burns more fuel), the system could enter a replan cascade. You MUST implement a replan cooldown: minimum 60 simulation-seconds between successive ReplanTriggered events for the same scope. Without this, the evaluation experiments will be invalid because the system will spend all time replanning.

---

## 10. PostgreSQL + PostGIS Schema

### 10.1 Entity-Relationship Overview

```
cyclones ──< incidents
shelters ──< shelter_inventory_snapshots
shelters ──< shelter_occupancy_snapshots
resources ──< resource_transactions
routes ──< route_blockages
tasks ──< task_assignments
decisions ──< decision_evidence
approvals ──< approval_audit_log
conflicts ──< conflict_request_links
```

### 10.2 Table Definitions

```sql
-- ================================================
-- ENABLE EXTENSIONS
-- ================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ================================================
-- CYCLONES
-- ================================================
CREATE TABLE cyclones (
    cyclone_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id   UUID NOT NULL,
    name            TEXT NOT NULL,
    category        INT NOT NULL CHECK (category BETWEEN 1 AND 5),
    position        GEOGRAPHY(Point, 4326) NOT NULL,
    wind_speed_kmh  DECIMAL(6,2) NOT NULL,
    storm_surge_m   DECIMAL(4,2),
    rainfall_mm     DECIMAL(6,2),
    predicted_path  GEOGRAPHY(LineString, 4326),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_cyclones_position ON cyclones USING GIST (position);
CREATE INDEX idx_cyclones_sim ON cyclones (simulation_id, recorded_at DESC);

-- ================================================
-- SHELTERS
-- ================================================
CREATE TABLE shelters (
    shelter_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    location        GEOGRAPHY(Point, 4326) NOT NULL,
    capacity        INT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'OPERATIONAL'
                    CHECK (status IN ('OPERATIONAL','FULL','DAMAGED','CLOSED')),
    zone_id         TEXT NOT NULL
);
CREATE INDEX idx_shelters_location ON shelters USING GIST (location);
CREATE INDEX idx_shelters_zone ON shelters (zone_id);

CREATE TABLE shelter_snapshots (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shelter_id          UUID NOT NULL REFERENCES shelters(shelter_id),
    tick_number         INT NOT NULL,
    current_occupancy   INT NOT NULL,
    food_days_remaining DECIMAL(4,2),
    water_days_remaining DECIMAL(4,2),
    overflow_risk       DECIMAL(4,3) CHECK (overflow_risk BETWEEN 0 AND 1),
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_shelter_snap_shelter ON shelter_snapshots (shelter_id, recorded_at DESC);

-- ================================================
-- RESOURCES
-- ================================================
CREATE TABLE resources (
    resource_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            TEXT NOT NULL
                    CHECK (type IN ('FOOD','WATER','FUEL','MEDICAL_KIT','BLANKET')),
    quantity        DECIMAL(10,2) NOT NULL,
    unit            TEXT NOT NULL,
    location        GEOGRAPHY(Point, 4326),
    shelter_id      UUID REFERENCES shelters(shelter_id),
    reorder_threshold DECIMAL(10,2),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE resource_transactions (
    tx_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id     UUID NOT NULL REFERENCES resources(resource_id),
    task_id         UUID REFERENCES tasks(task_id),
    delta           DECIMAL(10,2) NOT NULL,  -- negative = consumed
    reason          TEXT,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- ROUTES
-- ================================================
CREATE TABLE routes (
    route_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin          GEOGRAPHY(Point, 4326) NOT NULL,
    destination     GEOGRAPHY(Point, 4326) NOT NULL,
    path            GEOGRAPHY(LineString, 4326),
    distance_km     DECIMAL(8,2),
    status          TEXT NOT NULL DEFAULT 'CLEAR'
                    CHECK (status IN ('CLEAR','BLOCKED','DEGRADED'))
);
CREATE INDEX idx_routes_path ON routes USING GIST (path);

CREATE TABLE route_blockages (
    blockage_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id        UUID NOT NULL REFERENCES routes(route_id),
    reason          TEXT NOT NULL,
    blockage_point  GEOGRAPHY(Point, 4326),
    started_at      TIMESTAMPTZ NOT NULL,
    cleared_at      TIMESTAMPTZ
);

-- ================================================
-- TASKS
-- ================================================
CREATE TABLE tasks (
    task_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            TEXT NOT NULL,
    created_by      TEXT NOT NULL,   -- agent name
    priority        DECIMAL(4,3)     CHECK (priority BETWEEN 0 AND 1),
    status          TEXT NOT NULL    DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','APPROVED','EXECUTING',
                                      'COMPLETED','REJECTED','REPLANNING','SUPERSEDED')),
    resource_type   TEXT,
    resource_qty    DECIMAL(10,2),
    target_shelter  UUID REFERENCES shelters(shelter_id),
    target_route    UUID REFERENCES routes(route_id),
    deadline        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tasks_status ON tasks (status);
CREATE INDEX idx_tasks_type ON tasks (type, created_at DESC);

-- ================================================
-- DECISIONS
-- ================================================
CREATE TABLE decisions (
    decision_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by_agent TEXT NOT NULL,
    recommendation  TEXT NOT NULL,
    reasoning       TEXT NOT NULL,
    evidence        JSONB NOT NULL DEFAULT '[]',
    confidence      DECIMAL(4,3)   CHECK (confidence BETWEEN 0 AND 1),
    priority_score  DECIMAL(4,3)   CHECK (priority_score BETWEEN 0 AND 1),
    status          TEXT NOT NULL  DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','APPROVED','REJECTED','SUPERSEDED','EXPIRED')),
    conflict_id     UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================
-- APPROVALS
-- ================================================
CREATE TABLE approvals (
    approval_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id         UUID NOT NULL REFERENCES decisions(decision_id),
    level               INT NOT NULL DEFAULT 1,   -- 0=auto, 1=L1, 2=L2, 3=L3
    assigned_to_role    TEXT NOT NULL,
    assigned_to_user_id UUID,
    status              TEXT NOT NULL DEFAULT 'PENDING'
                        CHECK (status IN ('PENDING','APPROVED','REJECTED',
                                          'ESCALATED','EXPIRED')),
    deadline            TIMESTAMPTZ NOT NULL,
    approved_at         TIMESTAMPTZ,
    rejection_reason    TEXT,
    escalation_count    INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_approvals_status ON approvals (status, deadline);

-- ================================================
-- APPROVAL AUDIT LOG (from Section 8.3)
-- ================================================
CREATE TABLE approval_audit_log (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id         UUID NOT NULL REFERENCES approvals(approval_id),
    event_type          TEXT NOT NULL,
    from_state          TEXT,
    to_state            TEXT NOT NULL,
    actor_id            UUID,
    actor_role          TEXT,
    reason              TEXT,
    decision_snapshot   JSONB,
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_approval ON approval_audit_log (approval_id, occurred_at);
CREATE INDEX idx_audit_time ON approval_audit_log (occurred_at DESC);

-- ================================================
-- CONFLICTS
-- ================================================
CREATE TABLE conflicts (
    conflict_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type       TEXT NOT NULL,
    available_quantity  DECIMAL(10,2) NOT NULL,
    total_requested     DECIMAL(10,2) NOT NULL,
    deficit             DECIMAL(10,2) NOT NULL,
    resolution_decision_id UUID REFERENCES decisions(decision_id),
    resolved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conflict_request_links (
    conflict_id     UUID NOT NULL REFERENCES conflicts(conflict_id),
    task_id         UUID NOT NULL REFERENCES tasks(task_id),
    priority_score  DECIMAL(4,3),
    allocated_qty   DECIMAL(10,2),
    explanation     TEXT,
    PRIMARY KEY (conflict_id, task_id)
);
```

> [!WARNING]
> **PostGIS over-engineering flag**: The schema correctly uses `GEOGRAPHY` types for all spatial data, but if the simulation runs entirely within a single coastal district, plain `FLOAT` lat/lon with a computed Haversine distance would be equally valid and faster. Only use PostGIS if you actually query spatial relationships (e.g., "find all shelters within 50km of cyclone path"). If you do intend to use it, add a working `ST_DWithin` query in the evaluation section to justify the dependency.

---

## 11. Redis Usage Model

### 11.1 Key Namespace Structure

```
mirage:{sim_id}:blackboard:incidents:{cyclone_id}     → JSON hash
mirage:{sim_id}:blackboard:shelters:{shelter_id}      → JSON hash
mirage:{sim_id}:blackboard:resources:{resource_id}    → JSON hash
mirage:{sim_id}:blackboard:routes:{route_id}          → JSON hash
mirage:{sim_id}:blackboard:tasks:{task_id}            → JSON hash
mirage:{sim_id}:blackboard:decisions:{decision_id}    → JSON hash
mirage:{sim_id}:blackboard:approvals:{approval_id}    → JSON hash

mirage:{sim_id}:streams:cyclone                       → Redis Stream
mirage:{sim_id}:streams:risk                          → Redis Stream
mirage:{sim_id}:streams:shelter                       → Redis Stream
mirage:{sim_id}:streams:resource                      → Redis Stream
mirage:{sim_id}:streams:routes                        → Redis Stream
mirage:{sim_id}:streams:conflicts                     → Redis Stream
mirage:{sim_id}:streams:approvals                     → Redis Stream
mirage:{sim_id}:streams:replan                        → Redis Stream
mirage:{sim_id}:streams:system                        → Redis Stream

mirage:{sim_id}:locks:{region}:{id}                   → SET NX PX (distributed lock)
mirage:{sim_id}:agent:health:{agent_name}             → SETEX (heartbeat, TTL=10s)
```

### 11.2 Redis Usage by Purpose

| Purpose | Redis Primitive | TTL | Notes |
|---|---|---|---|
| Blackboard operational state | String (JSON) | sim_duration + 1hr | Primary live store |
| Event bus | Streams (XADD/XREAD) | 24hr | Consumer groups per agent |
| Distributed locking | SET NX PX | 5s max | Prevents write conflicts |
| Agent health heartbeat | SETEX | 10s | Missing → AgentCrashed event |
| Approval deadline timers | PEXPIREAT on approval key | deadline | On expiry: escalation trigger |
| Session/auth tokens | SETEX | 8hr | User session management |
| Simulation clock | String | sim_duration | Single source of tick time |

> [!NOTE]
> **Approval deadline via Redis TTL**: Setting a `PEXPIREAT` on the approval hash key and watching for keyspace expiry events (`CONFIG SET notify-keyspace-events Ex`) is an elegant mechanism for timeout-driven escalation without polling. Enable keyspace notifications in Redis config and subscribe to `__keyevent@0__:expired` in the Approval Agent.

---

## 12. Simulation Engine Architecture

### 12.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SIMULATION ENGINE                              │
│                                                                     │
│  ┌────────────────────┐    ┌─────────────────────────────────────┐  │
│  │  SIMULATION CLOCK  │───►│  TICK DISPATCHER                    │  │
│  │  configurable rate │    │  fires simulation_tick LangGraph node│  │
│  │  (1x to 60x speed) │    └──────────────┬──────────────────────┘  │
│  └────────────────────┘                   │                         │
│                                 ┌─────────┼──────────┐             │
│                                 │         │          │             │
│                          ┌──────▼──┐ ┌────▼────┐ ┌──▼──────────┐  │
│                          │ CYCLONE │ │ SHELTER │ │ RESOURCE     │  │
│                          │ SIM     │ │ SIM     │ │ SIM          │  │
│                          └──────┬──┘ └────┬────┘ └──┬──────────┘  │
│                                 │         │         │              │
│                          ┌──────▼─────────▼─────────▼───────────┐ │
│                          │     INFRASTRUCTURE FAILURE SIM        │ │
│                          └───────────────────────────────────────┘ │
│                                           │                         │
│                                           ▼                         │
│                                  writes to Blackboard               │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 Cyclone Simulator

**State Variables per tick:**
- `category` (1–5, may increase or decrease)
- `position` (lat/lon, advances along parameterized track)
- `wind_speed_kmh`
- `storm_surge_m`
- `rainfall_mm_per_hr`

**Track Model:**
```python
class CycloneTrack:
    control_points: List[GeoPoint]   # pre-defined waypoints
    landfall_tick: int               # tick number at landfall
    weakening_rate: float            # category reduction per tick post-landfall

def advance_cyclone(state: CycloneState, tick: int) -> CycloneState:
    # Interpolate position along control_points for this tick
    # Apply intensity changes (ramp up pre-landfall, weaken post-landfall)
    # Inject random perturbation ±5% on wind speed (realism)
    ...
```

**Pre-built scenarios:**
| Scenario | Description |
|---|---|
| `scenario_A` | Cat 3 → Cat 5 before landfall, rapid weakening post |
| `scenario_B` | Slow-moving Cat 4, prolonged rainfall, multiple route blockages |
| `scenario_C` | Stall-then-accelerate Cat 3, sudden direction change |

### 12.3 Shelter Simulator

```python
def shelter_tick(shelter: Shelter, cyclone: CycloneState, tick: int) -> Shelter:
    # Arrival rate = f(distance_to_cyclone, zone_population, road_status)
    arrivals = compute_arrivals(shelter, cyclone)
    
    # Consumption: food and water per person per tick
    food_consumed = shelter.occupancy * FOOD_PER_PERSON_PER_TICK
    water_consumed = shelter.occupancy * WATER_PER_PERSON_PER_TICK
    
    shelter.occupancy = min(shelter.capacity * 1.2, shelter.occupancy + arrivals)  # allow 20% overflow
    shelter.food_stock -= food_consumed
    shelter.water_stock -= water_consumed
    
    # Publish events if thresholds breached
    if shelter.occupancy >= shelter.capacity:
        publish(ShelterFull(shelter_id=shelter.shelter_id))
    ...
    return shelter
```

### 12.4 Resource Consumption Simulator

| Resource | Consumption Model |
|---|---|
| Food | `occupancy × 0.5 kg/tick` (tick = 6hr equivalent) |
| Water | `occupancy × 3 L/tick` |
| Fuel | `vehicles_deployed × 15 L/tick` |
| Medical Kits | `injured_population × 0.02 kits/tick` (injury rate from cyclone intensity) |
| Blankets | `new_arrivals × 1 blanket` (one-time, not per-tick) |

### 12.5 Infrastructure Failure Simulator

```python
FAILURE_EVENTS = [
    # (tick_number, event_type, target_id, parameters)
    (10, "ROUTE_BLOCKED",  "route_001", {"reason": "flooding"}),
    (18, "ROUTE_BLOCKED",  "route_003", {"reason": "debris"}),
    (25, "SHELTER_DAMAGED","shelter_05", {"capacity_reduction": 0.4}),
    (35, "POWER_OUTAGE",   "zone_B",    {"affected_shelters": ["shelter_02","shelter_07"]}),
    (50, "ROUTE_CLEARED",  "route_001", {}),
]
```

> [!WARNING]
> **Realism flag**: Hardcoded failure events at fixed ticks are deterministic and will not generalize. You MUST also implement a probabilistic failure mode: each route has `failure_probability_per_tick` sampled from a cyclone-intensity curve. Otherwise the simulation is a scripted replay, not a simulation, and reviewers will correctly flag this as insufficient for a research-grade evaluation.

---

## 13. Evaluation Framework

### 13.1 Metrics

| Metric ID | Name | Formula | Unit | Target |
|---|---|---|---|---|
| M1 | Decision Latency | `t_decision_ready - t_event_fired` | seconds | ≤ 5s |
| M2 | Approval Cycle Time | `t_approved - t_approval_requested` | minutes | ≤ 5 min (sim) |
| M3 | Resource Allocation Efficiency | `Σ allocated_qty / Σ requested_qty` | ratio 0–1 | ≥ 0.85 |
| M4 | Conflict Resolution Accuracy | Expert agreement rate on allocation decisions | % | ≥ 80% |
| M5 | Replanning Speed | `t_new_plan_ready - t_trigger_event` | seconds | ≤ 10s |
| M6 | Explainability Score | Likert 1–5, human evaluators rate explanation clarity | score | ≥ 4.0 |
| M7 | Missed Critical Events | Events that were not acted upon within deadline | count | 0 |
| M8 | Audit Completeness | `audit_log entries / expected entries` | ratio | 1.0 |

### 13.2 Experiments

| Experiment | Configuration | Measures |
|---|---|---|
| **E1 — Baseline** | Human-only. Scenario A played out. Coordinator uses spreadsheets + phone. Timed manually. | M1, M2, M3 (ground truth) |
| **E2 — MIRAGE Full** | All agents active, full approval workflow, explainability on. Scenario A. | M1–M8 |
| **E3 — No Conflict Resolution** | Agents active, conflict detection OFF. First-come first-served allocation. Scenario A. | M3, M4 (ablation) |
| **E4 — No Explainability** | Agents active, decision reasoning hidden from UI. Scenario A. | M6 (ablation) |
| **E5 — Stress Test** | Scenario B (slow-moving, prolonged). All agents. | M1, M5, M7 |
| **E6 — Failure Recovery** | Agent crash injected mid-simulation (Scenario C). | M7, system resilience |

### 13.3 Baselines

| Baseline | Description |
|---|---|
| B1 — Manual | Human coordinator, no AI assistance |
| B2 — First-Come-First-Served | Resources allocated in request arrival order, no prioritization |
| B3 — Equal-Split | Conflict resolved by splitting resources equally |

> [!WARNING]
> **Evaluation weakness — statistical validity**: Three scenarios and five experiments with a single human coordinator as B1 is NOT statistically valid. You need either: (a) multiple human subjects as baseline evaluators (minimum 3), or (b) frame E1 as a "reference run" not a "statistical baseline." For a final year project, framing it as (b) is acceptable but MUST be clearly disclosed in the paper's limitations section. Do not claim statistical significance from N=1.

> [!WARNING]
> **M4 ground truth problem**: "Expert agreement" requires defining a gold-standard allocation for each conflict scenario IN ADVANCE, before running experiments. Create an expert annotation sheet with correct allocations for all 15+ conflict scenarios in the simulation. Without this, M4 cannot be computed and the evaluation collapses.

---

## 14. Failure Scenarios

### 14.1 Agent Crash

```
DETECTION:
  Health monitor checks Redis heartbeat key: mirage:{sim_id}:agent:health:{agent_name}
  If key absent (TTL expired, no heartbeat for >10s):
    → Publish AgentCrashed event on ch:system

RESPONSE:
  If crashed agent = Risk Assessment Agent:
    → Use last known INCIDENTS.risk_score (stale, flagged in UI)
    → Downstream agents continue with stale data, UI shows warning banner
    → No replanning (risk data is read-only input)
    
  If crashed agent = Shelter / Resource / Logistics Agent:
    → Mark all TASKS created by that agent as status=SUSPENDED
    → EOC receives alert: "Shelter Agent offline — tasks suspended"
    → No automatic reassignment (operator must restart agent)
    
  If crashed agent = Conflict Resolution Agent:
    → All incoming ConflictDetected events queued in Redis Stream
    → When agent restarts, processes backlog
    → If queue > 10 events: EOC alert
    
  If crashed agent = Approval Agent:
    → All PENDING approvals retain their status
    → Deadline timers continue via Redis keyspace events (not agent-managed)
    → Agent restart replays APPROVALS stream from last ACK position

RECOVERY:
  All agents implement XREAD with XACK (consumer groups)
  On restart: agent reads from last unacknowledged stream position
  Blackboard state persists in Redis and PostgreSQL — no data loss
```

### 14.2 Stale Blackboard State

```
DETECTION:
  Each Blackboard write includes: {value, written_at, written_by, tick}
  Staleness check: if NOW() - written_at > STALE_THRESHOLD (default: 2 ticks)
    → Agent receiving stale data publishes DataStalenessWarning on ch:system
    → UI renders stale indicators on affected dashboard panels

MITIGATION:
  Agents that read stale critical data (INCIDENTS, RESOURCES):
    - DO NOT generate new recommendations
    - Request data refresh from source agent
    - Log stale read to audit trail

UNREALISTIC failure mode:
  If PostgreSQL sync worker is down AND Redis has full TTL remaining,
  data appears fresh but has not been persisted.
  → Periodic sync health check: if no PostgreSQL write in 30s, EOC alert.
```

### 14.3 Conflicting Recommendations

```
SCENARIO: Two agents independently generate contradictory TASKS
  e.g., Shelter Agent: "Route vehicles to shelter_03"
        Logistics Agent: "Route vehicles to shelter_07" (different priority)

DETECTION:
  Conflict Resolution Agent runs AFTER both Shelter and Logistics nodes
  (guaranteed by LangGraph graph ordering)
  Detects: same resource allocated to multiple TASKS in same tick

RESOLUTION:
  Apply Section 7 scoring model.
  Generate single canonical DECISIONS record.
  Supersede losing TASK.
  Publish ConflictDetected → Approval workflow.

PREVENTION:
  Agents must NOT write TASKS that allocate resources they do not own.
  Resource allocation authority: ONLY Conflict Resolution Agent may create
  resource-allocation TASKS. All other agents create "request" TASKS.
  This prevents contradictory direct allocations.
```

### 14.4 Missing Approvals

```
SCENARIO: Approval deadline passes with no stakeholder action

RESPONSE (from Approval State Machine, Section 8.1):
  L1 timeout → Escalate to L2 (EOC)
  L2 timeout → Escalate to L3 (EOC Director)
  L3 timeout → EXPIRED status

EXPIRED action:
  - Decision is NOT executed
  - TASKS remain in PENDING
  - EOC receives hard alert
  - Audit log records: reason=APPROVAL_EXPIRED
  - If TASK has hard deadline (e.g., resource delivery needed within 2hrs):
    → Automatic ReplanTriggered: plan without that resource

CRITICAL NOTE:
  The system MUST NEVER auto-execute a rejected or expired decision.
  Human approval is a hard constraint, not a soft preference.
  This is the core research commitment of MIRAGE.
```

---

## 15. Deployment Architecture

### 15.1 Local Development

```yaml
# docker-compose.yml (development)
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: mirage
      POSTGRES_PASSWORD: mirage_dev
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    command: redis-server --notify-keyspace-events Ex
    ports: ["6379:6379"]

  api:
    build: ./backend
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql://postgres:mirage_dev@postgres:5432/mirage
      REDIS_URL: redis://redis:6379
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    ports: ["8000:8000"]
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    command: npm run dev
    ports: ["3000:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000

  simulation:
    build: ./simulation
    command: python engine.py --scenario scenario_A --speed 10
    environment:
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://postgres:mirage_dev@postgres:5432/mirage
    depends_on: [redis, postgres]
```

### 15.2 Production Deployment

```yaml
# docker-compose.prod.yml
services:
  # Same services, with:
  # - api: gunicorn with 4 uvicorn workers
  # - nginx: reverse proxy for api + frontend
  # - redis: persistence (appendonly yes)
  # - postgres: volume-backed, with pg_dump cron backup
  # - No hot-reload, production builds only

  nginx:
    image: nginx:alpine
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]
    ports: ["80:80"]
    depends_on: [api, frontend]
```

> [!WARNING]
> **Deployment realism flag**: For a final year project evaluated in a lab, "production" means: runs reliably on a single server/laptop for the duration of the evaluation experiments. Do NOT attempt Kubernetes, cloud deployment, or replica sets. They add zero research value and consume weeks of devops time. Keep all deployment as Docker Compose on a single machine.

### 15.3 Observability

| Signal | Tool | What it monitors |
|---|---|---|
| Structured logs | Python `logging` → JSON format | All agent decisions, events, errors |
| API request logs | FastAPI middleware | All API requests with latency |
| Agent heartbeat | Redis TTL monitoring | Agent health |
| Simulation metrics | Custom `/metrics` endpoint | Tick rate, event counts, queue depths |
| Dashboard | MIRAGE EOC UI (existing) | Operational state, approval queue |
| Experiment recorder | Custom logger | All M1–M8 metric values per tick, written to CSV for analysis |

> [!NOTE]
> **Evaluation observability is non-optional**: The experiment recorder that captures metric values per tick MUST be built. If you reach evaluation without automated metric collection, you will spend days manually computing metrics from logs. Build the recorder in Week 1 of implementation.
