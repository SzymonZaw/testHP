"""Canonical spatial scope semantics for Digital Twin observations.

A scope is defined by the selected spatial_id and the recursive parent/child
hierarchy. Biological level is never part of spatial identity: it is a separate
filter/dimension applied after the spatial scope has been resolved.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def canonical_parent_id(spatial_id: str) -> str | None:
    """Return the canonical parent for a hand spatial id.

    Top-level hand regions are siblings. In particular, ``hand/thumb`` is not a
    child of ``hand/palm``. Deeper nodes inherit from their immediate path parent.
    """
    parts = [part for part in str(spatial_id or "").strip("/").split("/") if part]
    if not parts or parts[0] != "hand" or len(parts) == 1:
        return None
    if len(parts) == 2:
        return "hand"
    return "/".join(parts[:-1])


def location_parent(item: Mapping[str, Any], spatial_id: str) -> str | None:
    """Resolve a location's parent from its spatial identity.

    ``spatial_id`` is the authoritative spatial identity. A stale or incorrect
    persisted ``parent_id`` must not be able to move an observation into a
    sibling's subtree. ``parent_id`` remains compatibility metadata, but the
    canonical hand path defines traversal.
    """
    canonical = canonical_parent_id(spatial_id)
    if canonical is not None or str(spatial_id or "").strip("/") == "hand":
        return canonical
    explicit = item.get("parent_id")
    return str(explicit) if explicit else None


def build_parent_map(items: Iterable[Mapping[str, Any]]) -> dict[str, str | None]:
    parents: dict[str, str | None] = {}
    for item in items:
        spatial_id = str(item.get("spatial_id") or "hand")
        parents[spatial_id] = location_parent(item, spatial_id)
    # Materialize canonical ancestors so recursive traversal remains stable even
    # when no observation exists directly on an intermediate node.
    pending = list(parents)
    while pending:
        spatial_id = pending.pop()
        parent = parents.get(spatial_id)
        if not parent or parent in parents:
            continue
        parents[parent] = canonical_parent_id(parent)
        pending.append(parent)
    return parents


def scope_ids(selected_spatial_id: str, parent_map: Mapping[str, str | None], *, include_descendants: bool) -> set[str]:
    selected = str(selected_spatial_id or "hand").strip("/") or "hand"
    scope = {selected}
    if not include_descendants:
        return scope
    changed = True
    while changed:
        changed = False
        for spatial_id, parent_id in parent_map.items():
            if parent_id in scope and spatial_id not in scope:
                scope.add(spatial_id)
                changed = True
    return scope


def observation_in_scope(item: Mapping[str, Any], selected_spatial_id: str, parent_map: Mapping[str, str | None], *, include_descendants: bool) -> bool:
    spatial_id = str(item.get("spatial_id") or "hand").strip("/") or "hand"
    return spatial_id in scope_ids(selected_spatial_id, parent_map, include_descendants=include_descendants)


def split_spatial_scope(items: Iterable[Mapping[str, Any]], selected_spatial_id: str, *, include_descendants: bool) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    materialized = list(items)
    parents = build_parent_map(materialized)
    scope = scope_ids(selected_spatial_id, parents, include_descendants=include_descendants)
    selected = str(selected_spatial_id or "hand").strip("/") or "hand"
    direct: list[Mapping[str, Any]] = []
    descendants: list[Mapping[str, Any]] = []
    for item in materialized:
        spatial_id = str(item.get("spatial_id") or "hand").strip("/") or "hand"
        if spatial_id == selected:
            direct.append(item)
        elif spatial_id in scope:
            descendants.append(item)
    return direct, descendants
