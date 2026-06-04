import os
import json
import time
import pandas as pd
from typing import List, Dict, Any
from mirage.models.state import MirageState
from mirage.agents.llm_agent import LLMCommunicationAgent
from mirage.agents.rule_based_comm import RuleBasedCommunicationAgent
from mirage.core.llm_adapters import MockAdapter, OpenAIAdapter, ClaudeAdapter, GeminiAdapter
from mirage.core.evaluation import calculate_completeness, calculate_consistency, calculate_readability

def main():
    benchmark_file = "data/benchmark_inputs.json"
    if not os.path.exists(benchmark_file):
        print("Benchmark file not found. Run generate_benchmarks.py first.")
        return

    with open(benchmark_file, "r") as f:
        benchmarks = json.load(f)

    # Note: For full run, we'd need keys. For now, we'll use Mock + logic for others if keys missing.
    adapters = [
        MockAdapter("mock-v1"),
        # OpenAIAdapter("gpt-4o"), # Uncomment if keys available
        # ClaudeAdapter("claude-3-5-sonnet"),
        # GeminiAdapter("gemini-1.5-pro")
    ]
    
    # Also include the rule-based baseline
    baseline_agent = RuleBasedCommunicationAgent()
    
    results = []
    
    output_dir = "outputs/llm_benchmarks"
    os.makedirs(output_dir, exist_ok=True)
    
    for bm in benchmarks:
        tick = bm["tick"]
        scenario_id = bm["scenario_id"]
        state_dict = bm["state"]
        state = MirageState(**state_dict)
        
        # 1. Evaluate Baseline
        start_time = time.time()
        bulletin_base = baseline_agent.generate_bulletin(state, scenario_id)
        latency_base = (time.time() - start_time) * 1000
        
        eval_base = {
            "completeness": calculate_completeness(bulletin_base, state),
            "consistency": calculate_consistency(bulletin_base, state),
            "readability": calculate_readability(bulletin_base.executive_summary)
        }
        
        results.append({
            "scenario": scenario_id,
            "tick": tick,
            "model": "Baseline/Rule-Based",
            "latency_ms": latency_base,
            "completeness": eval_base["completeness"],
            "consistency": eval_base["consistency"],
            "ease": eval_base["readability"]["ease"],
            "grade": eval_base["readability"]["grade"],
            "cost": 0.0,
            "tokens": 0
        })

        # 2. Evaluate LLM Adapters
        for adapter in adapters:
            agent = LLMCommunicationAgent(adapter)
            start_time = time.time()
            bulletin = agent.generate_bulletin(state, scenario_id)
            latency = (time.time() - start_time) * 1000
            
            # For Mock, we simulate some variability if needed, but here we just evaluate
            eval_llm = {
                "completeness": calculate_completeness(bulletin, state),
                "consistency": calculate_consistency(bulletin, state),
                "readability": calculate_readability(bulletin.executive_summary)
            }
            
            results.append({
                "scenario": scenario_id,
                "tick": tick,
                "model": f"{adapter.provider_name}/{adapter.model_name}",
                "latency_ms": latency,
                "completeness": eval_llm["completeness"],
                "consistency": eval_llm["consistency"],
                "ease": eval_llm["readability"]["ease"],
                "grade": eval_llm["readability"]["grade"],
                "cost": 0.01, # Mock cost
                "tokens": 150 # Mock tokens
            })
            
    # Save results
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(output_dir, "benchmark_results.csv"), index=False)
    
    # Generate Report
    generate_report(df)

def generate_report(df):
    summary = df.groupby("model").agg({
        "completeness": "mean",
        "consistency": "mean",
        "latency_ms": "mean",
        "ease": "mean",
        "grade": "mean",
        "cost": "sum"
    }).reset_index()
    
    report = "# LLM Communication Benchmark Report\n\n"
    report += "## 1. Provider Comparison\n\n"
    report += summary.to_markdown(index=False)
    report += "\n\n## 2. Key Findings\n"
    report += "- **Completeness**: How much critical info was captured.\n"
    report += "- **Consistency**: Accuracy vs Digital Twin state.\n"
    report += "- **Readability**: Target audience accessibility.\n"
    
    with open("outputs/llm_benchmarks/llm_benchmark_report.md", "w") as f:
        f.write(report)
    
    print("Benchmark completed. Report generated at outputs/llm_benchmarks/llm_benchmark_report.md")

if __name__ == "__main__":
    main()
