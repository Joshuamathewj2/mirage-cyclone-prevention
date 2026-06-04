from typing import Annotated, Sequence, TypedDict, Union, List
from mirage.models.state import MirageState
from mirage.models.agents import Recommendation

class GraphState(TypedDict):
    # The current global state of the simulation
    mirage_state: MirageState
    # The cumulative list of recommendations generated in the current graph turn
    recommendations: List[Recommendation]
    # Current active agent/node
    current_node: str
    # Convergence flag
    is_stable: bool
    # History of agent actions in this turn
    action_log: List[str]
