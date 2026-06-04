from abc import ABC, abstractmethod
from typing import Dict, Any
from mirage.graph.state import GraphState

class BaseNode(ABC):
    """Base interface for all LangGraph nodes in MIRAGE."""
    
    @abstractmethod
    def __call__(self, state: GraphState) -> GraphState:
        """Execute node logic and return updated state."""
        pass

class AgentNode(BaseNode):
    """Wraps a MIRAGE agent into a graph node."""
    
    def __init__(self, agent: Any):
        self.agent = agent

    def __call__(self, state: GraphState) -> GraphState:
        # 1. Evaluate state
        # 2. Generate recommendations
        # 3. Update GraphState.recommendations
        # 4. Log action
        return state

class GovernanceNode(BaseNode):
    """Deterministic governance control node."""
    
    def __call__(self, state: GraphState) -> GraphState:
        # Check if recommendations violate rules
        return state
