"""Vision analyzer — orchestrates prompt building, image loading, and Gemini calls.

This is the core analysis module. For each claim it:
1. Loads and validates images
2. Builds the appropriate prompt (direct or few_shot strategy)
3. Calls Gemini with all images + context
4. Validates the response against allowed values
"""

import asyncio
from pydantic import ValidationError

from models import (
    ClaimInput, UserHistory, EvidenceRequirement, GeminiAnalysisResult,
    ALL_RISK_FLAGS, ALL_ISSUE_TYPES, ALL_SEVERITIES, ALL_CLAIM_STATUSES,
    OBJECT_PARTS,
)
from gemini_client import GeminiClient, create_image_part
from image_validator import validate_claim_images, get_image_bytes, get_image_mime_type
from prompts import build_user_prompt, get_system_prompt
from parsers import get_applicable_requirements


def _clamp_to_allowed(value: str, allowed: list[str], default: str = "unknown") -> str:
    """Ensure a value is in the allowed list, fallback to default."""
    return value if value in allowed else default


def _clamp_risk_flags(flags: list[str]) -> list[str]:
    """Filter risk flags to only allowed values."""
    valid = [f for f in flags if f in ALL_RISK_FLAGS]
    return valid if valid else ["none"]


def _validate_gemini_response(raw: dict, claim_object: str) -> GeminiAnalysisResult:
    """Validate and clamp Gemini's response to allowed values."""
    # Clamp issue_type
    raw["issue_type"] = _clamp_to_allowed(
        raw.get("issue_type", "unknown"), ALL_ISSUE_TYPES
    )
    
    # Clamp object_part to the right set for this claim_object
    valid_parts = OBJECT_PARTS.get(claim_object, [])
    raw["object_part"] = _clamp_to_allowed(
        raw.get("object_part", "unknown"), valid_parts
    )
    
    # Clamp claim_status
    raw["claim_status"] = _clamp_to_allowed(
        raw.get("claim_status", "not_enough_information"), ALL_CLAIM_STATUSES,
        default="not_enough_information"
    )
    
    # Clamp severity
    raw["severity"] = _clamp_to_allowed(
        raw.get("severity", "unknown"), ALL_SEVERITIES
    )
    
    # Clamp risk_flags
    raw_flags = raw.get("risk_flags", [])
    if isinstance(raw_flags, str):
        raw_flags = [f.strip() for f in raw_flags.split(";") if f.strip()]
    raw["risk_flags"] = _clamp_risk_flags(raw_flags)
    
    # Clamp supporting_image_ids
    raw_ids = raw.get("supporting_image_ids", [])
    if isinstance(raw_ids, str):
        raw_ids = [i.strip() for i in raw_ids.split(";") if i.strip()]
    raw["supporting_image_ids"] = raw_ids if raw_ids else ["none"]
    
    # Ensure booleans
    raw["evidence_standard_met"] = bool(raw.get("evidence_standard_met", False))
    raw["valid_image"] = bool(raw.get("valid_image", True))
    
    # Ensure strings
    raw.setdefault("evidence_standard_met_reason", "Unable to determine.")
    raw.setdefault("claim_status_justification", "Unable to determine.")
    
    return GeminiAnalysisResult(**raw)


async def analyze_claim(
    claim: ClaimInput,
    history: UserHistory | None,
    requirements: list[EvidenceRequirement],
    client: GeminiClient,
    strategy: str = "few_shot",
    semaphore: asyncio.Semaphore | None = None,
) -> GeminiAnalysisResult:
    """Analyze a single claim with Gemini vision.
    
    Args:
        claim: The claim to analyze
        history: User's claim history (or None)
        requirements: All evidence requirements
        client: GeminiClient instance
        strategy: "direct" or "few_shot"
        semaphore: Concurrency limiter
        
    Returns:
        Validated GeminiAnalysisResult
    """
    # Step 1: Validate images locally
    has_valid, valid_paths, local_flags = validate_claim_images(claim.image_paths)
    
    if not has_valid:
        # Short-circuit: no usable images
        return GeminiAnalysisResult(
            evidence_standard_met=False,
            evidence_standard_met_reason="No usable images were submitted or all images failed validation.",
            risk_flags=local_flags if local_flags else ["damage_not_visible"],
            issue_type="unknown",
            object_part="unknown",
            claim_status="not_enough_information",
            claim_status_justification="Cannot evaluate the claim without valid images.",
            supporting_image_ids=["none"],
            valid_image=False,
            severity="unknown",
        )
    
    # Step 2: Load image bytes for valid images
    image_parts = []
    for path in valid_paths:
        try:
            img_bytes = get_image_bytes(path)
            mime = get_image_mime_type(path)
            image_parts.append(create_image_part(img_bytes, mime))
        except Exception:
            continue  # Skip unreadable images
    
    if not image_parts:
        return GeminiAnalysisResult(
            evidence_standard_met=False,
            evidence_standard_met_reason="Images could not be loaded.",
            risk_flags=["damage_not_visible"],
            issue_type="unknown",
            object_part="unknown",
            claim_status="not_enough_information",
            claim_status_justification="Cannot evaluate the claim without loadable images.",
            supporting_image_ids=["none"],
            valid_image=False,
            severity="unknown",
        )
    
    # Step 3: Build prompts
    applicable_reqs = get_applicable_requirements(requirements, claim.claim_object)
    system_prompt = get_system_prompt(strategy)
    user_prompt = build_user_prompt(claim, history, applicable_reqs, claim.image_ids)
    
    # Step 4: Call Gemini
    try:
        raw_response = await client.analyze_with_images(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_parts=image_parts,
            semaphore=semaphore,
        )
    except RuntimeError:
        # All retries failed — return safe fallback
        return GeminiAnalysisResult(
            evidence_standard_met=False,
            evidence_standard_met_reason="API call failed after retries.",
            risk_flags=["manual_review_required"],
            issue_type="unknown",
            object_part="unknown",
            claim_status="not_enough_information",
            claim_status_justification="Unable to analyze due to API failure. Manual review required.",
            supporting_image_ids=["none"],
            valid_image=True,
            severity="unknown",
        )
    
    # Step 5: Validate and clamp response
    result = _validate_gemini_response(raw_response, claim.claim_object)
    
    return result
