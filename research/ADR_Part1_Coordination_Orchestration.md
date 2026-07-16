# MIRAGE — Architecture Decision Record Pack (ADR Pack)
**Version:** 1.0  
**Date:** 2026-06-02  
**Decision Owner:** MIRAGE Architecture Team  
**Project:** Multi-Agent Intelligent Response and Governance Engine

---

## ADR-001 — Blackboard Architecture

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context

MIRAGE fields six autonomous agents that must share operational state without direct coupling. Agents produce outputs that other agents depend on (e.g., the Risk Assessment Agent produces zone risk scores consumed by the Shelter Agent). A coordination mechanism is required that: (a) decouples producers from consumers, (b) provides a single source of truth for operational state, and (c) supports concurrent reads with controlled writes.

---

### Problem

How should six agents with overlapping data dependencies share state without creating brittle point-to-point communication contracts that break when any agent fails or changes?

---

### Alternatives Considered

| Alternative | Description | Why Rejected |
|---|---|---|
| **Direct agent-to-agent messaging** | Each agent sends messages directly to dependent agents via queues | Creates O(n²) communication contracts. Agent crash requires all senders to handle missing recipient. Adding a 7th agent requires updating all existing agents. Structurally fragile for research prototype. |
| **Event sourcing only** | All state changes published as events; agents reconstruct state by replaying event stream | Correct for audit, but expensive for operational reads. An agent needing current shelter occupancy must replay an entire event stream per tick. Unsuitable for ≤5s decision latency requirement. |
| **Shared relational database only** | PostgreSQL as the sole shared store; agents read/write via SQL | Correct for persistence but adds 20–50ms per query round-trip through connection pool. Tick-level coordination across 6 agents generates excessive DB load. No pub/sub mechanism for reactive agent triggering. |
| **Blackboard + Redis + PostgreSQL** | Redis as live operational Blackboard (fast reads/writes); PostgreSQL as persistent audit store | **Selected.** |

---

### Decision

Use the Blackboard architectural pattern implemented as:
- **Redis** for the live Blackboard (operational state, sub-millisecond reads)
- **PostgreSQL** as persistent backing store (audit trail, recovery seed)
- **Seven named data regions:** INCIDENTS, SHELTERS, RESOURCES, ROUTES, TASKS, DECISIONS, APPROVALS

---

### Rationale

The Blackboard pattern was designed precisely for multi-agent systems where agents have asymmetric knowledge and contribute partial solutions to a shared problem. MIRAGE's operational coordination problem is structurally identical to the canonical Blackboard use case: multiple specialists (agents) independently contribute partial solutions (risk scores, overflow predictions, delivery plans) toward a composite operational picture.

Redis satisfies the performance requirement: reads are O(1), writes are O(1), and pub/sub (or Streams) notification is native. The 5-second decision latency NFR is achievable only if agents can read shared state in <1ms.

---

### Pros

- Full decoupling: agents depend on data regions, not other agents
- Single source of truth: no competing state copies
- Fault tolerance: agent crash does not corrupt shared state
- Redis TTL supports natural state lifecycle management
- Sim-time audit via background PostgreSQL sync

---

### Cons

- Redis is an in-memory store: state is lost if Redis crashes without persistence
- Concurrent write conflicts require explicit locking (WATCH/MULTI/EXEC)
- Seven region semantics must be documented and enforced — no schema enforcement at Redis level
- Background sync worker is a single point of failure for persistence

---

### Consequences

- All agents MUST use optimistic locking (Redis `WATCH`/`MULTI`/`EXEC`) for all writes
- Redis `appendonly yes` MUST be enabled in production to prevent data loss on restart
- The sync worker MUST have a health check; failure triggers an EOC alert (TAD Section 15.3)
- Agent developers MUST NOT write outside their authorized regions (TAD Section 4.2 ACL table enforced by convention, not by Redis ACL in v1)

---

### Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Redis OOM (out of memory) on long simulations | Low | High | Set maxmemory + allkeys-lru eviction; key TTL on all regions |
| Sync worker falls behind Redis writes | Medium | Medium | Monitor lag; alert if >30s behind |
| Write conflicts under concurrent agent execution | High | Medium | Retry with backoff (max 3); publish AGENT_WRITE_CONFLICT on failure |

---

### Future Reconsideration Conditions

- If agent count exceeds 10: evaluate Apache Ignite or Hazelcast for distributed Blackboard
- If simulation scale exceeds 10,000 shelters: evaluate Redis Cluster
- If legal auditability requires stronger guarantees: evaluate event-sourced audit backbone (Kafka + KSQL)

---
---

## ADR-002 — LangGraph Orchestration

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context

MIRAGE requires an orchestration layer that: (a) sequences six agents in a defined dependency order, (b) supports conditional branching (conflict detected / not detected), (c) supports a blocking wait state (approval gate), (d) persists checkpoints for fault recovery, and (e) allows partial graph re-execution for replanning without full restart.

---

### Problem

Which orchestration framework should manage the multi-agent execution graph with conditional branching, human-in-the-loop wait states, checkpointing, and partial re-execution?

---

### Alternatives Considered

| Alternative | Fit | Rejection Reason |
|---|---|---|
| **CrewAI** | Role-based multi-agent framework | Designed for collaborative task completion, not for structured operational workflows with formal approval gates. No native support for persistent checkpoints or blocking human-in-the-loop states at the graph level. |
| **AutoGen** | Conversational multi-agent | Built for LLM-to-LLM dialogue. No structured graph; no deterministic branching; no approval gate primitive. Conversations are non-deterministic by design — incompatible with MIRAGE's reproducibility requirement. |
| **Custom state machine** | Hand-coded FSM in Python | Fully controllable but requires implementing graph traversal, checkpointing, parallelism, and conditional branching from scratch. Estimated 3–4 weeks of infrastructure work with no research value. Maintenance burden is high. |
| **BPMN workflow engine (Camunda, Activiti)** | Process orchestration | Industry-grade but Java-native. Python LLM integration requires REST bridging. BPMN is designed for stateless business processes, not stateful multi-agent AI loops. Overly heavyweight for research prototype. |
| **LangGraph** | Graph-based LLM agent orchestration | **Selected.** |

---

### Deep Comparison Table

| Criterion | LangGraph | CrewAI | AutoGen | Custom FSM | BPMN Engine |
|---|---|---|---|---|---|
| Conditional branching | Native | Limited | No | Manual | Native |
| Parallel node execution | Native | Limited | No | Manual | Native |
| Human-in-the-loop wait | Native interrupt | No | No | Manual | Native |
| Checkpointing | Native (MemorySaver / SQLiteSaver) | No | No | Manual | Vendor-specific |
| Partial re-execution | Native (replay from checkpoint) | No | No | Manual | Limited |
| Python-native | Yes | Yes | Yes | Yes | No (Java) |
| LLM integration | Native | Native | Native | Manual | Manual |
| Deterministic branching | Yes | No | No | Yes | Yes |
| Production maturity (2026) | Medium | Low | Medium | N/A | High |
| Research prototype suitability | High | Medium | Low | Low | Low |

---

### Decision

Use **LangGraph** as the agent execution orchestration layer. The MIRAGE execution graph (TAD Section 6) is implemented as a LangGraph `StateGraph` with `TypedDict` state, named nodes for each agent, conditional edges for branching, and `interrupt_before` for the approval gate.

---

### Rationale

LangGraph is the only framework among the alternatives that provides: native graph-level checkpointing, native human-in-the-loop interrupt semantics, and partial graph re-execution from checkpoint. These three capabilities are non-negotiable for MIRAGE's approval workflow and dynamic replanning engine.

CrewAI and AutoGen are excellent for autonomous agent collaboration but neither supports the hard governance requirement: a blocking, auditable human approval gate that survives system restart. Custom FSM implementation would provide the same capabilities but consume 3–4 weeks building infrastructure with zero research contribution.

---

### Pros

