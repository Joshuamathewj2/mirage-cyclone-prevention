# MIRAGE — Technical Architecture Document (TAD)
**Version:** 1.0  
**Date:** 2026-06-01  
**Scope:** Cyclone disaster coordination only  
**Status:** Research-grade final year project

---

> [!CAUTION]
> This document is brutally critical by design. Weaknesses, over-engineering flags, and under-specification warnings are embedded inline throughout every section.

---

## Table of Contents

1. System Context Diagram
2. High-Level Architecture Diagram
3. Internal Agent Architecture
4. Blackboard Architecture
5. Event-Driven Architecture
6. LangGraph Design
7. Conflict Resolution Engine
8. Approval Workflow Engine *(Part 2)*
9. Dynamic Replanning Engine *(Part 2)*
10. PostgreSQL + PostGIS Schema *(Part 2)*
11. Redis Usage Model *(Part 2)*
12. Simulation Engine Architecture *(Part 2)*
13. Evaluation Framework *(Part 2)*
14. Failure Scenarios *(Part 2)*
15. Deployment Architecture *(Part 2)*

---

## 1. System Context Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL ACTORS                               │
│                                                                      │
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Cyclone Forecast│   │  IMD / NOAA Feed │   │ Simulation       │  │
│  │ Data Source     │   │  (mocked in v1)  │   │ Engine (internal)│  │
│  └────────┬────────┘   └────────┬─────────┘   └────────┬─────────┘  │
│           │                     │                        │            │
└───────────┼─────────────────────┼────────────────────────┼───────────┘
            │                     │                        │
            ▼                     ▼                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         MIRAGE SYSTEM BOUNDARY                        │
│                                                                       │
│   ┌──────────────┐    ┌────────────────┐    ┌─────────────────────┐  │
│   │ EOC Dashboard│    │ Agent Execution│    │  Blackboard (Redis  │  │
│   │ (React/Next) │◄──►│ Engine         │◄──►│  + PostgreSQL)      │  │
│   └──────┬───────┘    │ (LangGraph)    │    └─────────────────────┘  │
│          │            └────────────────┘                              │
│          │                                                            │
│   ┌──────▼───────┐    ┌────────────────┐    ┌─────────────────────┐  │
│   │ Stakeholder  │    │ Approval Engine│    │  Audit Log Store    │  │
│   │ Portals      │◄──►│ (State Machine)│    │  (PostgreSQL)       │  │
│   └──────────────┘    └────────────────┘    └─────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
            │                     │                        │
            ▼                     ▼                        ▼
