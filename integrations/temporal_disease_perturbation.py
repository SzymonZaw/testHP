"""Optional research integrations for temporal ageing, disease and perturbation.

Only metadata/adapters are included; external weights and datasets are not vendored.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResearchIntegration:
    name: str
    capability: str
    source: str
    status: str = "experimental-adapter"
    license_note: str = "Verify current repository, model-weight, and dataset terms before use."


MAXTOKI = ResearchIntegration(
    "MaxToki", "temporal single-cell ageing trajectories and perturbation", "https://github.com/"
)
TEDDY = ResearchIntegration(
    "TEDDY", "single-cell disease-state representation", "https://github.com/"
)
KRONOS = ResearchIntegration(
    "KRONOS", "spatial proteomics representation", "https://github.com/"
)
TXPERT = ResearchIntegration(
    "TxPert", "out-of-distribution transcriptomic perturbation prediction", "https://github.com/"
)
CHRIS_CELL = ResearchIntegration(
    "ChrisCell", "interpretable single-cell representation and biological graph", "https://github.com/"
)
SCLONG = ResearchIntegration(
    "scLong", "large-context single-cell and perturbation modelling", "https://github.com/"
)

ALL = (MAXTOKI, TEDDY, KRONOS, TXPERT, CHRIS_CELL, SCLONG)


def get_integration(name: str) -> Optional[ResearchIntegration]:
    return next((x for x in ALL if x.name.casefold() == name.casefold()), None)


def list_integrations() -> list[ResearchIntegration]:
    return list(ALL)
