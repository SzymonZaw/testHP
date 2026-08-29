from __future__ import annotations

"""Unified view of built-in and newly added scientific integrations."""

from .additional_models import ADDITIONAL_MODEL_REGISTRY
from .model_registry import MODEL_REGISTRY, ModelSpec


SCIENTIFIC_INTEGRATIONS: dict[str, ModelSpec] = {
    **MODEL_REGISTRY,
    **ADDITIONAL_MODEL_REGISTRY,
}


def list_integrations(*, tag: str | None = None) -> tuple[ModelSpec, ...]:
    """Return integrations, optionally filtered by capability tag."""
    values = SCIENTIFIC_INTEGRATIONS.values()
    if tag is not None:
        values = (item for item in values if tag in item.tags)
    return tuple(sorted(values, key=lambda item: item.id))


def get_integration(integration_id: str) -> ModelSpec:
    try:
        return SCIENTIFIC_INTEGRATIONS[integration_id]
    except KeyError as exc:
        raise KeyError(f"unknown scientific integration: {integration_id}") from exc