┌────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ Emergency      │   │ Shelter Manager      │   │ Logistics Officer / │
│ Operations     │   │ (web portal)         │   │ Medical Coordinator │
│ Center (EOC)   │   │                      │   │ (web portals)       │
└────────────────┘   └──────────────────────┘   └─────────────────────┘
```

> [!WARNING]
> **Weakness**: The SRS lists IMD/NOAA as inputs but provides no integration contract. In v1, all external feeds MUST be mocked. Do not attempt live API integration — it introduces unavoidable network failure modes outside evaluation control.

---

## 2. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         MIRAGE HIGH-LEVEL ARCHITECTURE                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                      FRONTEND LAYER                                 │ │
│  │   React / Next.js Dashboard    │    Role-based Stakeholder Portals  │ │
│  │   WebSocket real-time updates  │    Approval UI                     │ │
│  └────────────────────────────────┬────────────────────────────────────┘ │
│                                   │ REST + WebSocket                      │
│  ┌────────────────────────────────▼────────────────────────────────────┐ │
│  │                       API GATEWAY LAYER (FastAPI)                   │ │
│  │   /agents/*   /approvals/*   /blackboard/*   /audit/*   /sim/*     │ │
│  └─────────┬─────────────────────┬──────────────────────┬─────────────┘ │
│            │                     │                       │               │
│  ┌─────────▼──────────┐ ┌────────▼────────┐ ┌──────────▼─────────────┐  │
│  │  AGENT EXECUTION   │ │ APPROVAL ENGINE  │ │  SIMULATION ENGINE     │  │
│  │  LAYER (LangGraph) │ │  (State Machine) │ │  (Cyclone/Shelter/     │  │
│  │                    │ │                  │ │   Resource/Infra)      │  │
│  │  6 Agents          │ │  Escalation      │ │                        │  │
│  │  Orchestrator      │ │  Audit Logging   │ │                        │  │
│  └─────────┬──────────┘ └────────┬─────────┘ └──────────┬─────────────┘  │
│            │                     │                       │               │
│  ┌─────────▼─────────────────────▼───────────────────────▼─────────────┐ │
│  │                      DATA LAYER                                      │ │
│  │   Redis Blackboard (operational state, pub/sub events)               │ │
│  │   PostgreSQL + PostGIS (persistent records, audit, spatial data)     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Over-engineering flag**: A full API gateway layer with FastAPI is appropriate, but if the team also wants a separate message broker (Kafka/RabbitMQ) on top of Redis pub/sub, that is scope creep. Redis pub/sub is sufficient for the simulation scale in v1. Do NOT add a dedicated message broker.

---

## 3. Internal Agent Architecture

Each agent follows this standard internal structure:

```
┌─────────────────────────────────────────────────────┐
│                  AGENT INTERNAL STRUCTURE            │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  1. PERCEPTION MODULE                         │  │
│  │     - Reads assigned Blackboard regions       │  │
│  │     - Subscribes to relevant Redis channels   │  │
│  └───────────────────┬───────────────────────────┘  │
│                      │                              │
│  ┌───────────────────▼───────────────────────────┐  │
│  │  2. REASONING MODULE                          │  │
│  │     - Applies domain logic / LLM prompt       │  │
│  │     - Produces scored recommendation          │  │
│  │     - Generates explanation (XAI output)      │  │
│  └───────────────────┬───────────────────────────┘  │
│                      │                              │
│  ┌───────────────────▼───────────────────────────┐  │
│  │  3. ACTION MODULE                             │  │
│  │     - Writes output to Blackboard             │  │
│  │     - Publishes domain event                  │  │
│  │     - Requests approval if needed             │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 3.1 Agent-by-Agent Specification

| Agent | Reads From | Writes To | Triggers | Approval Required |
|---|---|---|---|---|
| Risk Assessment | INCIDENTS, external forecast | INCIDENTS.risk_score, INCIDENTS.priority_zones | CycloneUpdated | No |
| Shelter | SHELTERS, INCIDENTS.priority_zones | SHELTERS.overflow_prediction, TASKS | ShelterFull, ShelterOverflowPredicted | No |
| Resource | RESOURCES, SHELTERS.demand | RESOURCES.shortage_forecast, TASKS | ResourceShortageDetected | No |
| Logistics | ROUTES, RESOURCES.allocation, TASKS | ROUTES.delivery_plan, TASKS.updated | RouteBlocked | No |
| Conflict Resolution | TASKS (competing), RESOURCES | DECISIONS.resolution, TASKS.priority | ConflictDetected | No — outputs go to Approval |
| Approval | DECISIONS, APPROVALS | APPROVALS.status, audit_log | ApprovalRequested | Is the approval authority |

> [!WARNING]
> **Under-specification**: The SRS says agents have LLM reasoning but never specifies which model, how prompts are structured, or what fallback logic exists when the LLM call fails or returns malformed JSON. This MUST be resolved before implementation. Recommendation: use Gemini Flash 2.0 with structured output (Pydantic models) and a deterministic fallback for all six agents.

> [!NOTE]
> **Design decision**: Agents are NOT fully autonomous. Every agent that creates a task which affects another stakeholder's domain MUST run through the Approval Agent. This is the explainability-approval boundary.

---

## 4. Blackboard Architecture

### 4.1 Data Regions

