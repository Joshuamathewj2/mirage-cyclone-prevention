from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class LLMResponse(BaseModel):
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    output_text: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
