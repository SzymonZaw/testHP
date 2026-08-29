"""Optional adapters for ageing and multimodal research models.

These adapters intentionally avoid importing heavyweight dependencies at module import
 time. Model weights are never bundled with testHP.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ResearchIntegration:
    name: str
    capability: str
    source: str
    license_note: str
    status: str = "adapter"


SCAGECLOCK = ResearchIntegration(
    name="scAgeClock",
    capability="single-cell biological age estimation",
    source="https://github.com/gangcai/scageclock",
    license_note="Verify code/weight terms before redistribution or commercial use.",
)

SPATIAL_AGING_CLOCK = ResearchIntegration(
    name="Spatial Aging Clocks",
    capability="spatial biological-age estimation",
    source="https://github.com/sunericd/SpatialAgingClock",
    license_note="Verify repository and pretrained-weight terms before redistribution.",
)

SUBCELL = ResearchIntegration(
    name="SubCell",
    capability="subcellular image representation and protein localization",
    source="https://github.com/CellProfiling/SubCellPortable",
    license_note="Repository is MIT; check any separately distributed weights/data.",
)

SCICORE_OMICS = ResearchIntegration(
    name="SciCore-Omics",
    capability="histology + spatial transcriptomics + biological language reasoning",
    source="https://github.com/OpenBMB/Scicore-Omics",
    license_note="Apache-2.0 code; verify model/data-specific terms.",
)


ALL = (SCAGECLOCK, SPATIAL_AGING_CLOCK, SUBCELL, SCICORE_OMICS)


def get_integration(name: str) -> Optional[ResearchIntegration]:
    """Return a registered research integration by case-insensitive name."""
    key = name.casefold()
    return next((item for item in ALL if item.name.casefold() == key), None)


def list_integrations() -> list[ResearchIntegration]:
    """Return all optional ageing/multimodal research integrations."""
    return list(ALL)


def unavailable_without_optional_dependency(name: str) -> dict[str, Any]:
    """Describe a model that is registered but not installed locally."""
    item = get_integration(name)
    if item is None:
        raise KeyError(f"Unknown integration: {name}")
    return {
        "name": item.name,
        "capability": item.capability,
        "status": "optional_dependency_not_installed",
        "source": item.source,
        "license_note": item.license_note,
    }
