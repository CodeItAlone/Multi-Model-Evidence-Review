"""CSV parsers for claims, user history, and evidence requirements.

All parsers return typed Pydantic models for downstream safety.
History and requirements are indexed as dicts for O(1) lookup per claim.
"""

import csv
from pathlib import Path

from models import ClaimInput, UserHistory, EvidenceRequirement, SampleClaimLabels


def parse_claims(csv_path: Path) -> list[ClaimInput]:
    """Parse claims.csv or sample_claims.csv → list of ClaimInput.
    
    Only reads the 4 input columns. Splits semicolon-delimited image_paths.
    """
    claims = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_paths = [p.strip() for p in row["image_paths"].split(";") if p.strip()]
            claims.append(ClaimInput(
                user_id=row["user_id"].strip(),
                image_paths=image_paths,
                user_claim=row["user_claim"].strip(),
                claim_object=row["claim_object"].strip(),
            ))
    return claims


def parse_sample_labels(csv_path: Path) -> list[SampleClaimLabels]:
    """Parse sample_claims.csv → list of SampleClaimLabels (ground truth).
    
    Reads only the output columns for evaluation comparison.
    """
    labels = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels.append(SampleClaimLabels(
                evidence_standard_met=row["evidence_standard_met"].strip(),
                evidence_standard_met_reason=row["evidence_standard_met_reason"].strip(),
                risk_flags=row["risk_flags"].strip(),
                issue_type=row["issue_type"].strip(),
                object_part=row["object_part"].strip(),
                claim_status=row["claim_status"].strip(),
                claim_status_justification=row["claim_status_justification"].strip(),
                supporting_image_ids=row["supporting_image_ids"].strip(),
                valid_image=row["valid_image"].strip(),
                severity=row["severity"].strip(),
            ))
    return labels


def parse_user_history(csv_path: Path) -> dict[str, UserHistory]:
    """Parse user_history.csv → dict keyed by user_id for O(1) lookup."""
    history_map = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = UserHistory(
                user_id=row["user_id"].strip(),
                past_claim_count=int(row["past_claim_count"]),
                accept_claim=int(row["accept_claim"]),
                manual_review_claim=int(row["manual_review_claim"]),
                rejected_claim=int(row["rejected_claim"]),
                last_90_days_claim_count=int(row["last_90_days_claim_count"]),
                history_flags=row["history_flags"].strip(),
                history_summary=row["history_summary"].strip(),
            )
            history_map[user.user_id] = user
    return history_map


def parse_evidence_requirements(csv_path: Path) -> list[EvidenceRequirement]:
    """Parse evidence_requirements.csv → list of EvidenceRequirement.
    
    Requirements are matched by claim_object + issue family at runtime.
    """
    requirements = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            requirements.append(EvidenceRequirement(
                requirement_id=row["requirement_id"].strip(),
                claim_object=row["claim_object"].strip(),
                applies_to=row["applies_to"].strip(),
                minimum_image_evidence=row["minimum_image_evidence"].strip(),
            ))
    return requirements


def get_applicable_requirements(
    requirements: list[EvidenceRequirement],
    claim_object: str,
) -> list[EvidenceRequirement]:
    """Filter requirements applicable to a specific claim_object.
    
    Returns requirements where claim_object matches OR is "all".
    """
    return [
        req for req in requirements
        if req.claim_object == claim_object or req.claim_object == "all"
    ]
