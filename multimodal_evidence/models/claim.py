"""Pydantic data models and enums for the Multi-Modal Evidence Review SDK.

All allowed values are defined here as enums/literals to ensure
Gemini responses are validated against the problem statement constraints.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums — Allowed Values (from problem_statement.md)
# =============================================================================

class ClaimObject(str, Enum):
    CAR = "car"
    LAPTOP = "laptop"
    PACKAGE = "package"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class IssueType(str, Enum):
    DENT = "dent"
    SCRATCH = "scratch"
    CRACK = "crack"
    GLASS_SHATTER = "glass_shatter"
    BROKEN_PART = "broken_part"
    MISSING_PART = "missing_part"
    TORN_PACKAGING = "torn_packaging"
    CRUSHED_PACKAGING = "crushed_packaging"
    WATER_DAMAGE = "water_damage"
    STAIN = "stain"
    NONE = "none"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class RiskFlag(str, Enum):
    NONE = "none"
    BLURRY_IMAGE = "blurry_image"
    CROPPED_OR_OBSTRUCTED = "cropped_or_obstructed"
    LOW_LIGHT_OR_GLARE = "low_light_or_glare"
    WRONG_ANGLE = "wrong_angle"
    WRONG_OBJECT = "wrong_object"
    WRONG_OBJECT_PART = "wrong_object_part"
    DAMAGE_NOT_VISIBLE = "damage_not_visible"
    CLAIM_MISMATCH = "claim_mismatch"
    POSSIBLE_MANIPULATION = "possible_manipulation"
    NON_ORIGINAL_IMAGE = "non_original_image"
    TEXT_INSTRUCTION_PRESENT = "text_instruction_present"
    USER_HISTORY_RISK = "user_history_risk"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


# Object-part mappings per claim_object
CAR_PARTS = [
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender", "quarter_panel",
    "body", "unknown",
]

LAPTOP_PARTS = [
    "screen", "keyboard", "trackpad", "hinge", "lid",
    "corner", "port", "base", "body", "unknown",
]

PACKAGE_PARTS = [
    "box", "package_corner", "package_side", "seal",
    "label", "contents", "item", "unknown",
]

OBJECT_PARTS = {
    "car": CAR_PARTS,
    "laptop": LAPTOP_PARTS,
    "package": PACKAGE_PARTS,
}

ALL_RISK_FLAGS = [flag.value for flag in RiskFlag]
ALL_ISSUE_TYPES = [it.value for it in IssueType]
ALL_SEVERITIES = [s.value for s in Severity]
ALL_CLAIM_STATUSES = [cs.value for cs in ClaimStatus]


# =============================================================================
# Input Models
# =============================================================================

class ClaimInput(BaseModel):
    """A single row from claims.csv or sample_claims.csv (input columns only)."""
    user_id: str
    image_paths: list[str]  # Split from semicolon-delimited string
    user_claim: str
    claim_object: str

    @property
    def image_ids(self) -> list[str]:
        """Extract image IDs (filename without extension) from paths."""
        from pathlib import Path
        return [Path(p).stem for p in self.image_paths]


class UserHistory(BaseModel):
    """A single row from user_history.csv."""
    user_id: str
    past_claim_count: int
    accept_claim: int
    manual_review_claim: int
    rejected_claim: int
    last_90_days_claim_count: int
    history_flags: str  # semicolon-separated or "none"
    history_summary: str

    @property
    def has_risk(self) -> bool:
        return self.history_flags != "none"

    @property
    def flag_list(self) -> list[str]:
        if self.history_flags == "none":
            return []
        return [f.strip() for f in self.history_flags.split(";") if f.strip()]


class EvidenceRequirement(BaseModel):
    """A single row from evidence_requirements.csv."""
    requirement_id: str
    claim_object: str  # "car", "laptop", "package", or "all"
    applies_to: str    # Issue family description
    minimum_image_evidence: str


# =============================================================================
# Gemini Response Model (what we expect from the API)
# =============================================================================

class GeminiAnalysisResult(BaseModel):
    """Structured response expected from Gemini vision analysis."""
    evidence_standard_met: bool
    evidence_standard_met_reason: str
    risk_flags: list[str] = Field(default_factory=list)
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: list[str] = Field(default_factory=list)
    valid_image: bool
    severity: str


# =============================================================================
# Output Model
# =============================================================================

class ClaimOutput(BaseModel):
    """Final output row — matches the required 14-column schema exactly."""
    user_id: str
    image_paths: str          # Original semicolon-delimited string
    user_claim: str
    claim_object: str
    evidence_standard_met: str  # "true" or "false"
    evidence_standard_met_reason: str
    risk_flags: str             # Semicolon-separated or "none"
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str   # Semicolon-separated or "none"
    valid_image: str            # "true" or "false"
    severity: str

    @classmethod
    def column_order(cls) -> list[str]:
        """Return columns in the exact required order."""
        return [
            "user_id", "image_paths", "user_claim", "claim_object",
            "evidence_standard_met", "evidence_standard_met_reason",
            "risk_flags", "issue_type", "object_part",
            "claim_status", "claim_status_justification",
            "supporting_image_ids", "valid_image", "severity",
        ]


# =============================================================================
# Sample Claim (labeled — for evaluation)
# =============================================================================

class SampleClaimLabels(BaseModel):
    """Expected output columns from sample_claims.csv (ground truth)."""
    evidence_standard_met: str
    evidence_standard_met_reason: str
    risk_flags: str
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str
    valid_image: str
    severity: str
