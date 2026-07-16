# MIRAGE — Architecture Decision Record Pack (ADR Pack) Part 2
**Version:** 1.0  
**Date:** 2026-06-02  
**Decision Owner:** MIRAGE Architecture Team

---

## ADR-006 — PostgreSQL + PostGIS

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context
MIRAGE maintains persistent records of cyclone tracks, shelter locations, delivery routes, and priority zones. These entities are inherently geospatial.

---

### Problem
The system needs to store and query spatial data to answer questions like: "Which shelters are within the predicted 10km storm surge zone?" or "Which delivery routes intersect with the current flooding hazard area?"

---

### Alternatives Considered

| Alternative | Description | Rejection Reason |
|---|---|---|
| **PostgreSQL only** | Store lat/lon as separate `FLOAT` columns with Haversine distance functions | Hard-coded distance math is error-prone. No support for polygon/LineString intersection queries. Performance scales poorly for complex path-intersect tests required by the Logistics Agent. |
| **MongoDB** | Document store with 2D sphere indexing | Good for simple proximity but lacks the ACID guarantees required for the immutable audit log. Joins across incidents/shelters/tasks are complex and slower than in a relational model. |
| **Neo4j** | Graph database for transportation network | Excellent for pathfinding, but redundant since Logistics Agent performs pathfinding in-memory or via external API. Spatial querying in Neo4j (Cypher) is less mature than PostGIS for complex geometry. |
| **PostgreSQL + PostGIS** | Relational DB with spatial extensions | **Selected.** |

---

### Decision
Use **PostgreSQL with the PostGIS extension**. All spatial data (cyclone eye, shelter centroids, route paths, priority zones) will be stored using the `GEOGRAPHY` type (EPSG:4326).

---

### Rationale
PostGIS is the industry standard for academic and operational geospatial informatics. It provides native operators (`ST_DWithin`, `ST_Intersects`, `ST_Buffer`) to compute relationships between cyclone paths and infrastructure—a core requirement for the Risk Assessment and Logistics agents. Using PostGIS ensures the system's spatial logic is mathematically defensible and interoperable with standard GIS visualization tools.

---

### Consequences
- Requires PostGIS installed in the database environment (handled via `postgis/postgis` Docker image).
- Developers must use PostGIS syntax for spatial queries.
- Higher storage overhead for GIST indexes compared to plain B-trees.
- Transitioning to real IMD/NOAA datasets becomes trivial as they natively use EPSG:4326.

---

### Risks
- **Over-engineering**: If the simulation remains small-scale (e.g., 20 shelters), plain coordinate math would suffice. However, research rigor favors the standardized approach.
- **Latency**: Spatial joins can be slow if not properly indexed. GIST indexes on all `GEOGRAPHY` columns are mandatory.

---

### Future Reconsideration Conditions
- If the project scales to a country-wide level (10,000+ routes), evaluate dedicated spatial routing engines like PgRouting or OSRM.

---
---

## ADR-007 — Redis Streams Event Bus

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context
Six agents communicate asynchronously via events. The TAD (Section 5) identifies 14 event types across various channels.

---

### Problem
If an agent is offline or restarting when an event is published, it might miss critical triggers (e.g., `CycloneUpdated`). The standard Redis Pub/Sub mechanism is "fire-and-forget" and provides no persistence or acknowledgement.

---

### Alternatives Considered

| Alternative | Description | Rejection Reason |
|---|---|---|
| **Redis Pub/Sub** | Native transient messaging | Zero persistence. Missing an event can stall a whole operational cycle. Unreliable for research-grade systems requiring deterministic state transitions. |
| **RabbitMQ / Kafka** | Dedicated message brokers | Significant infrastructure overhead. Adds network hops and management complexity that is unnecessary for the projected throughput (~10 events/sec). |
| **Redis Streams** | Log-structured messaging | **Selected.** |

---

### Decision
Use **Redis Streams** (`XADD`, `XREADGROUP`) instead of plain Pub/Sub. Each agent will belong to a Consumer Group, allowing for persistent message storage, explicit acknowledgement (`XACK`), and "at-least-once" delivery semantics.

---

### Rationale
Redis Streams provides the reliability of a message queue with the simplicity of the existing Redis deployment. It allows "replay-from-failure"—if an agent crashes at tick 12, it can resume reading from the stream where it left off, ensuring no critical cyclone or risk updates are missed. This is critical for Section 14 (Failure Scenarios) resilience.

---

