# MIRAGE – Software Requirements Specification (SRS)

Version: 1.0

Project Name: MIRAGE (Multi-Agent Intelligent Response and Governance Engine)

Document Type: Software Requirements Specification (SRS)

---

# 1. Introduction

## 1.1 Purpose

MIRAGE is an Explainable Approval-Aware Multi-Agent Coordination System designed to assist Emergency Operations Centers (EOCs) during cyclone disaster response.

Unlike existing disaster management platforms that primarily focus on forecasting, visualization, and alerts, MIRAGE focuses on operational coordination by supporting:

* Resource allocation
* Stakeholder coordination
* Conflict resolution
* Approval workflows
* Dynamic replanning

The system aims to improve decision quality, reduce response time, and provide transparent recommendations throughout the disaster lifecycle.

---

## 1.2 Scope

MIRAGE supports cyclone disaster management operations across five phases:

1. Early Warning
2. Risk Assessment
3. Evacuation Preparation
4. Response Coordination
5. Post-Landfall Recovery Planning

The system provides decision support for:

* Emergency Operations Centers
* Shelter Managers
* Logistics Officers
* Medical Coordinators

Version 1 is limited to cyclone scenarios.

---

## 1.3 Objectives

The objectives of MIRAGE are:

* Provide explainable disaster response recommendations
* Coordinate multiple operational stakeholders
* Resolve competing resource requests
* Maintain approval-aware workflows
* Support dynamic replanning during changing conditions
* Create a complete audit trail of decisions

---

# 2. Problem Statement

Current disaster management systems provide:

* Forecasting
* Mapping
* Alerting
* Data visualization

However, operational coordination remains largely manual.

Decision-makers must:

* Allocate scarce resources
* Resolve conflicting requests
* Track approvals
* Replan operations when conditions change

These tasks are often performed through spreadsheets, phone calls, emails, and manual coordination.

MIRAGE addresses this gap.

---

# 3. Stakeholders

## 3.1 Emergency Operations Center (EOC)

Responsibilities:

* Monitor disaster situation
* Review recommendations
* Approve critical actions
* Override agent decisions

---

## 3.2 Shelter Manager

Responsibilities:

* Manage shelter occupancy
* Monitor food and water stocks
* Request resources

---

## 3.3 Logistics Officer

Responsibilities:

* Manage transportation assets
* Plan delivery routes
* Coordinate supply movement

---

## 3.4 Medical Coordinator

Responsibilities:

* Track medical supplies
* Manage emergency medical support
* Request healthcare resources

---

# 4. System Overview

The system consists of six autonomous agents:

1. Risk Assessment Agent
2. Shelter Agent
3. Resource Agent
4. Logistics Agent
5. Conflict Resolution Agent
6. Approval Agent

Agents communicate through a shared operational knowledge repository called the Blackboard.

---

# 5. Functional Requirements

## FR-1 Risk Assessment

The system shall:

* Ingest cyclone forecast data
* Calculate risk scores
* Identify affected regions
* Prioritize response zones

---

## FR-2 Shelter Monitoring

The system shall:

* Track shelter capacity
* Track occupancy
* Monitor food availability
* Monitor water availability
* Predict shelter overflow

---

## FR-3 Resource Monitoring

The system shall:

* Track available resources
* Monitor consumption rates
* Forecast shortages
* Generate replenishment recommendations

Resources include:

* Food
* Water
* Fuel
* Medical Kits
* Blankets

---

## FR-4 Logistics Planning

The system shall:

* Track vehicle availability
* Track route status
* Monitor road disruptions
* Generate delivery plans
* Recommend alternative routes

---

## FR-5 Conflict Resolution

The system shall:

* Detect competing resource requests
* Prioritize requests
* Recommend resource allocations
* Provide explanations for decisions

---

## FR-6 Approval Workflow

The system shall:

* Route recommendations for approval
* Record approval status
* Record approver information
* Track approval history
* Escalate pending approvals

---

## FR-7 Dynamic Replanning

The system shall:

* Detect operational changes
* Recompute recommendations
* Update execution plans
* Notify affected stakeholders

Trigger examples:

* Road closure
* Resource shortage
* Shelter overflow
* Forecast change

---

## FR-8 Explainability

The system shall provide:

* Decision reasoning
* Supporting evidence
* Priority calculations
* Resource allocation rationale

---

## FR-9 Audit Trail

The system shall record:

* Decisions
* Approvals
* Resource allocations
* Recommendation history
* Stakeholder actions

---

# 6. Non-Functional Requirements

## NFR-1 Availability

System availability target:

99% during active simulation.

---

## NFR-2 Performance

Risk assessment updates:

≤ 5 seconds

Replanning operations:

≤ 10 seconds

---

## NFR-3 Scalability

System shall support:

* 100+ shelters
* 1000+ resource records
* 100+ active incidents

---

## NFR-4 Security

The system shall:

* Authenticate users
* Authorize actions based on role
* Protect operational data

---

## NFR-5 Explainability

Every recommendation shall contain:

* Reasoning
* Evidence
* Priority score
* Confidence level

---

## NFR-6 Reliability

System shall continue operating if an individual agent fails.

---

# 7. Agent Specifications

## Risk Assessment Agent

Inputs:

* Cyclone forecast
* Wind speed
* Rainfall
* Storm surge

Outputs:

* Risk scores
* Priority zones
* Impact predictions

---

## Shelter Agent

Inputs:

* Shelter data
* Occupancy data
* Inventory data

Outputs:

* Capacity alerts
* Overflow predictions

---

## Resource Agent

Inputs:

* Inventory records
* Consumption records

Outputs:

* Demand forecasts
* Shortage forecasts

---

## Logistics Agent

Inputs:

* Route data
* Vehicle status
* Weather impacts

Outputs:

* Delivery plans
* Alternative routes

---

## Conflict Resolution Agent

Inputs:

* Resource requests
* Risk levels
* Available inventory

Outputs:

* Allocation recommendations
* Conflict explanations

---

## Approval Agent

Inputs:

* Recommendations
* Approval requests

Outputs:

* Approval decisions
* Escalation notifications

---

# 8. Blackboard Architecture

The Blackboard shall maintain:

## INCIDENTS

Stores disaster events.

## SHELTERS

Stores shelter information.

## RESOURCES

Stores resource inventory.

## ROUTES

Stores route status.

## TASKS

Stores active tasks.

## APPROVALS

Stores approval workflows.

## DECISIONS

Stores recommendation history.

---

# 9. Event Model

Supported events include:

* CycloneUpdated
* RiskLevelChanged
* ShelterFull
* ShelterOverflowPredicted
* ResourceShortageDetected
* RouteBlocked
* ResourceRequestCreated
* ConflictDetected
* ApprovalRequested
* ApprovalGranted
* ApprovalRejected
* ReplanTriggered

---

# 10. Simulation Environment

The simulation engine shall generate:

## Cyclone Progression

Category changes over time.

## Shelter Demand

Population movement into shelters.

## Resource Consumption

Food, water, fuel, and medical usage.

## Infrastructure Failures

Road closures.

Bridge failures.

Power outages.

---

# 11. Evaluation Framework

## Experiment 1

Human-only coordination.

Baseline.

---

## Experiment 2

MIRAGE-assisted coordination.

Comparison system.

---

## Metrics

### M1 Decision Time

Average time required to make operational decisions.

### M2 Resource Allocation Efficiency

Allocated Resources / Requested Resources

### M3 Conflict Resolution Accuracy

Agreement with expert-defined allocation strategy.

### M4 Replanning Speed

Time required to generate revised plans.

### M5 Explainability Score

Human evaluation of recommendation clarity.

---

# 12. Assumptions

* Forecast data is available.
* Stakeholders interact through the platform.
* Resource inventory is maintained.
* Simulation data is realistic.

---

# 13. Constraints

* Cyclone disasters only.
* Single-region simulation.
* Human approval required before execution.
* No direct field deployment in Version 1.

---

# 14. Future Enhancements

* Multi-disaster support
* Real-time satellite integration
* UAV data integration
* Multi-region coordination
* Edge deployment
* Offline operation
* Digital Twin integration

---

# 15. Success Criteria

MIRAGE will be considered successful if:

* Decision time is reduced.
* Resource allocation efficiency improves.
* Conflict resolution quality improves.
* Replanning speed improves.
* Stakeholders understand recommendations.
* Complete auditability is maintained.
