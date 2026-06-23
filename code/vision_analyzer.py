from config import DATASET_DIR
from multimodal_evidence.verification.verifier import (
    _clamp_to_allowed, _clamp_risk_flags, _validate_gemini_response,
    analyze_claim_async
)

async def analyze_claim(
    claim,
    history,
    requirements,
    client,
    strategy="few_shot",
    semaphore=None
):
    return await analyze_claim_async(
        claim=claim,
        history=history,
        requirements=requirements,
        client=client,
        strategy=strategy,
        base_dir=DATASET_DIR,
        semaphore=semaphore
    )