### Consequences
- Agents must manage consumer group offsets.
- Dead-letter handling must be implemented (messages not ACKed after 3 retries).
- Event bus state survives Redis restarts if AOF (Append Only File) is enabled.

---

### Future Reconsideration Conditions
- If event throughput exceeds 50,000 events/sec or multiple-datacenter replication is required, migrate to Apache Kafka.

---
---

## ADR-008 — Conflict Resolution Scoring Model

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context
During disasters, demand for food, water, and fuel often exceeds available stock. Multiple shelters will request the same resources simultaneously.

---

### Problem
The Conflict Resolution Agent needs a mechanism to prioritize these requests that is mathematically sound, explainable to human stakeholders, and computationally efficient.

---

### Alternatives Considered

| Alternative | Description | Rejection Reason |
|---|---|---|
| **FCFS** | Chronological processing | Unfair and dangerous; a late-arriving critical request might be denied because resources were wasted on an earlier low-priority one. |
| **Equal Allocation** | Partition resources equally | No requesters get enough; everyone remains under-supplied. Violates the principle of triage. |
| **Optimization Solver (MILP)** | Use Linear Programming to maximize global utility | "Optimal" allocations are often "unintuitive/black-box" to stakeholders. Solvers are computationally heavy for real-time loops. Too complex for initial research prototype. |
| **Weighted Scoring Model** | 5-dimension priority score + greedy allocation | **Selected.** |

---

### Decision
Use a **deterministic weighted scoring model** (Life Safety + Risk Zone + Population + Criticality + Urgency) followed by a greedy allocation algorithm.

---

### Rationale
This model balances rigorous prioritization with transparent explainability. Unlike a solver, the logic ("Requester A had a higher risk score and lower supply levels") is easily translatable by the LLM into human-readable text. It satisfies the requirement for "explainable coordination" without sacrificing performance.

---

### Consequences
- Weights (Section 5.2 of RB) must be carefully calibrated and peer-validated.
- The model is deterministic; the same input always yields the identical allocation.
- Complexity is O(n log n) due to sorting, which easily meets performance NFRs.

---
---

## ADR-009 — Human-in-the-Loop Architecture

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context
MIRAGE functions as a recommendation engine for high-stakes emergency response.

---

### Problem
Can an AI system be trusted to execute disaster response plans autonomously? Who is accountable if a machine-driven resource allocation leads to a failure?

---

### Decision
Implement a **Hard Human-in-the-Loop (HITL)** architecture. No recommendation with high operational impact (Level 1-3) can be executed without explicit human authorization.

---

### Rationale
Trust and Accountability. In the context of a PhD-level project and real-world disaster governance, fully autonomous execution is ethically and legally untenable. The HITL approach creates a "governance layer" (Section 3 of RB) that ensures the AI supports, rather than replaces, human experts. This also increases the "Explainability Score" (M6) by forcing humans to engage with and validate agent reasoning.

---

### Consequences
- Decision latency (M1) includes human wait-time.
- The system must provide escalation rules if no human acts within the deadline.
- The UI must be designed to minimize cognitive load for the approver.

---
---

## ADR-010 — Experiment Recorder as First-Class Component

**Status:** Accepted  
**Date:** 2026-06-02

---

### Context
Academic publication requires rigorous, reproducible evaluation (Section 7 of RB).

---

### Problem
Metric collection is often an afterthought in software projects, leading to "bolted-on" telemetry that misses critical contextual data needed for research.

---

### Decision
The **Experiment Recorder is a core subsystem**, not a utility. It must be implemented before experiments begin and must capture per-tick metrics (M1-M8) atomically with agent execution.

---

### Rationale
Research validity. For the findings to be publishable at venues like ISCRAM or AAAI, we must prove that the data was collected systematically. A "First-Class" recorder ensures that all agent reasoning, conflict states, and approval cycles are captured for post-hoc statistical analysis without data gaps.

---

### Consequences
- Performance overhead of metric collection must be negligible to keep DL (M1) valid.
- The recorder must produce standardized CSV/Parquet files for Python/R analysis.
- Every simulation run is automatically "tagged" with metadata (seed, version, scenario).

---

### Risks
- If the recorder crashes, the entire simulation run is invalid. It needs high reliability.
- Disk I/O bottlenecks if recording is too verbose.

---
---

## Pack Conclusion
This ADR pack establishes MIRAGE as a **governed, explainable, and academically rigorous** system. The choice of Redis Streams, PostGIS, and a deterministic-first decision engine differentiates this project from typical "Agent Wrappers" and qualifies it as a systems-research-grade project.
