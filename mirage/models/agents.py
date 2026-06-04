from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
from abc import ABC, abstractmethod

class RecommendationCategory(str, Enum):
    RISK = "RISK"
    LOGISTICS = "LOGISTICS"
    GOVERNANCE = "GOVERNANCE"
    COMMUNICATION = "COMMUNICATION"
    SHELTER = "SHELTER"

class Recommendation(BaseModel):
    """Standardized Recommendation Protocol object."""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    tick: int
    agent_name: str
    category: RecommendationCategory
    priority: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str
    proposed_action: Dict[str, Any]
    accepted: bool = False
    implementation_status: str = "PENDING"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseAgent(ABC):
    """Abstract Base Class for all MIRAGE agents."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self._name = name
        self._version = version

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @abstractmethod
    def evaluate(self, state: Any) -> Dict[str, Any]:
        """Analyze the current state and return findings."""
        pass

    @abstractmethod
    def generate_recommendation(self, state: Any) -> List[Recommendation]:
        """Generate actionable recommendations based on state."""
        pass
