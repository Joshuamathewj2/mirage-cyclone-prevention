```mermaid
gantt
    title Cyclone Scenario Execution Flow (A/101)
    dateFormat  s
    axisFormat %s
    section Pre-Landfall
    Evacuation Warnings     :a1, 0, 12s
    Resource Pre-positioning:a2, 2s, 10s
    section Landfall
    Storm Surge Hits        :crit, b1, 12s, 8s
    Infra Degradation       :b2, 12s, 16s
    section Post-Landfall
    Logistics Recovery      :c1, 18s, 10s
    Shelter Restocking      :c2, 20s, 28s
```