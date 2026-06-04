```mermaid
sequenceDiagram
    participant Blackboard
    participant ResourceAgent
    participant ConflictResolver
    Blackboard->>ResourceAgent: Read Current State
    ResourceAgent->>ResourceAgent: Identify Needs
    ResourceAgent->>Blackboard: Write Recommendation
    Blackboard->>ConflictResolver: Fetch Recommendations
    ConflictResolver->>ConflictResolver: Score & Prioritize
    ConflictResolver->>Blackboard: Write Allocation Plan
```