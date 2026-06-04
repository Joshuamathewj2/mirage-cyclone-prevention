from typing import List, Dict, Any, Callable
from pydantic import BaseModel

class TransitionContract(BaseModel):
    source_node: str
    target_node: str
    condition: str
    description: str

# Defined transitions for Phase 7 validation
MIRAGE_TRANSITIONS = [
    TransitionContract(
        source_node="RiskNode",
        target_node="ShelterNode",
        condition="HighRisk",
        description="Escalate to shelter assessment if risk is critical."
    ),
    TransitionContract(
        source_node="ShelterNode",
        target_node="ResourceNode",
        condition="ShortageDetected",
        description="Request resources from depots."
    ),
    TransitionContract(
        source_node="ResourceNode",
        target_node="LogisticsNode",
        condition="AllocationReady",
        description="Plan delivery for allocated resources."
    )
]