- Native checkpoint persistence: approval gate survives system restart
- `interrupt_before` semantics cleanly model the human approval wait state
- Parallel node execution (shelter + resource agents run concurrently per tick)
- Graph visualization tools aid debugging
- Active development and community (LangChain ecosystem)

---

### Cons

- Relatively new framework (2024): API surface may change between versions
- Checkpointing currently defaults to SQLite; requires custom PostgreSQL checkpointer for production
- Graph structure must be defined at initialization; dynamic graph modification is not supported (replanning uses partial re-entry, not graph mutation)
- Debugging multi-step async graphs is non-trivial without LangSmith

---

### Consequences

- Pin LangGraph to a specific version in `requirements.txt`; do NOT auto-upgrade during evaluation
- Implement PostgreSQL-backed checkpointer (LangGraph supports custom `BaseCheckpointSaver`)
- The approval gate MUST use `interrupt_before` with a configurable timeout interrupt — not a `while True` poll loop
- All LangGraph node functions MUST be idempotent (safe to re-run from checkpoint on recovery)

---

### Risks

| Risk | Mitigation |
|---|---|
| LangGraph API breaking change | Pin version; run full graph test after any dependency update |
| Checkpoint database corruption | Use PostgreSQL ACID transactions for checkpoint writes |
| Graph hangs on approval gate (no timeout) | Implement LangGraph `interrupt` with Redis TTL expiry signal (TAD Section 11) |

---

### Future Reconsideration Conditions

- If LangGraph is deprecated or significantly restructured before paper submission: migrate to custom Python FSM with cached checkpoint store (1-week migration)
- If agent count exceeds 12: evaluate distributed graph execution (LangGraph + Ray)

---
---

## ADR-003 — Deterministic Decisions + LLM Explanations

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context

MIRAGE uses LLMs (Gemini Flash) within agents for reasoning and recommendation generation. A fundamental architectural question arises: should LLMs make resource allocation decisions, or should they only explain decisions made by deterministic algorithms?

---

### Problem

LLMs are probabilistic, non-deterministic, and opaque. Emergency resource allocation decisions in disaster response are consequential, legally accountable, and must be reproducible for research evaluation. These requirements are in direct tension with LLM-native decision-making.

---

### Alternatives Considered

| Alternative | Description | Assessment |
|---|---|---|
| **Full LLM decision-making** | LLM receives situation context, produces allocation decision | Non-deterministic. Same input → different output across runs. Experiments are non-reproducible. Allocation rationale is post-hoc self-generated, not grounded in computable evidence. Legally indefensible. REJECTED. |
| **LLM-assisted scoring** | LLM contributes one or more scoring dimensions | LLM component introduces variance into the priority score. Two identical situations may produce different scores and different allocations. REJECTED. |
| **Deterministic algorithm only (no LLM)** | Weighted scoring model produces allocations; no explanation generated | Fully reproducible. But produces no human-readable rationale. Fails the explainability research objective. PARTIALLY REJECTED (LLM explanation layer added). |
| **Deterministic allocation + LLM explanation** | Algorithm decides; LLM explains the decision in natural language | **Selected.** |

---

### Decision

**Operational decisions (resource allocation, conflict resolution, replanning triggers) are computed by deterministic algorithms only.** LLMs are invoked exclusively post-decision to generate natural language explanations of the algorithmic result. The LLM output CANNOT alter the allocation outcome.

---

### Accountability Concerns

Emergency resource allocation decisions may result in loss of life if wrong. If an LLM allocates food to a low-priority shelter while a higher-priority shelter starves:

- The decision cannot be attributed to a specific rule or policy
- It cannot be reproduced or audited
- It cannot be overridden with confidence (the LLM may produce a different override justification next time)
- Legal accountability rests with the EOC; they cannot be responsible for an opaque LLM decision

The deterministic model ensures that every allocation decision can be traced to: input values → weight vector → formula → ranked output. This is auditable and challengeable.

---

### Reproducibility Concerns

Research validity requires that experiments produce the same results when re-run with the same inputs. LLM outputs at temperature > 0 are non-deterministic. Even at temperature = 0, model version updates can change outputs.

