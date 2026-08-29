"""Research integrations for multiscale, multimodal and virtual-cell modelling.

Metadata/adapters only: external weights and datasets are intentionally not vendored.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ResearchIntegration:
    name: str
    capability: str
    source: str
    status: str = "research-watch"
    license_note: str = "Verify current code, model-weight, and dataset terms before use."

TERRA = ResearchIntegration("TERRA", "gene-cell-neighborhood spatial representation", "https://github.com/")
CAPTAIN = ResearchIntegration("CAPTAIN", "single-cell RNA + protein multimodal representation", "https://github.com/")
STACK = ResearchIntegration("Stack", "in-context single-cell perturbation prediction", "https://github.com/")
PERTURB_SAPIENS = ResearchIntegration("Perturb Sapiens", "virtual-cell perturbation/reference data", "https://arcinstitute.org/")
VIRTUES = ResearchIntegration("VirTues", "spatial proteomics cell-niche-tissue representation", "https://github.com/")
DEEPSPOT2CELL = ResearchIntegration("DeepSpot2Cell", "H&E plus cell segmentation to virtual transcriptomic profile", "https://github.com/")
CELLVIT_PLUS_PLUS = ResearchIntegration("CellViT++", "efficient cell segmentation and classification", "https://github.com/")
INSTANSEG = ResearchIntegration("InstanSeg", "cell/nucleus instance segmentation", "https://github.com/")
STAGE = ResearchIntegration("stAge", "spatial transcriptomics biological-age analysis", "https://github.com/")
VIRTUALCELL = ResearchIntegration("VirtualCell", "multimodal virtual-cell research framework", "https://github.com/")

ALL = (TERRA, CAPTAIN, STACK, PERTURB_SAPIENS, VIRTUES, DEEPSPOT2CELL, CELLVIT_PLUS_PLUS, INSTANSEG, STAGE, VIRTUALCELL)

def get_integration(name: str) -> Optional[ResearchIntegration]:
    return next((x for x in ALL if x.name.casefold() == name.casefold()), None)

def list_integrations() -> list[ResearchIntegration]:
    return list(ALL)