```
┌──────────────────────────────────────────────────────────────────────┐
│                        BLACKBOARD STRUCTURE                          │
│                         (Redis Hash + PostgreSQL persistence)        │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │   INCIDENTS     │  │    SHELTERS      │  │     RESOURCES       │  │
│  │                 │  │                  │  │                     │  │
│  │ cyclone_id      │  │ shelter_id       │  │ resource_id         │  │
│  │ category        │  │ capacity         │  │ type                │  │
│  │ position (geo)  │  │ current_occupancy│  │ quantity            │  │
│  │ wind_speed      │  │ food_days        │  │ location (geo)      │  │
│  │ storm_surge     │  │ water_days       │  │ consumption_rate    │  │
│  │ predicted_path  │  │ overflow_risk    │  │ shortage_predicted  │  │
│  │ risk_score      │  │ status           │  │ reorder_threshold   │  │
│  │ priority_zones  │  │                  │  │                     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │     ROUTES      │  │     TASKS        │  │     DECISIONS       │  │
│  │                 │  │                  │  │                     │  │
│  │ route_id        │  │ task_id          │  │ decision_id         │  │
│  │ origin (geo)    │  │ type             │  │ recommendation      │  │
│  │ destination(geo)│  │ assigned_agent   │  │ reasoning           │  │
│  │ distance_km     │  │ priority         │  │ evidence            │  │
│  │ status          │  │ status           │  │ confidence_score    │  │
│  │ blockage_reason │  │ created_at       │  │ created_by_agent    │  │
│  │ alt_route_id    │  │ deadline         │  │ created_at          │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                       APPROVALS                                 │ │
│  │                                                                 │ │
│  │ approval_id | decision_id | requested_by | assigned_to         │ │
│  │ status (PENDING/APPROVED/REJECTED/ESCALATED/EXPIRED)           │ │
│  │ approver_id | approved_at | rejection_reason | escalation_count│ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Read/Write Permissions

| Region | Risk Agent | Shelter Agent | Resource Agent | Logistics Agent | Conflict Agent | Approval Agent | EOC |
|---|---|---|---|---|---|---|---|
| INCIDENTS | R/W | R | R | R | R | R | R |
| SHELTERS | R | R/W | R | R | R | R | R |
| RESOURCES | R | R | R/W | R | R/W | R | R |
| ROUTES | R | R | R | R/W | R | R | R |
| TASKS | W | W | W | R/W | R/W | R | R |
| DECISIONS | R | R | R | R | R/W | R/W | R |
| APPROVALS | — | — | — | — | — | R/W | R/W |

> [!CAUTION]
> **Critical weakness**: The SRS describes the Blackboard with zero concurrency control. Multiple agents running concurrently WILL produce write conflicts on shared regions (e.g., RESOURCES during a conflict resolution cycle). You MUST implement optimistic locking via Redis `WATCH`/`MULTI`/`EXEC` on all write operations. Failure to do this makes the system non-deterministic and unreproducible in experiments.

### 4.3 Synchronization Strategy

```
Write Protocol (all agents):
  1. Agent reads current value: GET blackboard:{region}:{id}
  2. Agent issues: WATCH blackboard:{region}:{id}
  3. Agent computes new value
  4. Agent issues MULTI block:
       SET blackboard:{region}:{id} {new_value}
       LPUSH event_log {event_json}
     EXEC
  5. If EXEC returns nil (concurrent modification detected):
       Agent retries with exponential backoff (max 3 retries)
       If still failing: publishes AGENT_WRITE_CONFLICT event
                         and halts its cycle for this tick

Persistence Sync:
  - Redis is the live operational store (TTL = simulation duration + 1hr)
  - PostgreSQL is the persistent audit store
  - A background sync worker flushes Redis writes to PostgreSQL every 5s
  - On system restart, Redis is re-seeded from PostgreSQL snapshot
