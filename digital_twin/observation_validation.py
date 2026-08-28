"""Validation and quality assessment for digital-twin observations."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from typing import Any, Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome separating hard errors from quality warnings."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completeness: float = 0.0
    confidence: float = 0.0
    checked_fields: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "errors", list(self.errors))
        object.__setattr__(self, "warnings", list(self.warnings))
        object.__setattr__(self, "checked_fields", list(self.checked_fields))
        object.__setattr__(self, "completeness", max(0.0, min(1.0, float(self.completeness))))
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "completeness": self.completeness,
            "confidence": self.confidence,
            "checked_fields": list(self.checked_fields),
        }


def validate_cell_records(records: Iterable[Mapping[str, Any]]) -> ValidationResult:
    """Validate raw cell records before they enter the ingestion pipeline."""
    rows = list(records)
    errors: List[str] = []
    warnings: List[str] = []
    checked: List[str] = []

    ids = [row.get("cell_id") for row in rows]
    checked.append("cell_id")
    if any(not isinstance(value, str) or not value.strip() for value in ids):
        errors.append("every cell record requires a non-empty cell_id")
    if len([value for value in ids if value is not None]) != len(set(value for value in ids if value is not None)):
        errors.append("cell_id values must be unique")

    for field_name in ("observed_at", "confidence", "biological_age"):
        checked.append(field_name)

    for index, row in enumerate(rows):
        timestamp = row.get("observed_at")
        if timestamp is not None:
            try:
                datetime.fromisoformat(str(timestamp))
            except ValueError:
                errors.append(f"record {index}: observed_at is not a valid ISO timestamp")

        confidence = row.get("confidence")
        if confidence is not None:
            try:
                value = float(confidence)
                if not isfinite(value) or not 0.0 <= value <= 1.0:
                    errors.append(f"record {index}: confidence must be between 0 and 1")
            except (TypeError, ValueError):
                errors.append(f"record {index}: confidence must be numeric")
        else:
            warnings.append(f"record {index}: confidence is missing")

        biological_age = row.get("biological_age")
        if biological_age is not None:
            try:
                value = float(biological_age)
                if not isfinite(value) or value < 0:
                    errors.append(f"record {index}: biological_age must be a finite non-negative number")
            except (TypeError, ValueError):
                errors.append(f"record {index}: biological_age must be numeric")

        markers = row.get("health_markers")
        if markers is not None:
            if not isinstance(markers, Mapping):
                errors.append(f"record {index}: health_markers must be a mapping")
            else:
                for marker, marker_value in markers.items():
                    try:
                        numeric = float(marker_value)
                        if not isfinite(numeric):
                            raise ValueError
                    except (TypeError, ValueError):
                        errors.append(f"record {index}: health marker '{marker}' must be numeric")

    if not rows:
        warnings.append("no cell records supplied")
        completeness = 0.0
        confidence = 0.0
    else:
        populated = sum(1 for row in rows if row.get("cell_id") and row.get("observed_at"))
        completeness = populated / len(rows)
        confidence_values = [float(row["confidence"]) for row in rows if row.get("confidence") is not None and _is_number(row["confidence"])]
        confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0

    if completeness < 1.0:
        warnings.append("some records are incomplete")
    if confidence < 0.5:
        warnings.append("overall input confidence is low")

    return ValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        completeness=completeness,
        confidence=confidence,
        checked_fields=checked,
    )


def _is_number(value: Any) -> bool:
    try:
        return isfinite(float(value))
    except (TypeError, ValueError):
        return False
