"""Registry of external cell-type references used by the annotation layer.

The registry stores provenance and intended use only. It deliberately does not
ship external datasets or claim that any reference is clinical ground truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CellTypeReference:
    reference_id: str
    title: str
    modality: str
    tissue: str
    role: str
    url: str
    status: str


REFERENCES: tuple[CellTypeReference, ...] = (
    CellTypeReference(
        reference_id="hsca_2026",
        title="Human Skin Cell Atlas",
        modality="scRNA-seq",
        tissue="skin",
        role="primary_reference",
        url="https://zenodo.org/records/21022952",
        status="reference_candidate",
    ),
    CellTypeReference(
        reference_id="tabula_sapiens",
        title="Tabula Sapiens",
        modality="scRNA-seq",
        tissue="skin_and_multi_organ",
        role="cross_tissue_reference",
        url="https://tabula-sapiens.sf.czbiohub.org/",
        status="reference_candidate",
    ),
    CellTypeReference(
        reference_id="hpa_single_cell_skin",
        title="Human Protein Atlas single-cell skin",
        modality="scRNA-seq",
        tissue="skin",
        role="marker_reference",
        url="https://www.proteinatlas.org/humanproteome/single-cell+type",
        status="secondary_reference",
    ),
    CellTypeReference(
        reference_id="popv_tabula_sapiens_skin",
        title="popV Tabula Sapiens Skin",
        modality="scRNA-seq",
        tissue="skin",
        role="external_baseline_model",
        url="https://huggingface.co/popV/tabula_sapiens_Skin",
        status="external_model_candidate",
    ),
)


def list_references(*, tissue: str | None = None, modality: str | None = None) -> list[dict[str, Any]]:
    """Return reference metadata filtered by tissue and/or modality."""
    result = []
    for reference in REFERENCES:
        if tissue is not None and tissue.lower() not in reference.tissue.lower():
            continue
        if modality is not None and modality.lower() != reference.modality.lower():
            continue
        result.append(asdict(reference))
    return result


def reference_status(reference_id: str) -> str:
    """Return the registry status for one reference, or ``unknown``."""
    for reference in REFERENCES:
        if reference.reference_id == reference_id:
            return reference.status
    return "unknown"
