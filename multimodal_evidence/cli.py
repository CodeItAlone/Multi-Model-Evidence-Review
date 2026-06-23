"""Command-line interface (CLI) for the Multimodal Evidence SDK.

Supports verification, requirements/factual searching, and risk ranking.
"""

import argparse
import json
import sys
from pathlib import Path

from multimodal_evidence.verification.verifier import verify_claim
from multimodal_evidence.retrieval.search import parse_evidence_requirements, get_applicable_requirements
from multimodal_evidence.ranking.ranker import rank_evidence


def verify_command(args):
    """Factual or damage claim verification via CLI."""
    images_list = None
    if args.images:
        images_list = [img.strip() for img in args.images.split(";") if img.strip()]
        
    try:
        result = verify_claim(
            claim_text=args.claim,
            images=images_list,
            claim_object=args.object,
            strategy=args.strategy,
            api_key=args.api_key,
            model=args.model
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during claim verification: {e}", file=sys.stderr)
        sys.exit(1)


def search_command(args):
    """Retrieve and display evidence requirements or factual details."""
    query = args.query.lower().strip()
    
    # Check if query matches standard claim objects
    if query in ("car", "laptop", "package", "all"):
        # Load local requirements if they exist in standard path
        requirements_path = Path("dataset/evidence_requirements.csv")
        if requirements_path.exists():
            try:
                reqs = parse_evidence_requirements(requirements_path)
                filtered = get_applicable_requirements(reqs, query)
                print(json.dumps([r.model_dump() for r in filtered], indent=2))
                return
            except Exception as e:
                print(f"Error reading local requirements file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Requirements database not found at dataset/evidence_requirements.csv", file=sys.stderr)
            sys.exit(1)
            
    # Generic query factual check fallback using Gemini
    try:
        result = verify_claim(
            claim_text=f"Search facts and retrieve evidence about: {args.query}",
            claim_object="all",
            api_key=args.api_key,
            model=args.model
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during factual search: {e}", file=sys.stderr)
        sys.exit(1)


def rank_command(args):
    """Aggregates and overrides findings from an input JSON file."""
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: JSON file not found at {json_path}", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        claim_input = data.get("claim_input")
        gemini_result = data.get("gemini_result")
        history = data.get("history", None)
        
        if not claim_input or not gemini_result:
            print("Error: JSON must contain 'claim_input' and 'gemini_result' objects", file=sys.stderr)
            sys.exit(1)
            
        output = rank_evidence(
            claim_input=claim_input,
            gemini_result=gemini_result,
            history=history
        )
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error during evidence ranking: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="evidence",
        description="CLI utility for Multimodal Evidence Verification and Review."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a claim statement or damage claim conversation.")
    verify_parser.add_argument("claim", type=str, help="Claim statement or dialogue to verify.")
    verify_parser.add_argument("--images", type=str, default="", help="Semicolon-separated path to images.")
    verify_parser.add_argument("--object", type=str, default="all", choices=["car", "laptop", "package", "all"], help="Claim object class.")
    verify_parser.add_argument("--strategy", type=str, default="few_shot", choices=["direct", "few_shot"], help="Prompt strategy.")
    verify_parser.add_argument("--api-key", type=str, default="", help="Optional Gemini API key.")
    verify_parser.add_argument("--model", type=str, default="", help="Optional Gemini model override.")
    verify_parser.set_defaults(func=verify_command)
    
    # 2. search command
    search_parser = subparsers.add_parser("search", help="Search requirements or fact-check factual details.")
    search_parser.add_argument("query", type=str, help="Search query or fact to search/retrieve.")
    search_parser.add_argument("--api-key", type=str, default="", help="Optional Gemini API key.")
    search_parser.add_argument("--model", type=str, default="", help="Optional Gemini model override.")
    search_parser.set_defaults(func=search_command)
    
    # 3. rank command
    rank_parser = subparsers.add_parser("rank", help="Apply decision guardrails and rank evidence from a JSON payload.")
    rank_parser.add_argument("json_file", type=str, help="Path to JSON payload containing claim_input and gemini_result.")
    rank_parser.set_defaults(func=rank_command)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
