from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class ResourceType(str, Enum):
    FOOD = "FOOD"
    WATER = "WATER"
    FUEL = "FUEL"
    MEDICAL_KIT = "MEDICAL_KIT"
    BLANKET = "BLANKET"

class TaskType(str, Enum):
    DELIVER = "DELIVER"
    EVACUATE = "EVACUATE"
    REPAIR = "REPAIR"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    REPLANNING = "REPLANNING"
    SUPERSEDED = "SUPERSEDED"

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED_L1 = "APPROVED_L1"
    APPROVED_L2 = "APPROVED_L2"
    APPROVED_L3 = "APPROVED_L3"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_plan_id: str
    target_action: Dict[str, Any]
    required_level: int = 1
    current_level: int = 0
    status: ApprovalStatus = ApprovalStatus.PENDING
    deadline: datetime
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ApprovalDecision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    approver_id: str
    level: int
    decision: ApprovalStatus # APPROVED_LX or REJECTED
    reason: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.now)

class GeoPoint(BaseModel):
    lat: float
    lon: float

class Cyclone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    simulation_id: str
    name: str
    category: int = Field(ge=1, le=5)
    position: GeoPoint
    wind_speed_kmh: float
    storm_surge_m: Optional[float] = None
    rainfall_mm: Optional[float] = None
    predicted_path: Optional[List[GeoPoint]] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    risk_score: float = 0.0
    priority_zones: List[str] = []

class Shelter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: GeoPoint
    capacity: int
    current_occupancy: int = 0
    food_days: float = 0.0
    water_days: float = 0.0
    overflow_risk: float = 0.0
    status: str = "OPERATIONAL"
    zone_id: str

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ResourceType
    quantity: float
    unit: str
    location: Optional[GeoPoint] = None
    shelter_id: Optional[str] = None
    reorder_threshold: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.now)

class Route(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    origin: GeoPoint
    destination: GeoPoint
    distance_km: float
    status: str = "CLEAR"
    blockage_reason: Optional[str] = None
    alt_route_id: Optional[str] = None

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType
    created_by: str  # agent name
    priority: float = Field(default=0.0, ge=0.0, le=1.0)
    status: TaskStatus = TaskStatus.PENDING
    resource_type: Optional[ResourceType] = None
    resource_qty: Optional[float] = None
    target_shelter_id: Optional[str] = None
    target_route_id: Optional[str] = None
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Decision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by_agent: str
    recommendation: str
    reasoning: str
    evidence: List[Dict[str, Any]] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = "PENDING"
    conflict_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Approval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str
    level: int = 1
    assigned_to_role: str
    assigned_to_user_id: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    deadline: datetime
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    escalation_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

class ResourceRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    shelter_id: str
    resource_type: ResourceType
    quantity_requested: float
    timestamp: datetime = Field(default_factory=datetime.now)
    risk_score: float
    occupancy_ratio: float
    stock_days_remaining: float
    accessibility_score: float

class Allocation(BaseModel):
    request_id: str
    shelter_id: str
    resource_type: ResourceType
    quantity_requested: float
    quantity_allocated: float
    explanation: str

class AllocationPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tick: int
    allocations: List[Allocation]
    summary: str
    created_at: datetime = Field(default_factory=datetime.now)

class ShelterAssessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    shelter_id: str
    tick: int
    occupancy_rate: float
    infrastructure_status: str
    isolation_risk: float
    resource_gap: Dict[str, float]
    assessment_score: float

class DeliveryItem(BaseModel):
    resource_type: ResourceType
    quantity: float

class DeliveryPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    allocation_plan_id: str
    source_depot_id: str
    target_shelter_id: str
    route_id: str
    items: List[DeliveryItem]
    estimated_arrival_tick: int
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.now)
