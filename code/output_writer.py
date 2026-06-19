"""Output writer — writes ClaimOutput rows to CSV with exact schema."""

import csv
from pathlib import Path

from models import ClaimOutput


def write_output_csv(outputs: list[ClaimOutput], output_path: Path):
    """Write predictions to output.csv with the exact required column order.
    
    Uses csv.writer with proper quoting to handle commas in text fields.
    """
    columns = ClaimOutput.column_order()
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for output in outputs:
            writer.writerow(output.model_dump())


def validate_output_csv(output_path: Path, expected_rows: int) -> list[str]:
    """Validate the output CSV against requirements.
    
    Returns list of error messages (empty = valid).
    """
    errors = []
    expected_columns = ClaimOutput.column_order()
    
    if not output_path.exists():
        errors.append(f"Output file not found: {output_path}")
        return errors
    
    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Check columns
        if reader.fieldnames != expected_columns:
            errors.append(
                f"Column mismatch. Expected: {expected_columns}, Got: {reader.fieldnames}"
            )
        
        # Check row count and values
        row_count = 0
        valid_statuses = {"supported", "contradicted", "not_enough_information"}
        valid_severities = {"none", "low", "medium", "high", "unknown"}
        
        for i, row in enumerate(reader, start=1):
            row_count += 1
            
            # Check claim_status
            if row.get("claim_status") not in valid_statuses:
                errors.append(f"Row {i}: Invalid claim_status '{row.get('claim_status')}'")
            
            # Check severity
            if row.get("severity") not in valid_severities:
                errors.append(f"Row {i}: Invalid severity '{row.get('severity')}'")
            
            # Check evidence_standard_met
            if row.get("evidence_standard_met") not in ("true", "false"):
                errors.append(f"Row {i}: Invalid evidence_standard_met '{row.get('evidence_standard_met')}'")
            
            # Check valid_image
            if row.get("valid_image") not in ("true", "false"):
                errors.append(f"Row {i}: Invalid valid_image '{row.get('valid_image')}'")
            
            # Check no empty required fields
            for col in expected_columns:
                if not row.get(col, "").strip():
                    errors.append(f"Row {i}: Empty value in column '{col}'")
        
        if row_count != expected_rows:
            errors.append(f"Row count mismatch. Expected: {expected_rows}, Got: {row_count}")
    
    return errors
