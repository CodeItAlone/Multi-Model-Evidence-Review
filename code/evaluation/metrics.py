"""Evaluation metrics for comparing predictions against sample_claims.csv labels.

Metrics computed:
  - Per-field exact match accuracy
  - Jaccard similarity for set fields (risk_flags, supporting_image_ids)
  - Per-object-type breakdown
  - Overall summary
"""


def exact_match(predicted: str, expected: str) -> bool:
    """Case-insensitive exact match."""
    return predicted.strip().lower() == expected.strip().lower()


def jaccard_similarity(predicted_str: str, expected_str: str) -> float:
    """Jaccard similarity for semicolon-separated sets (e.g., risk_flags).
    
    J(A, B) = |A ∩ B| / |A ∪ B|
    """
    pred_set = {x.strip().lower() for x in predicted_str.split(";") if x.strip()}
    exp_set = {x.strip().lower() for x in expected_str.split(";") if x.strip()}
    
    if not pred_set and not exp_set:
        return 1.0
    if not pred_set or not exp_set:
        return 0.0
    
    intersection = pred_set & exp_set
    union = pred_set | exp_set
    return len(intersection) / len(union)


def compute_metrics(predictions: list[dict], labels: list[dict]) -> dict:
    """Compute all evaluation metrics.
    
    Args:
        predictions: List of prediction dicts (from output CSV)
        labels: List of label dicts (from sample_claims.csv)
        
    Returns:
        Dict with per-field metrics and overall summary
    """
    assert len(predictions) == len(labels), (
        f"Row count mismatch: {len(predictions)} predictions vs {len(labels)} labels"
    )
    
    n = len(predictions)
    
    # Fields for exact match
    exact_fields = [
        "claim_status", "issue_type", "object_part",
        "evidence_standard_met", "valid_image", "severity",
    ]
    
    # Fields for Jaccard similarity
    jaccard_fields = ["risk_flags", "supporting_image_ids"]
    
    # Compute per-field metrics
    field_metrics = {}
    
    for field in exact_fields:
        matches = sum(
            1 for p, l in zip(predictions, labels)
            if exact_match(p.get(field, ""), l.get(field, ""))
        )
        field_metrics[field] = {
            "accuracy": matches / n if n > 0 else 0.0,
            "correct": matches,
            "total": n,
        }
    
    for field in jaccard_fields:
        scores = [
            jaccard_similarity(p.get(field, ""), l.get(field, ""))
            for p, l in zip(predictions, labels)
        ]
        field_metrics[field] = {
            "avg_jaccard": sum(scores) / n if n > 0 else 0.0,
            "scores": scores,
        }
    
    # Per-object breakdown
    object_breakdown = {}
    for obj_type in ["car", "laptop", "package"]:
        indices = [
            i for i, l in enumerate(labels)
            if l.get("claim_object", "").lower() == obj_type
        ]
        if indices:
            obj_matches = sum(
                1 for i in indices
                if exact_match(predictions[i].get("claim_status", ""), labels[i].get("claim_status", ""))
            )
            object_breakdown[obj_type] = {
                "claim_status_accuracy": obj_matches / len(indices),
                "count": len(indices),
            }
    
    # Overall summary
    overall = {
        "claim_status_accuracy": field_metrics["claim_status"]["accuracy"],
        "issue_type_accuracy": field_metrics["issue_type"]["accuracy"],
        "object_part_accuracy": field_metrics["object_part"]["accuracy"],
        "evidence_standard_met_accuracy": field_metrics["evidence_standard_met"]["accuracy"],
        "severity_accuracy": field_metrics["severity"]["accuracy"],
        "risk_flags_jaccard": field_metrics["risk_flags"]["avg_jaccard"],
        "supporting_image_ids_jaccard": field_metrics["supporting_image_ids"]["avg_jaccard"],
    }
    
    return {
        "overall": overall,
        "per_field": field_metrics,
        "per_object": object_breakdown,
        "total_samples": n,
    }


def print_metrics(metrics: dict):
    """Pretty-print evaluation metrics."""
    print(f"\n{'='*60}")
    print(f"EVALUATION RESULTS ({metrics['total_samples']} samples)")
    print(f"{'='*60}")
    
    print(f"\n📊 Overall Metrics:")
    overall = metrics["overall"]
    for key, value in overall.items():
        print(f"  {key}: {value:.1%}")
    
    print(f"\n📋 Per-Object claim_status Accuracy:")
    for obj, data in metrics.get("per_object", {}).items():
        print(f"  {obj}: {data['claim_status_accuracy']:.1%} ({data['count']} claims)")
    
    print(f"\n📈 Per-Field Detail:")
    for field, data in metrics["per_field"].items():
        if "accuracy" in data:
            print(f"  {field}: {data['accuracy']:.1%} ({data['correct']}/{data['total']})")
        elif "avg_jaccard" in data:
            print(f"  {field}: {data['avg_jaccard']:.1%} (Jaccard avg)")
