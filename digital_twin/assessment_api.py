"""Transport-neutral API contract for DigitalTwin assessment views.

A web framework can mount ``get_cell_assessment`` at
GET /api/digital-twin/cells/{cell_id}/assessment.
"""
from __future__ import annotations

from typing import Any, Dict


def get_cell_assessment(twin: Any, cell_id: str) -> Dict[str, Any]:
    view = twin.assessment_view(cell_id)
    if view is None:
        return {"error": "cell_not_found", "cell_id": cell_id}
    return {
        "data": view,
        "schema_version": "1.0",
        "resource": "cell_assessment",
    }
