# MIRAGE Agent Contracts (Phase 7)

This document defines the operational inputs, outputs, and event-driven signals for all MIRAGE agents and core engines.

## 1. Risk Assessment Agent
- **Inputs**: `MirageState.cyclone`
- **Outputs**: `RecommendationCategory.RISK`
- **Events Produced**: `CYCLONE_INTENSITY_ALERT`
- **Events Consumed**: None

## 2. Shelter Agent
- **Inputs**: `MirageState.shelters`, `MirageState.cyclone`
- **Outputs**: `ShelterAssessment`, `ResourceRequest` (via Recommendations)
- **Events Produced**: `SHELTER_OVERCAPACITY`, `ISOLATION_RISK_DETECTED`
- **Events Consumed**: `CYCLONE_INTENSITY_ALERT`

## 3. Resource Advisor Agent
- **Inputs**: `MirageState.resources`
- **Outputs**: `RecommendationCategory.LOGISTICS` (Restock advise)
- **Events Produced**: `LOW_STOCK_WARNING`
- **Events Consumed**: None

## 4. Conflict Resolution Engine
- **Inputs**: `List[ResourceRequest]`, `List[Resource]`
- **Outputs**: `AllocationPlan`
- **Events Produced**: `ALLOCATION_READY`, `RESOURCE_SHORTAGE_REJECTION`
- **Events Consumed**: `REQUEST_RESOURCES`

## 5. Approval Engine
- **Inputs**: `AllocationPlan`
- **Outputs**: `ApprovalDecision`
- **Events Produced**: `APPROVAL_GRANTED`, `APPROVAL_DENIED`, `ESCALATION_TRIGGERED`
- **Events Consumed**: `ALLOCATION_READY`

## 6. Logistics Agent
- **Inputs**: `MirageState.allocation_history`, `MirageState.active_tasks`
- **Outputs**: `DeliveryPlan` (via Recommendations)
- **Events Produced**: `DELIVERY_PLAN_CREATED`, `ROUTE_FAILURE_ALERT`
- **Events Consumed**: `APPROVAL_GRANTED`

## 7. Governance Advisor Agent
- **Inputs**: `MirageState.approval_records`
- **Outputs**: `RecommendationCategory.GOVERNANCE`
- **Events Produced**: `GOVERNANCE_SLO_VIOLATION`
- **Events Consumed**: `ESCALATION_TRIGGERED`
