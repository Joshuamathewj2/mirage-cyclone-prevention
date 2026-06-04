from abc import ABC, abstractmethod
from typing import Any, Dict

class DigitalTwin(ABC):
    def __init__(self, name: str):
        self.name = name

    def initialize(self, blackboard: Any) -> None:
        """Seed initial state into the Blackboard before simulation starts.
        Override in subclasses that need pre-tick-1 seeding."""
        pass

    @abstractmethod
    def update(self, tick: int, blackboard: Any) -> Dict[str, Any]:
        """Update the DT state for the current tick."""
        pass