```

---

## 5. Event-Driven Architecture

### 5.1 Event Definitions

| Event Name | Producer | Consumers | Payload Fields |
|---|---|---|---|
| `CycloneUpdated` | Simulation Engine | Risk Agent | cyclone_id, category, wind_speed, position, timestamp |
| `RiskLevelChanged` | Risk Agent | Shelter Agent, Resource Agent, Logistics Agent | cyclone_id, new_risk_score, priority_zones, delta |
| `ShelterOverflowPredicted` | Shelter Agent | Resource Agent, Conflict Agent | shelter_id, predicted_overflow_at, current_occupancy, capacity |
| `ShelterFull` | Shelter Agent | EOC, Conflict Agent | shelter_id, timestamp |
| `ResourceShortageDetected` | Resource Agent | Conflict Agent, Logistics Agent | resource_type, location_id, quantity_remaining, days_remaining |
| `RouteBlocked` | Simulation Engine | Logistics Agent | route_id, blockage_reason, blockage_geometry, timestamp |
| `ResourceRequestCreated` | Shelter Agent, Medical Coordinator | Resource Agent, Conflict Agent | request_id, requester_id, resource_type, quantity, priority |
| `ConflictDetected` | Conflict Agent | Approval Agent, EOC | conflict_id, competing_request_ids, resolution_recommendation |
| `ApprovalRequested` | Approval Agent | Assigned Stakeholder | approval_id, decision_id, deadline, assigned_to_role |
| `ApprovalGranted` | Approval Agent | Logistics Agent, Resource Agent, EOC | approval_id, decision_id, approver_id |
| `ApprovalRejected` | Approval Agent | Originating Agent, EOC | approval_id, decision_id, rejection_reason |
| `ApprovalEscalated` | Approval Agent | EOC | approval_id, escalation_level, reason |
| `ReplanTriggered` | Conflict Agent, Logistics Agent | All Agents | trigger_event_id, trigger_reason, affected_task_ids |
| `AgentCrashed` | Health Monitor | EOC, Orchestrator | agent_id, crash_time, last_known_state |

### 5.2 Event Lifecycle

```
                    ┌──────────┐
                    │ PRODUCED │
                    └────┬─────┘
                         │ Push to Redis channel
                         ▼
                    ┌──────────┐
                    │ QUEUED   │ (Redis LIST: events:{channel})
                    └────┬─────┘
                         │ Subscriber pulls
                         ▼
                    ┌──────────┐
                    │ CONSUMED │ Agent processes event
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       ┌──────────┐          ┌──────────────┐
       │ HANDLED  │          │ DEAD_LETTERED│
       │ (success)│          │ (3 failures) │
       └──────────┘          └──────┬───────┘
                                    │
                                    ▼
                             ┌──────────────┐
                             │ EOC ALERT    │
                             │ + audit log  │
                             └──────────────┘
```

### 5.3 Event Routing

```
Redis Pub/Sub Channel Map:
  ch:cyclone          → Risk Agent
  ch:risk             → Shelter Agent, Resource Agent, Logistics Agent
  ch:shelter          → Resource Agent, Conflict Agent, EOC
  ch:resource         → Conflict Agent, Logistics Agent
  ch:routes           → Logistics Agent
  ch:requests         → Conflict Agent
  ch:conflicts        → Approval Agent, EOC
  ch:approvals        → All Agents (filtered by decision_id), EOC
  ch:replan           → All Agents
  ch:system           → Orchestrator, EOC (health + agent crash events)
```

> [!WARNING]
> **Under-specification**: Redis pub/sub has no persistence. If a subscriber is offline when an event fires, it WILL miss the event permanently. You MUST use Redis Streams (`XADD`/`XREAD` with consumer groups) instead of plain pub/sub. This gives you message persistence, consumer group acknowledgement, and dead-letter semantics. Changing this now costs ~2 days; changing it after coding costs 2 weeks.

---

## 6. LangGraph Design

### 6.1 Graph Structure

```
[START]
   │
   ▼
┌─────────────────────┐
│  simulation_tick     │ ← fires every N seconds (configurable)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  risk_assessment     │ reads INCIDENTS, writes risk_score
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     │             │
     ▼             ▼
┌─────────┐  ┌──────────┐
│ shelter  │  │ resource │  ← run in parallel (both read risk output)
│ _assess  │  │ _assess  │
└────┬─────┘  └────┬─────┘
     │              │
     └──────┬───────┘
            │
            ▼
