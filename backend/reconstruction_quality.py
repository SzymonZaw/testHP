"""Quality gates and user-facing diagnostics for Photo 3D Reconstruction."""
from __future__ import annotations

from typing import Any


def validate_inputs(records: list[dict[str, Any]]) -> dict[str, Any]:
    prepared = [r for r in records if r.get("prepared") and r.get("view")]
    registered = [r for r in records if r.get("registration", {}).get("status") == "registered"]
    views = sorted({str(r.get("view")) for r in registered})
    warnings: list[str] = []
    errors: list[str] = []
    if len(prepared) < 2:
        errors.append("At least two prepared views are required.")
    if len(registered) < 2:
        errors.append("At least two views must be successfully registered.")
    if len(views) < 2 and registered:
        errors.append("Registered views must represent at least two different view directions.")
    for r in prepared:
        quality = r.get("quality") or {}
        if float(quality.get("overall", 1.0)) < 0.5:
            warnings.append(f"{r.get('filename', r.get('asset_id'))}: image quality is below the preferred threshold.")
        if r.get("warnings"):
            warnings.extend(f"{r.get('filename', r.get('asset_id'))}: {w}" for w in r["warnings"])
    for r in records:
        reg = r.get("registration") or {}
        if reg.get("status") == "needs-review":
            warnings.append(f"{r.get('filename', r.get('asset_id'))}: registration needs review.")
    return {
        "status": "ready" if not errors else "blocked",
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "prepared_count": len(prepared),
        "registered_count": len(registered),
        "registered_views": views,
        "minimum_views": 2,
    }


def user_message(validation: dict[str, Any]) -> str:
    if validation["errors"]:
        return validation["errors"][0]
    if validation["warnings"]:
        return "Ready to build. Review the photo warnings before continuing."
    return "Ready to build the 3D reconstruction."
