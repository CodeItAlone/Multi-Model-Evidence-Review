"""Batch claim pipeline orchestrator with async concurrency.

Processes claims end-to-end concurrently, resolving user history
and evidence requirements, and returns structured predictions.
"""

import asyncio
import time
from pathlib import Path
from tqdm import tqdm

from multimodal_evidence.models.claim import ClaimInput, ClaimOutput
from multimodal_evidence.retrieval.search import (
    parse_claims, parse_user_history, parse_evidence_requirements,
)
from multimodal_evidence.multimodal.client import GeminiClient
# Import analyze_claim_async inside function to prevent circular dependency

from multimodal_evidence.ranking.ranker import build_claim_output


async def process_single_claim_async(
    claim: ClaimInput,
    history_map: dict,
    requirements: list,
    client: GeminiClient,
    strategy: str,
    base_dir: Path | None,
    semaphore: asyncio.Semaphore,
) -> ClaimOutput:
    """Process a single claim through the SDK pipeline."""
    from multimodal_evidence.verification.verifier import analyze_claim_async
    history = history_map.get(claim.user_id)
    
    result = await analyze_claim_async(
        claim=claim,
        history=history,
        requirements=requirements,
        client=client,
        strategy=strategy,
        base_dir=base_dir,
        semaphore=semaphore,
    )
    
    return build_claim_output(claim, result, history)


async def run_pipeline_async(
    claims_path: str | Path,
    history_path: str | Path,
    requirements_path: str | Path,
    strategy: str = "few_shot",
    concurrency: int = 5,
    api_key: str = "",
    model: str = "",
    base_dir: str | Path | None = None,
    show_progress: bool = True,
) -> tuple[list[ClaimOutput], dict, float]:
    """Run the batch claims pipeline asynchronously.
    
    Args:
        claims_path: Path to input claims CSV.
        history_path: Path to user_history.csv.
        requirements_path: Path to evidence_requirements.csv.
        strategy: prompt strategy ('direct' or 'few_shot').
        concurrency: Max concurrent API calls.
        api_key: Override Gemini API key.
        model: Override Gemini model name.
        base_dir: Optional base directory to resolve relative image paths.
        show_progress: Whether to render the tqdm progress bar.
        
    Returns:
        tuple: (list of ClaimOutput models, token usage summary, elapsed time)
    """
    claims = parse_claims(claims_path)
    history_map = parse_user_history(history_path)
    requirements = parse_evidence_requirements(requirements_path)
    
    client = GeminiClient(api_key=api_key, model=model)
    semaphore = asyncio.Semaphore(concurrency)
    resolved_base_dir = Path(base_dir) if base_dir else None
    
    start_time = time.time()
    
    tasks = [
        process_single_claim_async(
            claim, history_map, requirements, client, strategy, resolved_base_dir, semaphore
        )
        for claim in claims
    ]
    
    outputs = []
    if show_progress:
        for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Analyzing claims"):
            result = await coro
            outputs.append(result)
    else:
        outputs = await asyncio.gather(*tasks)
        
    elapsed = time.time() - start_time
    
    # Re-order outputs to match input order
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
            # Fallback (should not happen if keys match)
            ordered_outputs.append(outputs[len(ordered_outputs)])
            
    token_summary = client.tracker.summary()
    return ordered_outputs, token_summary, elapsed
