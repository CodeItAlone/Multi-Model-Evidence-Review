"""Evidence ranking, risk flag merging, and decision guardrails module.

Applies post-processing business rules to ensure consistency and risk alignment.
"""

from multimodal_evidence.models.claim import (
    GeminiAnalysisResult, ClaimInput, UserHistory,
    ClaimOutput, ALL_RISK_FLAGS
)


def merge_risk_flags(
    gemini_flags: list[str],
    history: UserHistory | None,
    local_flags: list[str] | None = None,
) -> list[str]:
    """Merge risk flags from Gemini, user history, and local image validation.
    
    Rules:
    - Add history flags (user_history_risk, manual_review_required) if present
    - Deduplicate
    - Remove "none" if other flags exist
    """
    all_flags = set()
    
    # Gemini flags
    for f in gemini_flags:
        if f in ALL_RISK_FLAGS and f != "none":
            all_flags.add(f)
    
    # Local image validation flags
    if local_flags:
        for f in local_flags:
            if f in ALL_RISK_FLAGS and f != "none":
                all_flags.add(f)
    
    # User history flags
    if history and history.has_risk:
        for flag in history.flag_list:
            if flag in ALL_RISK_FLAGS:
                all_flags.add(flag)
    
    if not all_flags:
        return ["none"]
    
    return sorted(all_flags)


def apply_decision_guardrails(result: GeminiAnalysisResult) -> GeminiAnalysisResult:
    """Apply business rules that override Gemini's raw output.
    
    Rules:
    1. If valid_image=false → claim_status MUST be not_enough_information
    2. If evidence_standard_met=false → claim_status MUST be not_enough_information
    3. If claim_status is NEI → supporting_image_ids should be ["none"]
    """
    status = result.claim_status
    justification = result.claim_status_justification
    supporting = result.supporting_image_ids
    
    # Rule 1 & 2: Force NEI when evidence is insufficient
    if not result.valid_image or not result.evidence_standard_met:
        if status != "not_enough_information":
            status = "not_enough_information"
            justification = (
                result.claim_status_justification
                + " [Overridden: evidence standard not met or images not usable.]"
            )
    
    # Rule 3: NEI should have no supporting images
    if status == "not_enough_information":
        supporting = ["none"]
    
    return GeminiAnalysisResult(
        evidence_standard_met=result.evidence_standard_met,
        evidence_standard_met_reason=result.evidence_standard_met_reason,
        risk_flags=result.risk_flags,
        issue_type=result.issue_type,
        object_part=result.object_part,
        claim_status=status,
        claim_status_justification=justification,
        supporting_image_ids=supporting,
        valid_image=result.valid_image,
        severity=result.severity,
    )


def build_claim_output(
    claim: ClaimInput,
    result: GeminiAnalysisResult,
    history: UserHistory | None,
) -> ClaimOutput:
    """Build the final ClaimOutput from claim input + Gemini result + history.
    
    Merges risk flags and applies guardrails before formatting.
    """
    # Merge all risk flags
    merged_flags = merge_risk_flags(result.risk_flags, history)
    
    # Apply guardrails
    guarded = apply_decision_guardrails(GeminiAnalysisResult(
        evidence_standard_met=result.evidence_standard_met,
        evidence_standard_met_reason=result.evidence_standard_met_reason,
        risk_flags=merged_flags,
        issue_type=result.issue_type,
        object_part=result.object_part,
        claim_status=result.claim_status,
        claim_status_justification=result.claim_status_justification,
        supporting_image_ids=result.supporting_image_ids,
        valid_image=result.valid_image,
        severity=result.severity,
    ))
    
    # Format for CSV output
    return ClaimOutput(
        user_id=claim.user_id,
        image_paths=";".join(claim.image_paths),
        user_claim=claim.user_claim,
        claim_object=claim.claim_object,
        evidence_standard_met=str(guarded.evidence_standard_met).lower(),
        evidence_standard_met_reason=guarded.evidence_standard_met_reason,
        risk_flags=";".join(guarded.risk_flags),
        issue_type=guarded.issue_type,
        object_part=guarded.object_part,
        claim_status=guarded.claim_status,
        claim_status_justification=guarded.claim_status_justification,
        supporting_image_ids=";".join(guarded.supporting_image_ids),
        valid_image=str(guarded.valid_image).lower(),
        severity=guarded.severity,
    )


def rank_evidence(
    claim_input: dict,
    gemini_result: dict,
    history: dict | None = None
) -> dict:
    """Exposed SDK API: Applies risk aggregation and overrides on raw Gemini findings.
    
    Args:
        claim_input: Dictionary of claim details matching ClaimInput schema.
        gemini_result: Raw unstructured or structured Gemini analysis result.
        history: Optional user claim history record dict matching UserHistory schema.
        
    Returns:
        dict: Final ranked/guarded claim status verification output details.
    """
    claim = ClaimInput(**claim_input)
    res = GeminiAnalysisResult(**gemini_result)
    user_hist = UserHistory(**history) if history else None
    
    output = build_claim_output(claim, res, user_hist)
    return output.model_dump()
