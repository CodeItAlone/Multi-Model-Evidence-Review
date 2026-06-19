"""CLI entry point for the Multi-Modal Evidence Review pipeline.

Usage:
    # Run on test data (default)
    python main.py
    
    # Run on sample data (for evaluation)
    python main.py --sample
    
    # Run with specific strategy
    python main.py --strategy direct
    
    # Custom paths
    python main.py --input path/to/claims.csv --output path/to/output.csv
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    SAMPLE_CLAIMS_PATH, TEST_CLAIMS_PATH,
    USER_HISTORY_PATH, EVIDENCE_REQUIREMENTS_PATH,
    OUTPUT_PATH, PROJECT_ROOT,
)
from pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Modal Evidence Review Pipeline"
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="Run on sample_claims.csv instead of claims.csv"
    )
    parser.add_argument(
        "--input", type=str, default=None,
        help="Custom input CSV path"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Custom output CSV path"
    )
    parser.add_argument(
        "--strategy", type=str, default="few_shot",
        choices=["direct", "few_shot"],
        help="Prompt strategy (default: few_shot)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=5,
        help="Max parallel Gemini calls (default: 5)"
    )
    parser.add_argument(
        "--api-key", type=str, default="",
        help="Gemini API key (overrides env var)"
    )
    parser.add_argument(
        "--model", type=str, default="",
        help="Gemini model name (overrides env var)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    if args.input:
        claims_path = Path(args.input)
    elif args.sample:
        claims_path = SAMPLE_CLAIMS_PATH
    else:
        claims_path = TEST_CLAIMS_PATH
    
    if args.output:
        output_path = Path(args.output)
    elif args.sample:
        output_path = PROJECT_ROOT / "output_sample.csv"
    else:
        output_path = OUTPUT_PATH
    
    # Run pipeline
    outputs, token_summary, elapsed = asyncio.run(
        run_pipeline(
            claims_path=claims_path,
            history_path=USER_HISTORY_PATH,
            requirements_path=EVIDENCE_REQUIREMENTS_PATH,
            output_path=output_path,
            strategy=args.strategy,
            concurrency=args.concurrency,
            api_key=args.api_key,
            model=args.model,
        )
    )


if __name__ == "__main__":
    main()
