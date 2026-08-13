"""
Main Digital Twin representation.

The DigitalTwin class combines:

- tissue state
- cellular state
- biological age
- risk state
- longitudinal state

It acts as the central biological state representation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .tissue_state import TissueState
from .cell_state import CellState
from .biological_age import BiologicalAge
from .risk_state import RiskState
from .temporal_state import TemporalState
from .twin_update import TwinUpdater


@dataclass
class DigitalTwin:
    """
    Central digital representation of a biological subject.
    """

    subject_id: str

    tissue_state: TissueState = field(
        default_factory=TissueState
    )

    cell_state: CellState = field(
        default_factory=CellState
    )

    biological_age: BiologicalAge = field(
        default_factory=BiologicalAge
    )

    risk_state: RiskState = field(
        default_factory=RiskState
    )

    temporal_state: TemporalState = field(
        default_factory=TemporalState
    )

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def __post_init__(self) -> None:
        """
        Initialize update engine.
        """

        self.updater = TwinUpdater(self)

    def update(
        self,
        observation: Dict[str, Any],
        timepoint: Optional[str] = None,
    ) -> None:
        """
        Update the digital twin from a new observation.
        """

        self.updater.update_from_observation(
            observation,
            timepoint=timepoint,
        )

        self.updated_at = datetime.utcnow().isoformat()

    def snapshot(self) -> Dict[str, Any]:
        """
        Return complete current twin state.
        """

        return {
            "subject_id": self.subject_id,

            "tissue_state":
                self.tissue_state.to_dict(),

            "cell_state":
                self.cell_state.to_dict(),

            "biological_age":
                self.biological_age.to_dict(),

            "risk_state":
                self.risk_state.to_dict(),

            "temporal_state":
                self.temporal_state.to_dict(),

            "metadata": self.metadata,

            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def summary(self) -> Dict[str, Any]:
        """
        Return a compact summary of the biological state.
        """

        return {
            "subject_id": self.subject_id,

            "biological_age":
                self.biological_age.biological_age,

            "age_acceleration":
                self.biological_age.age_acceleration,

            "overall_risk":
                self.risk_state.overall_risk,

            "risk_label":
                self.risk_state.risk_label,

            "tissue_abnormality":
                self.tissue_state.tissue_abnormality_score,

            "cellular_abnormality":
                self.cell_state.cellular_abnormality_score,

            "timepoints":
                len(self.temporal_state.timepoints),

            "updated_at":
                self.updated_at,
        }

    def save(
        self,
        path: str | Path,
    ) -> None:
        """
        Save digital twin to JSON.
        """

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.snapshot(),
                f,
                indent=2,
                ensure_ascii=False,
            )

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "DigitalTwin":
        """
        Load a DigitalTwin from JSON.
        """

        path = Path(path)

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        twin = cls(
            subject_id=data["subject_id"],
            tissue_state=TissueState.from_dict(
                data["tissue_state"]
            ),
            cell_state=CellState.from_dict(
                data["cell_state"]
            ),
            biological_age=BiologicalAge.from_dict(
                data["biological_age"]
            ),
            risk_state=RiskState.from_dict(
                data["risk_state"]
            ),
            temporal_state=TemporalState.from_dict(
                data["temporal_state"]
            ),
            metadata=data.get(
                "metadata",
                {},
            ),
            created_at=data.get(
                "created_at",
                datetime.utcnow().isoformat(),
            ),
            updated_at=data.get(
                "updated_at",
                datetime.utcnow().isoformat(),
            ),
        )

        return twin


if __name__ == "__main__":

    print("=" * 60)
    print("DIGITAL TWIN TEST")
    print("=" * 60)

    twin = DigitalTwin(
        subject_id="TEST_001"
    )

    print("\nInitial state:")
    print(twin.summary())

    observation_t0 = {

        "tissue": {
            "thickness": 1.42,
            "collagen_disorganization": 0.18,
            "inflammation_score": 0.12,
            "tissue_abnormality_score": 0.21,
        },

        "cells": {
            "total_cell_count": 12500,
            "cell_density": 412.5,
            "senescent_cell_fraction": 0.08,
            "abnormal_cell_fraction": 0.03,
            "cellular_abnormality_score": 0.15,
        },

        "biological_age": {
            "chronological_age": 45,
            "biological_age": 47.3,
            "confidence": 0.87,
            "contributions": {
                "tissue": 0.35,
                "cellular": 0.25,
                "rna": 0.20,
                "morphology": 0.15,
                "hand": 0.05,
            },
        },

        "risk": {
            "overall_risk": 0.22,
            "abnormality_risk": 0.17,
            "pathology_risk": 0.12,
            "aging_related_risk": 0.31,
            "progression_risk": 0.18,
            "confidence": 0.82,
        },
    }

    twin.update(
        observation_t0,
        timepoint="T0",
    )

    print("\nAfter T0:")
    print(json.dumps(
        twin.summary(),
        indent=2,
    ))

    observation_t1 = {

        "tissue": {
            "thickness": 1.37,
            "collagen_disorganization": 0.25,
            "inflammation_score": 0.19,
            "tissue_abnormality_score": 0.28,
        },

        "cells": {
            "senescent_cell_fraction": 0.11,
            "abnormal_cell_fraction": 0.05,
            "cellular_abnormality_score": 0.22,
        },

        "biological_age": {
            "biological_age": 49.1,
            "confidence": 0.89,
        },

        "risk": {
            "overall_risk": 0.34,
            "abnormality_risk": 0.24,
            "aging_related_risk": 0.41,
            "progression_risk": 0.29,
            "confidence": 0.84,
        },
    }

    twin.update(
        observation_t1,
        timepoint="T1",
    )

    print("\nAfter T1:")
    print(json.dumps(
        twin.summary(),
        indent=2,
    ))

    print("\nBiological-age trajectory:")

    print(
        json.dumps(
            twin.temporal_state.get_trajectory(
                "biological_age"
            ),
            indent=2,
        )
    )

    print("\nRisk trajectory:")

    print(
        json.dumps(
            twin.temporal_state.get_trajectory(
                "overall_risk"
            ),
            indent=2,
        )
    )

    print("\nRisk change:")

    print(
        twin.temporal_state.calculate_change(
            "overall_risk"
        )
    )

    output_path = Path(
        "outputs/digital_twin/test_twin.json"
    )

    twin.save(output_path)

    print(
        f"\nDigital twin saved to: {output_path}"
    )

    loaded_twin = DigitalTwin.load(
        output_path
    )

    print("\nLoaded twin:")

    print(
        json.dumps(
            loaded_twin.summary(),
            indent=2,
        )
    )

    print("\nModel ready.")