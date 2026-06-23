from multimodal_evidence.retrieval.search import retrieve_evidence
from multimodal_evidence.ranking.ranker import rank_evidence
from multimodal_evidence.verification.verifier import verify_claim

__version__ = "0.1.0"

__all__ = [
    "retrieve_evidence",
    "rank_evidence",
    "verify_claim",
]
