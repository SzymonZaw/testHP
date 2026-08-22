"""Canonical spatial identifiers shared by registry/state APIs.

The UI may use display/ontology aliases such as ``hypothenar-eminence`` while
stored evidence uses the stable contract id ``hypothenar``.  Keep this mapping
small and explicit: canonicalization must never infer a more specific target.
"""
from __future__ import annotations

from typing import Any

ALIASES = {
    "hypothenar-eminence": "hypothenar",
    "thenar-eminence": "thenar",
    "central-palm-region": "central-palm",
}


def canonical_spatial_id(value: Any) -> str:
    raw = str(value or "").strip().strip("/")
    if not raw:
        return "hand"
    parts = [part for part in raw.split("/") if part]
    if not parts:
        return "hand"
    parts = [ALIASES.get(part, part) for part in parts]
    if parts[0] != "hand":
        parts.insert(0, "hand")
    return "/".join(parts)


def spatial_ids_equal(left: Any, right: Any) -> bool:
    return canonical_spatial_id(left) == canonical_spatial_id(right)