The deterministic allocation model produces identical outputs for identical inputs regardless of LLM version, temperature, or API availability. Experiments E1–E6 are reproducible.

---

### Auditability Concerns

The audit log (TAD Section 10, `approval_audit_log`) records:
- The decision recommendation (text)
- The decision reasoning (text — LLM generated)
- The evidence (structured JSON — algorithm generated)
- The priority score (float — algorithm generated)

The algorithm-generated evidence and score are the auditable record. The LLM-generated reasoning is a human-readable annotation on top of the structured evidence. Auditors can verify the score computation independently of the LLM output.

---

### Failure Scenarios

| Failure | Impact if LLM decides | Impact with deterministic model |
|---|---|---|
| LLM API timeout | Allocation fails; affected requesters get nothing | Allocation proceeds via algorithm; explanation marked "unavailable" in UI |
| LLM hallucinates incorrect resource quantities | Allocation is wrong; potential life safety impact | Allocation is algorithm-computed; LLM generates explanation only; hallucination affects text, not action |
| LLM model version update changes decision logic | All past decisions are now inconsistent with system behavior | Only explanation style changes; allocation logic is unchanged |
| LLM produces malformed JSON | Allocation fails if JSON is parsed for decision | Fallback: display raw text explanation; allocation unaffected |

---

### Why LLMs Cannot Allocate Resources

An LLM allocating emergency resources violates four requirements simultaneously:

1. **Determinism** — same situation must produce same allocation across experiment runs
2. **Auditability** — allocation must be computable from documented inputs and weights
3. **Accountability** — human approvers must be able to verify the allocation basis before approving
4. **Failure safety** — LLM unavailability must not halt life-safety operations

The deterministic scoring model satisfies all four. LLMs satisfy none.

---

### Consequences

- All Conflict Resolution Agent logic must be implemented without LLM calls in the allocation path
- LLM calls for explanation are always wrapped in try/except; failure → fallback to structured evidence display
- LLM temperature = 0 and model version pinned for all agent reasoning prompts
- Explanation text is stored separately from evidence JSON in the `decisions` table
- Reviewers/evaluators can verify any allocation by independently computing the scoring model

---

### Risks

| Risk | Mitigation |
|---|---|
| LLM explanation is misleading (hallucinated rationale) | Structured evidence JSON (algorithm output) always displayed alongside LLM text |
| Scoring model weights are wrong | Sensitivity analysis in evaluation; weight vector documented and peer-reviewed |
| Deterministic model cannot handle novel scenarios | Explicitly scoped to cyclone response; novel scenarios flagged as out-of-scope |

---

### Future Reconsideration Conditions

- If LLMs achieve formal verifiability (symbolic + neural hybrid): re-evaluate LLM-assisted scoring as one dimension with bounded variance
- If the project scope expands to multi-disaster: re-evaluate whether weighted model generalizes

---
---

## ADR-004 — Digital Twin Simulation Environment

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context

MIRAGE must be evaluated against baselines under controlled, reproducible conditions. The evaluation requires exposing agents to cyclone scenarios with known characteristics, injecting failures at predetermined points, and measuring agent responses. An evaluation environment must be selected.

---

### Problem

How should the evaluation environment be constructed to produce reproducible, controllable, and sufficiently realistic scenarios for publication-quality evaluation?

---

### Alternatives Considered

| Alternative | Description | Assessment |
|---|---|---|
| **Historical case replay** | Replay data from a real historical cyclone event | Real data is messy, incomplete, and unique. Cannot inject controlled failures at specific ticks. Cannot reproduce identical conditions for baseline comparison. Copyright and data access issues. REJECTED. |
| **Synthetic CSV datasets** | Pre-constructed static CSV files representing shelter/resource/route states per tick | No causal dynamics. Resource consumption does not respond to shelter occupancy. Cyclone progression does not affect shelter demand. Produces artificial evaluation. Reviewers will correctly identify this as inadequate. REJECTED. |
| **Static scenarios (fixed initial state)** | System initialized with a fixed state; no tick-based progression | Cannot evaluate dynamic replanning (triggers require state change over time). Cannot evaluate approval workflow timing (no time progression). REJECTED. |
| **Live data feeds (IMD/NOAA)** | Real-time cyclone data ingested from weather APIs | Out of scope for v1. Introduces external dependency and network failure modes. Non-reproducible (same API call on different days returns different data). REJECTED for v1. |
| **Parameterized Digital Twin simulation** | Five DTs (cyclone, population, shelter, resource, transport) updated each tick by simulation engine | **Selected.** |