┌─────────────────────┐
│  logistics_plan     │ reads shelter + resource outputs
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  conflict_detect    │ reads all TASKS, detects collisions
└──────────┬──────────┘
           │
     ┌─────┴──────────────┐
     │                     │
     ▼                     ▼
 [conflict=NO]       [conflict=YES]
     │                     │
     ▼                     ▼
┌─────────────────┐  ┌──────────────────┐
│ approval_route  │  │ conflict_resolve  │
│ (low-risk auto) │  │ (scored decision) │
└────────┬────────┘  └────────┬──────────┘
         │                    │
         └──────────┬─────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  approval_gate   │  ← waits for human approval
         └──────────┬───────┘
                    │
            ┌───────┴────────┐
            │                 │
            ▼                 ▼
       [APPROVED]         [REJECTED]
            │                 │
            ▼                 ▼
   ┌──────────────┐   ┌───────────────┐
   │ execute_plan │   │ replan_trigger│
   └──────┬───────┘   └───────┬───────┘
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  audit_write     │  ← always runs, writes to PostgreSQL
          └──────────────────┘
                    │
                    ▼
                [END / next tick]
```

### 6.2 Nodes

| Node | Type | State Read | State Written | LLM Call? |
|---|---|---|---|---|
| `simulation_tick` | Trigger | — | INCIDENTS, sim clock | No |
| `risk_assessment` | Agent | INCIDENTS | INCIDENTS.risk_score, priority_zones | Yes (risk scoring prompt) |
| `shelter_assess` | Agent | SHELTERS, INCIDENTS | SHELTERS.overflow_prediction | Yes |
| `resource_assess` | Agent | RESOURCES, SHELTERS | RESOURCES.shortage_forecast | Yes |
| `logistics_plan` | Agent | ROUTES, TASKS, RESOURCES | TASKS.delivery_plan | Yes |
| `conflict_detect` | Decision | TASKS | conflict_flag, conflict_id | No (rule-based) |
| `conflict_resolve` | Agent | TASKS, RESOURCES | DECISIONS.resolution | Yes (arbitration prompt) |
| `approval_route` | Router | DECISIONS | APPROVALS | No |
| `approval_gate` | Wait | APPROVALS | APPROVALS.status | No |
| `execute_plan` | Action | APPROVALS, TASKS | TASKS.status=EXECUTING | No |
| `replan_trigger` | Action | rejected decision | ReplanTriggered event | No |
| `audit_write` | Sink | Full graph state | PostgreSQL audit_log | No |

### 6.3 State Schema (LangGraph TypedDict)

```python
from typing import TypedDict, List, Optional
from datetime import datetime

class MirageGraphState(TypedDict):
    # Simulation context
    simulation_id: str
    tick_number: int
    tick_timestamp: datetime

    # Cyclone context
    cyclone_id: str
    cyclone_category: int
    cyclone_position: dict          # {lat, lon}
    cyclone_risk_score: float       # 0.0 – 1.0
    priority_zones: List[str]       # zone_ids

    # Shelter context
    shelter_statuses: List[dict]    # [{shelter_id, overflow_risk, ...}]

    # Resource context
    resource_shortages: List[dict]  # [{type, location, days_remaining}]

    # Task context
    active_tasks: List[dict]

    # Conflict context
    conflict_detected: bool
    conflict_id: Optional[str]
    conflict_resolution: Optional[dict]

    # Approval context
    pending_approval_id: Optional[str]
    approval_status: Optional[str]  # PENDING/APPROVED/REJECTED/ESCALATED

    # Execution
    executed_plan: Optional[dict]

    # Replan
    replan_required: bool
    replan_reason: Optional[str]

    # Audit
    audit_entries: List[dict]
