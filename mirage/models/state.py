from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid
from mirage.models.entities import (
    Cyclone, Shelter, Resource, Route, 
    ResourceRequest, AllocationPlan, ApprovalRequest, Task
)

class MirageState(BaseModel):
    """Centralized Global State for MIRAGE agents."""
    simulation_tick: int
    cyclone: Optional[Cyclone] = None
    shelters: List[Shelter] = []
    resources: List[Resource] = []
    conflicts: List[ResourceRequest] = []
    allocation_history: List[AllocationPlan] = []
    approval_records: List[ApprovalRequest] = []
    active_tasks: List[Task] = []
    
    # Research & Metadata
    metrics: Dict[str, float] = {}
    recommendations: List[Any] = [] # List[Recommendation]
    communications: List[Dict[str, Any]] = []
    
    # Audit
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
