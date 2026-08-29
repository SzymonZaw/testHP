from __future__ import annotations

"""Single public contract facade for Digital Twin data.

New integrations should import identity, spatial, evidence and provenance
primitives from this module rather than creating parallel representations.
"""

from dataclasses import asdict
from typing import Any

from .data_foundation import (
    Acquisition,
    DataObject,
    Hand,
    Provenance,
    Quality,
    SpatialReference,
    Subject,
    Timepoint,
    Uncertainty,
)
from .digital_twin_contract import DigitalTwin

CONTRACT_VERSION = "1"


def validate_twin_payload(twin: DigitalTwin) -> dict[str, Any]:
    twin.validate()
    return asdict(twin)


__all__ = [
    "CONTRACT_VERSION", "Acquisition", "DataObject", "DigitalTwin", "Hand",
    "Provenance", "Quality", "SpatialReference", "Subject", "Timepoint",
    "Uncertainty", "validate_twin_payload",
]
