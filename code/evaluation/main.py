"""Evaluation entry point — runs pipeline on sample data and computes metrics.

Usage:
    python evaluation/main.py
    python evaluation/main.py --compare   # Compare both strategies
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

# Add parent code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    SAMPLE_CLAIMS_PATH, USER_HISTORY_PATH,
    EVIDENCE_REQUIREMENTS_PATH, PROJECT_ROOT,
)
from pipeline import run_pipeline
from evaluation.metrics import compute_metrics, print_metrics


def load_csv_as_dicts(path: Path) -> list[dict]:
    """Load a CSV file as a list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def evaluate_strategy(strategy: str, output_suffix: str = "") -> dict:
    """Run pipeline on sample data with a given strategy and compute metrics."""
    output_path = PROJECT_ROOT / f"output_sample_{strategy}{output_suffix}.csv"
    
    outputs, token_summary, elapsed = await run_pipeline(
        claims_path=SAMPLE_CLAIMS_PATH,
        history_path=USER_HISTORY_PATH,
        requirements_path=EVIDENCE_REQUIREMENTS_PATH,
        output_path=output_path,
        strategy=strategy,
    )
    
    # Load predictions and labels
    predictions = load_csv_as_dicts(output_path)
    labels = load_csv_as_dicts(SAMPLE_CLAIMS_PATH)
    
    # Compute metrics
    metrics = compute_metrics(predictions, labels)
    print_metrics(metrics)
    
    return {
        "strategy": strategy,
        "metrics": metrics,
        "token_summary": token_summary,
        "elapsed": elapsed,
        "output_path": str(output_path),
    }


async def compare_strategies():
    """Run both strategies on sample data and compare."""
    print("\n" + "="*70)
    print("STRATEGY COMPARISON")
    print("="*70)
    
    # Strategy 1: Direct
    print("\n\n>>> Strategy 1: DIRECT (no few-shot examples)")
    result_direct = await evaluate_strategy("direct")
    
    # Strategy 2: Few-shot
    print("\n\n>>> Strategy 2: FEW_SHOT (with representative examples)")
    result_few_shot = await evaluate_strategy("few_shot")
    
    # Comparison table
    print("\n\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    d = result_direct["metrics"]["overall"]
    f = result_few_shot["metrics"]["overall"]
    
    print(f"\n{'Metric':<35} {'Direct':>10} {'Few-Shot':>10} {'Winner':>10}")
    print("-" * 70)
    for key in d:
        dv = d[key]
        fv = f[key]
        winner = "Few-Shot" if fv > dv else ("Direct" if dv > fv else "Tie")
        print(f"  {key:<33} {dv:>9.1%} {fv:>9.1%} {winner:>10}")
    
    print(f"\n{'Operational':<35} {'Direct':>10} {'Few-Shot':>10}")
    print("-" * 70)
    dt = result_direct["token_summary"]
    ft = result_few_shot["token_summary"]
    print(f"  {'Total API calls':<33} {dt['total_calls']:>10} {ft['total_calls']:>10}")
    print(f"  {'Total tokens':<33} {dt['total_tokens']:>10,} {ft['total_tokens']:>10,}")
    print(f"  {'Time (seconds)':<33} {result_direct['elapsed']:>10.1f} {result_few_shot['elapsed']:>10.1f}")
    
    # Recommendation
    best = "few_shot" if f["claim_status_accuracy"] >= d["claim_status_accuracy"] else "direct"
    print(f"\n✅ Recommended strategy: {best}")
    
    return result_direct, result_few_shot


def main():
    parser = argparse.ArgumentParser(description="Evaluate the Evidence Review system")
    parser.add_argument(
        "--compare", action="store_true",
        help="Compare both strategies (direct vs few_shot)"
    )
    parser.add_argument(
        "--strategy", type=str, default="few_shot",
        choices=["direct", "few_shot"],
        help="Strategy to evaluate (default: few_shot)"
    )
    args = parser.parse_args()
    
    if args.compare:
        asyncio.run(compare_strategies())
    else:
        asyncio.run(evaluate_strategy(args.strategy))


if __name__ == "__main__":
    main()
