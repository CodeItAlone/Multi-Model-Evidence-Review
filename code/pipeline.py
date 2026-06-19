"""Pipeline orchestrator — processes claims end-to-end with async concurrency.

Flow per claim:
  1. Load context (history, requirements)
  2. Validate images locally
  3. Call Gemini vision analyzer
  4. Post-process (merge flags, apply guardrails)
  5. Build output row

Supports configurable concurrency and progress tracking.
"""

import asyncio
import time
from pathlib import Path
from tqdm import tqdm

from config import CONCURRENCY
from models import ClaimInput, ClaimOutput
from parsers import (
    parse_claims, parse_user_history, parse_evidence_requirements,
    parse_sample_labels, get_applicable_requirements,
)
from gemini_client import GeminiClient
from vision_analyzer import analyze_claim
from post_processor import build_claim_output
from output_writer import write_output_csv, validate_output_csv


async def process_single_claim(
    claim: ClaimInput,
    history_map: dict,
    requirements: list,
    client: GeminiClient,
    strategy: str,
    semaphore: asyncio.Semaphore,
) -> ClaimOutput:
    """Process a single claim through the full pipeline."""
    history = history_map.get(claim.user_id)
    
    # Analyze with Gemini
    result = await analyze_claim(
        claim=claim,
        history=history,
        requirements=requirements,
        client=client,
        strategy=strategy,
        semaphore=semaphore,
    )
    
    # Post-process and build output
    return build_claim_output(claim, result, history)


async def run_pipeline(
    claims_path: Path,
    history_path: Path,
    requirements_path: Path,
    output_path: Path,
    strategy: str = "few_shot",
    concurrency: int = CONCURRENCY,
    api_key: str = "",
    model: str = "",
) -> list[ClaimOutput]:
    """Run the full pipeline on a claims CSV file.
    
    Args:
        claims_path: Path to claims CSV (sample or test)
        history_path: Path to user_history.csv
        requirements_path: Path to evidence_requirements.csv
        output_path: Path to write output.csv
        strategy: "direct" or "few_shot"
        concurrency: Max parallel Gemini calls
        api_key: Override API key
        model: Override model name
        
    Returns:
        List of ClaimOutput objects
    """
    print(f"\n{'='*60}")
    print(f"Multi-Modal Evidence Review Pipeline")
    print(f"{'='*60}")
    print(f"Strategy: {strategy}")
    print(f"Concurrency: {concurrency}")
    print(f"Input: {claims_path}")
    print(f"Output: {output_path}")
    
    # Step 1: Load all data
    print("\n[1/4] Loading data...")
    claims = parse_claims(claims_path)
    history_map = parse_user_history(history_path)
    requirements = parse_evidence_requirements(requirements_path)
    print(f"  Loaded {len(claims)} claims, {len(history_map)} user histories, {len(requirements)} requirements")
    
    # Step 2: Initialize Gemini client
    print("\n[2/4] Initializing Gemini client...")
    client = GeminiClient(api_key=api_key, model=model)
    semaphore = asyncio.Semaphore(concurrency)
    
    # Step 3: Process all claims
    print(f"\n[3/4] Processing {len(claims)} claims...")
    start_time = time.time()
    
    # Create tasks
    tasks = [
        process_single_claim(claim, history_map, requirements, client, strategy, semaphore)
        for claim in claims
    ]
    
    # Run with progress tracking
    outputs = []
    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Analyzing claims"):
        result = await coro
        outputs.append(result)
    
    elapsed = time.time() - start_time
    
    # Re-order outputs to match input order (as_completed doesn't preserve order)
    # Build a map from (user_id, image_paths) -> output
    output_map = {}
    for out in outputs:
        key = (out.user_id, out.image_paths)
        output_map[key] = out
    
    ordered_outputs = []
    for claim in claims:
        key = (claim.user_id, ";".join(claim.image_paths))
        if key in output_map:
            ordered_outputs.append(output_map[key])
        else:
            # Fallback: find by position (shouldn't happen)
            ordered_outputs.append(outputs[len(ordered_outputs)])
    
    # Step 4: Write output
    print(f"\n[4/4] Writing output to {output_path}...")
    write_output_csv(ordered_outputs, output_path)
    
    # Validate
    errors = validate_output_csv(output_path, expected_rows=len(claims))
    if errors:
        print(f"\n⚠️  Validation warnings:")
        for err in errors:
            print(f"  - {err}")
    else:
        print(f"  ✅ Output validated: {len(ordered_outputs)} rows, 14 columns")
    
    # Summary
    token_summary = client.tracker.summary()
    print(f"\n{'='*60}")
    print(f"Pipeline Complete!")
    print(f"{'='*60}")
    print(f"  Claims processed: {len(ordered_outputs)}")
    print(f"  Time elapsed: {elapsed:.1f}s ({elapsed/len(claims):.1f}s per claim)")
    print(f"  API calls: {token_summary['total_calls']} (failed: {token_summary['failed_calls']})")
    print(f"  Tokens — input: {token_summary['total_input_tokens']:,}, output: {token_summary['total_output_tokens']:,}")
    print(f"  Output: {output_path}")
    
    return ordered_outputs, token_summary, elapsed