```

### 6.4 Checkpoints

| Checkpoint | Trigger | Persistence Target | Purpose |
|---|---|---|---|
| `post_risk_assessment` | After risk node | Redis + PostgreSQL | Allow replay if downstream nodes fail |
| `post_conflict_detect` | After conflict detection | Redis | Gate for conflict branch |
| `pre_approval_gate` | Before human wait | PostgreSQL | Durable — survives system restart |
| `post_approval` | After approval decision | PostgreSQL | Legal audit anchor |
| `post_execution` | After execute_plan | PostgreSQL | Execution record |

> [!WARNING]
> **Critical design gap**: The current design has no timeout on `approval_gate`. If a stakeholder never responds, the graph hangs indefinitely. You MUST add a configurable approval deadline (default: 30 minutes in simulation, 4 hours in real deployment) with automatic escalation as a graph-level timeout interrupt.

---

## 7. Conflict Resolution Engine

### 7.1 Conflict Detection Algorithm

A conflict exists when two or more TASKS compete for the same resource where the combined requested quantity exceeds available stock.

```python
def detect_conflicts(tasks: List[Task], resources: Dict[str, Resource]) -> List[Conflict]:
    conflicts = []
    by_resource = group_tasks_by_resource(tasks)
    for resource_id, competing_tasks in by_resource.items():
        total_requested = sum(t.quantity for t in competing_tasks)
        available = resources[resource_id].quantity
        if total_requested > available:
            conflicts.append(Conflict(
                resource_id=resource_id,
                competing_tasks=competing_tasks,
                deficit=total_requested - available
            ))
    return conflicts
```

### 7.2 Priority Scoring Model

Each competing request is scored on five weighted dimensions:

| Dimension | Weight | Scoring Rule |
|---|---|---|
| Life Safety Risk | 0.40 | 1.0 = immediate life threat; 0.5 = moderate; 0.0 = logistical only |
| Cyclone Risk Zone | 0.25 | Normalized risk_score of the requesting location (from Risk Agent) |
| Population Density | 0.15 | Affected population / max population in simulation |
| Resource Criticality | 0.10 | Water > Food > Medical > Fuel > Blankets (ordinal scale 1.0→0.2) |
| Time Urgency | 0.10 | 1.0 if needed within 2hrs; 0.5 within 6hrs; 0.0 otherwise |

```
Priority Score = Σ (dimension_value × weight)
Range: 0.0 – 1.0
```

**Allocation Algorithm:**  
Requests are ranked by Priority Score descending. Resources are allocated greedily from highest to lowest score until stock is exhausted. Remaining unfulfilled requests are queued for partial fulfillment or escalation.

### 7.3 Decision Process

```
┌─────────────────────────────────────────────────────────────────┐
│               CONFLICT RESOLUTION DECISION FLOW                 │
│                                                                 │
│  1. DETECT: Identify competing tasks for same resource          │
│     └─→ Output: Conflict object                                 │
│                                                                 │
│  2. SCORE: Apply priority scoring model to each request         │
│     └─→ Output: Ranked list with scores                         │
│                                                                 │
│  3. ALLOCATE: Greedy allocation by rank until stock exhausted   │
│     └─→ Output: Allocation plan (who gets what, who gets zero)  │
│                                                                 │
│  4. EXPLAIN: Generate natural-language explanation per decision  │
│     └─→ Output: explanation string per request outcome          │
│                                                                 │
│  5. ROUTE: Write DECISIONS record, publish ConflictDetected     │
│     └─→ Triggers Approval workflow for EOC review               │
│                                                                 │
│  6. AUDIT: Write conflict + resolution to audit_log             │
└─────────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Weakness — Tie-breaking**: The scoring model provides no explicit tie-breaking rule. Two requests with identical scores will produce non-deterministic allocation depending on Python dict ordering. Add tie-breaker: earliest request creation timestamp wins. Document this in the evaluation section so reviewers understand determinism guarantees.

> [!NOTE]
> **Research contribution note**: The combination of the 5-dimension weighted scoring model + LLM-generated natural language explanation per outcome is the explainability contribution of this system. The LLM does NOT make the allocation decision — it only explains the deterministic algorithmic result. This distinction is critical for academic defensibility.
