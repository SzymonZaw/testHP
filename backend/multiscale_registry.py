from __future__ import annotations

from dataclasses import asdict
from typing import Any

from psycopg.types.json import Json

# ... existing module content retained ...


def _json(value: Any) -> Any:
    """Adapt dataclass/dict/list JSON values for psycopg JSONB parameters."""
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return Json(value)
