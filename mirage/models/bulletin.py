from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class CommunicationBulletin(BaseModel):
    bulletin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    scenario: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    headline: str
    executive_summary: str
    affected_shelters: List[str]
    recommended_public_actions: List[str]
    governance_notes: str
    confidence: float
    model_info: Optional[str] = None # model/provider used