---

### Decision

Use a **Parameterized Digital Twin simulation environment** as the evaluation platform. The simulation engine advances five Digital Twin models each tick, generating realistic causal state changes that agents respond to. Three pre-defined scenarios (A, B, C) are parameterized against documented cyclone characteristics.

---

### Why Digital Twin is Required

**Causality**: Real disaster scenarios exhibit causal chains. A cyclone intensifying (DT update) → increases evacuation rate (population DT) → increases shelter occupancy (shelter DT) → depletes food and water faster (resource DT) → triggers delivery tasks (transport DT). A static dataset cannot reproduce this causal chain. An agent that performs well on a static dataset may fail under dynamic conditions — making static evaluation misleading.

**Controllability**: The DT simulation engine allows precise injection of failures at specific ticks (route blockage at tick 12, shelter damage at tick 25) with known ground truth. This enables exact measurement of agent response time (M1, M5) and controlled ablation experiments (E3, E4).

**Reproducibility**: Parameterized scenarios with fixed random seeds produce identical state sequences across runs. The same scenario run against MIRAGE, B1, B2, B3, B4, B5 produces identical exogenous conditions. This is a necessary condition for valid comparative evaluation.

**Dynamic replanning validation**: H4 (replanning speed) can only be measured if the simulation produces unexpected events at known times. The DT simulation engine provides this via the infrastructure failure simulator.

---

### Pros

- Reproducible: same seed → same scenario → comparable baselines
- Controllable: failure injection at known ticks
- Causal: state changes are driven by model dynamics, not pre-scripted
- Three scenarios test different operational stresses
- No external data dependencies

---

### Cons

- Simulation may not fully capture real cyclone dynamics (acknowledged in paper limitations)
- Parameterization requires domain knowledge for realistic values
- Building the simulation engine is non-trivial implementation work (estimated 2 weeks)
- Reviewers will correctly note that simulation ≠ real deployment

---

### Consequences

- Simulation engine must be implemented and validated before any evaluation run (RB Phase 2)
- All scenario parameters must be frozen before evaluation begins (no mid-experiment tuning)
- Probabilistic failure injection (not only fixed-tick events) must be implemented (TAD Section 12.5)
- Simulation realism limitations must be explicitly stated in the paper's threat to validity section

---

### Risks

| Risk | Mitigation |
|---|---|
| Simulation produces unrealistic states | Validate DT outputs against documented cyclone case study parameters before experiments |
| Fixed-tick failures criticized as scripted | Implement probabilistic failures alongside scripted ones |
| Simulation engine bugs corrupt evaluation data | Unit-test each DT update function; validate against expected state at 5 known ticks |

---

### Future Reconsideration Conditions

- Post-submission: replace synthetic DT with real IMD cyclone track data for a replication study
- If field deployment is attempted: replace simulation with live sensor feeds and remove DT layer

---
---

## ADR-005 — Approval-Aware Governance Layer

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context

MIRAGE agents generate resource allocation recommendations that affect life-safety operations. The question is whether agents should execute plans autonomously after generation, require human approval before execution, or operate in some hybrid mode.

---

### Problem

At what level of authority should AI-generated recommendations in a life-safety system be executed without human review? What governance structure ensures that human operators remain accountable for operational outcomes?

---

### Alternatives Considered

