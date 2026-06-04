# MIRAGE Final Defense: Viva Voce Questions

## 1. Technical Implementation
**Q1: How do you prevent agents from corrupting the simulation state?**
*Ideal Answer:* MIRAGE uses an asymmetric architecture. Agents only have read access to the `MirageState`. They publish `Recommendation` objects to the Blackboard. The deterministic `SimulationClock` and `ConflictResolver` evaluate these recommendations and make the actual state changes.

**Q2: Why use Pydantic models for the Blackboard?**
*Ideal Answer:* It provides strict schema validation, ensuring that data moving between the Digital Twins and the generic agents is strongly typed, mitigating runtime errors caused by unexpected agent outputs.

## 2. Architecture Questions
**Q3: Why separate the Digital Twins (DT) from the Agents?**
*Ideal Answer:* Separation of concerns. DTs emulate physical reality (weather, population limits). Agents emulate human coordination strategy. Blurring them creates un-testable systems where we cannot tell if a failure was bad physics or a bad decision.

**Q4: Explain the conflict resolution algorithm.**
*Ideal Answer:* It uses a weighted priority scoring model. It considers Risk, Occupancy, Urgency (stock days remaining), and Accessibility. When requests exceed inventory, it ranks them. If scores are equal at the threshold of inventory exhaustion, it applies a pro-rata distribution to ensure mathematical fairness.

## 3. Methodology Questions
**Q5: Why did MIRAGE show 0.0 'Resilience' (M10) while Manuel baselines scored 0.98?**
*Ideal Answer:* M10 measured absolute stock levels. Manual baselines failed to evacuate populations, meaning shelters remained empty and stocks were untouched (scoring high). MIRAGE successfully evacuated populations, draining the stocks. It highlights a common flaw in naive metrics applied to complex systems.

## 4. Criticism & Weaknesses
**Q6: What happens if the Redis broker goes offline?**
*Ideal Answer:* The `Blackboard` is designed with an in-memory python dictionary fallback mechanism. While cross-process pub/sub is lost, the local simulation thread can continue without data loss.