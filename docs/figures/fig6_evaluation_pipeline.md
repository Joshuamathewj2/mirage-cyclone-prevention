```mermaid
graph LR;
    A[Scenarios] --> C[Simulation Loop]
    B[Seeds] --> C
    D[Baselines] --> C
    C --> E[Recorder JSON/CSV]
    E --> F[Metric Calculator]
    F --> G[Results Summary]
```