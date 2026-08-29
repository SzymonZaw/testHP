"""External scientific integrations for testHP.

Integrations are deliberately optional: testHP owns the evidence contracts,
provenance and orchestration while external projects provide specialised
models or reference data.
"""

from .model_registry import MODEL_REGISTRY, ModelSpec, get_model_spec

__all__ = ["MODEL_REGISTRY", "ModelSpec", "get_model_spec"]
