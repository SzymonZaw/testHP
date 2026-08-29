from __future__ import annotations

"""Architecture boundary for the hand Digital Twin.

The backend contract is intentionally small: one aggregate owns identity,
while domain modules provide observations and derived assessments.
"""

from dataclasses import dataclass
from typing import Any

from .digital_twin_contract import DigitalTwin
from .spatial_contract import normalize_spatial_id


@dataclass(frozen=True)
class TwinEnvelope:
    twin: DigitalTwin
    payload: dict[str, Any]

    def validate(self) -> None:
        self.twin.validate()
        spatial_id = self.payload.get("spatial_id")
        if spatial_id is not None:
            normalize_spatial_id(spatial_id)


def canonical_spatial_id(value: str) -> str:
    return normalize_spatial_id(value)
