"""
Digital-twin update engine.

Combines new observations with the existing digital-twin state.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .tissue_state import TissueState
from .cell_state import CellState
from .biological_age import BiologicalAge
from .risk_state import RiskState
from .temporal_state import TemporalState


class TwinUpdater:
    """
    Responsible for updating a digital twin from new observations.
    """

    def __init__(self, twin: Any):
        self.twin = twin

    def update_tissue(
        self,
        values: Dict[str, Any],
        confidence: Optional[float] = None,
    ) -> None:
        """
        Update tissue state.
        """

        if not hasattr(self.twin, "tissue_state"):
            self.twin.tissue_state = TissueState()

        self.twin.tissue_state.update(
            values,
            confidence=confidence,
        )

    def update_cells(
        self,
        values: Dict[str, Any],
        confidence: Optional[float] = None,
    ) -> None:
        """
        Update cellular state.
        """

        if not hasattr(self.twin, "cell_state"):
            self.twin.cell_state = CellState()

        self.twin.cell_state.update(
            values,
            confidence=confidence,
        )

    def update_biological_age(
        self,
        biological_age: Optional[float] = None,
        chronological_age: Optional[float] = None,
        confidence: Optional[float] = None,
        contributions: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Update biological age.
        """

        if not hasattr(self.twin, "biological_age"):
            self.twin.biological_age = BiologicalAge()

        self.twin.biological_age.update(
            biological_age=biological_age,
            chronological_age=chronological_age,
            confidence=confidence,
            contributions=contributions,
        )

    def update_risk(
        self,
        overall_risk: Optional[float] = None,
        confidence: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """
        Update risk state.
        """

        if not hasattr(self.twin, "risk_state"):
            self.twin.risk_state = RiskState()

        self.twin.risk_state.update(
            overall_risk=overall_risk,
            confidence=confidence,
            **kwargs,
        )

    def add_timepoint(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add current twin state to longitudinal history.
        """

        if not hasattr(self.twin, "temporal_state"):
            self.twin.temporal_state = TemporalState()

        biological_age = getattr(
            self.twin.biological_age,
            "biological_age",
            None,
        )

        overall_risk = getattr(
            self.twin.risk_state,
            "overall_risk",
            None,
        )

        tissue_state = self.twin.tissue_state.to_dict()
        cell_state = self.twin.cell_state.to_dict()

        self.twin.temporal_state.add_timepoint(
            name=name,
            biological_age=biological_age,
            overall_risk=overall_risk,
            tissue_state=tissue_state,
            cell_state=cell_state,
            metadata=metadata,
        )

    def update_from_observation(
        self,
        observation: Dict[str, Any],
        timepoint: Optional[str] = None,
    ) -> None:
        """
        Update the twin from a combined observation dictionary.

        Expected structure:

        {
            "tissue": {...},
            "cells": {...},
            "biological_age": {...},
            "risk": {...}
        }
        """

        tissue = observation.get("tissue")

        if tissue:
            self.update_tissue(tissue)

        cells = observation.get("cells")

        if cells:
            self.update_cells(cells)

        age = observation.get("biological_age")

        if age:

            self.update_biological_age(
                biological_age=age.get("biological_age"),
                chronological_age=age.get("chronological_age"),
                confidence=age.get("confidence"),
                contributions=age.get("contributions"),
            )

        risk = observation.get("risk")

        if risk:

            risk_data = dict(risk)

            overall_risk = risk_data.pop(
                "overall_risk",
                None,
            )

            confidence = risk_data.pop(
                "confidence",
                None,
            )

            self.update_risk(
                overall_risk=overall_risk,
                confidence=confidence,
                **risk_data,
            )

        if timepoint:
            self.add_timepoint(timepoint)