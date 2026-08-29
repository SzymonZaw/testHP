"""User-facing analysis gate for the digital-twin pipeline.

This module is intentionally small: ingestion/QC remains responsible for
accepting/rejecting files, while capability resolution decides what analyses
may run from the accepted modalities. No missing measurement is inferred.
"""
from __future__ import annotations

from typing import Any

from .user_capability_resolver_v1 import resolve_capabilities


SUPPORTED_KINDS = {
    "hand_images",
    "hand_video",
    "hand_3d",
    "tissue_wsi",
    "microscopy",
    "single_cell_rna",
    "genomics",
    "proteomics",
    "epigenetics",
}


def _structural_input_ids(package: dict[str, Any]) -> set[str]:
    """Return input kinds that are structurally usable.

    This is deliberately not a scientific QC step. Projects can pass their
    own QC result through ``accepted_kinds`` when available.
    """
    accepted: set[str] = set()
    for item in package.get("inputs", []):
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        input_id = item.get("input_id")
        if kind in SUPPORTED_KINDS and input_id:
            accepted.add(kind)
    return accepted


def build_user_analysis_report(
    package: dict[str, Any],
    *,
    accepted_kinds: set[str] | None = None,
) -> dict[str, Any]:
    """Build a safe, user-facing analysis report.

    ``accepted_kinds`` should be supplied by the real ingestion/QC layer.
    Without it, only structurally valid input records are considered; this
    does not claim that the underlying measurements are scientifically valid.
    """
    kinds = accepted_kinds if accepted_kinds is not None else _structural_input_ids(package)
    result = resolve_capabilities(package, accepted_kinds=kinds)

    available = [c for c in result["capabilities"] if c["status"] == "available"]
    partial = [c for c in result["capabilities"] if c["status"] == "partial"]
    unavailable = [c for c in result["capabilities"] if c["status"] == "unavailable"]

    return {
        "status": "ready" if available else "no_supported_analysis",
        "input_kinds": sorted(kinds),
        "available_analyses": available,
        "partial_analyses": partial,
        "unavailable_analyses": unavailable,
        "evidence_coverage": result["evidence_coverage"],
        "limitations": result["limitations"],
        "safety": {
            "missing_data_is_not_negative_finding": True,
            "clinical_decision": "not_supported_by_this_layer",
        },
    }


def format_user_summary(report: dict[str, Any]) -> str:
    """Render a compact summary suitable for an API/UI response."""
    lines = ["INPUT", "✓ " + "\n✓ ".join(report["input_kinds"]) if report["input_kinds"] else "— none"]
    lines += ["", "AVAILABLE ANALYSES"]
    lines += [f"✓ {x['capability_id']}" for x in report["available_analyses"]] or ["— none"]
    lines += ["", "PARTIAL ANALYSES"]
    lines += [f"~ {x['capability_id']}: {'; '.join(x['blocking_reasons'])}" for x in report["partial_analyses"]] or ["— none"]
    lines += ["", "UNAVAILABLE ANALYSES"]
    lines += [f"— {x['capability_id']}" for x in report["unavailable_analyses"]] or ["— none"]
    lines += ["", "LIMITATIONS"]
    lines += [f"• {x}" for x in report["limitations"]]
    return "\n".join(lines)