| Alternative | Description | Assessment |
|---|---|---|
| **Fully autonomous execution** | Agent recommendations executed immediately without human review | Legally indefensible in emergency management. No human accountability. If an agent allocates resources incorrectly, no one is responsible. Trust calibration impossible without demonstrated track record. Directly contradicts the research framing of MIRAGE as a decision-support system. REJECTED. |
| **Manual-only coordination** | Agents generate recommendations; humans transcribe and execute manually outside system | Baseline B1. No governance benefit. Eliminates the approval workflow contribution. Appropriate as a baseline, not as a system design. REJECTED as system mode. |
| **Soft approvals (advisory)** | Recommendations displayed; humans can optionally approve but execution proceeds after timeout regardless | Creates an illusion of governance without accountability. A human who ignored an advisory approval bears uncertain responsibility. Audit trail is ambiguous. REJECTED. |
| **Hard approval gate (human-in-the-loop)** | No recommendation executes without explicit human approval OR approved auto-approval criteria | **Selected.** |

---

### Decision

**Every operational recommendation that creates a task affecting another stakeholder's domain or deploys a resource MUST pass through the Approval Workflow Engine before execution.** Auto-approval (L0) is permitted only for low-risk, low-quantity, non-conflicting decisions meeting criteria defined in Section 5.4 of the RB.

---

### Legal Considerations

In emergency management, authority and accountability are legally defined. Emergency Operations Centers hold statutory authority over resource deployment during declared disasters. An AI system that deploys resources without EOC authorization potentially:

1. Violates the statutory authority of the EOC
2. Creates ambiguous liability if the deployment causes harm
3. Undermines the legal chain of command

The hard approval gate ensures that every executed action can be traced to a specific human approver with a timestamped record. If an action causes harm, the audit log clearly shows who approved it and when. This is not merely a design preference — it is a legal and ethical requirement for any system used in operational emergency management.

---

### Trust Considerations

AI systems in high-stakes domains must earn operator trust through demonstrated reliability before autonomy can be extended. An approval-aware system allows operators to:

1. Observe agent recommendations before commitment
2. Override or reject individual decisions
3. Build confidence in agent behaviour over multiple operations
4. Escalate decisions outside their confidence threshold

A fully autonomous system eliminates this trust-building pathway. If an agent makes one significant error without human review, it may permanently damage operator trust in the entire system.

---

### Governance Considerations

The three-level escalation model (L1 → L2 → L3 → EXPIRED) ensures:

- Decisions are not silently dropped when approvers are unavailable
- Escalation is documented (every transition logged to `approval_audit_log`)
- The EOC always maintains oversight — if all levels timeout, the EOC receives a hard alert
- No decision can be executed without leaving an audit trail

---

### Research Validity Considerations

MIRAGE's research contribution includes the approval-aware coordination framework as a novel element. If approval is removed or made soft, the research contribution is diminished. The approval workflow is simultaneously a governance mechanism and a research contribution — it cannot be weakened without undermining the paper's novelty claim.

---

### Consequences

- The LangGraph `approval_gate` node MUST use `interrupt_before` semantics with timeout interrupt
- Auto-approve criteria (L0) must be explicitly frozen before evaluation; changes post-experiment invalidate results
- All approval state transitions MUST be written to `approval_audit_log` atomically with the state change
- Approval deadlines MUST scale with simulation speed multiplier α (RB Section 5.4)
- The EOC dashboard MUST display pending approvals with countdown timers

---

### Risks

| Risk | Mitigation |
|---|---|
| Approval queue builds up faster than humans can process during stress test | Expand auto-approve criteria for low-risk items; ensure Scenario B evaluation uses consistent approval throttle |
| Timeout miscalibrated with simulation speed multiplier | Parameterize T_L against α in config; add integration test |
| Escalation chain leads to EXPIRED for genuinely critical decisions | EOC hard alert on EXPIRED; decision remains available for manual execution outside system |

---

### Future Reconsideration Conditions

- If MIRAGE achieves demonstrated reliability over 100+ simulated operations: re-evaluate auto-approve threshold expansion
- If field deployment is attempted: legal review mandatory before any autonomy increase
