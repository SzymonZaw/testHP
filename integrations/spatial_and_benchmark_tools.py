"""Optional research integrations discovered for spatial/multimodal benchmarking.

Only lightweight metadata is kept here. External repositories, weights and large datasets
are not vendored into testHP.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResearchTool:
    name: str
    capability: str
    source: str
    license_note: str
    category: str


TOOLS = (
    ResearchTool("Baysor", "probabilistic spatial transcriptomics cell segmentation", "https://github.com/kharchenkolab/Baysor", "Verify current repository/data terms before redistribution.", "segmentation"),
    ResearchTool("ComSeg", "cell segmentation from spatial transcript points", "https://github.com/fish-quant/ComSeg", "Verify current repository/data terms before redistribution.", "segmentation"),
    ResearchTool("DISSECT", "joint cytology and spatial transcriptomics analysis", "https://github.com/", "Verify official repository and model/data terms before use.", "multimodal"),
    ResearchTool("spateo", "spatial and spatiotemporal modeling, reconstruction and analysis", "https://github.com/aristoteleo/spateo-release", "Verify current repository/data terms before redistribution.", "spatial"),
    ResearchTool("DeepLIIF", "IHC-to-multiplex inference, cell segmentation and protein quantification", "https://github.com/nadeemlab/DeepLIIF", "Non-commercial academic use; do not assume commercial rights.", "pathology"),
    ResearchTool("NaVis", "interactive H&E and spatial transcriptomics visualization", "https://github.com/Izzilab/NaVis", "Verify current repository/data terms before redistribution.", "viewer"),
    ResearchTool("Pantheon-LLM", "unified single-cell foundation-model interface", "https://github.com/aristoteleo/pantheon-llm", "MIT repository; verify each model's separate weights/license terms.", "runtime"),
    ResearchTool("scFM-Bench", "single-cell foundation-model benchmarking", "https://github.com/wujialu/scFM-Bench", "Use benchmark datasets/results under their stated terms.", "benchmark"),
    ResearchTool("scDrugPerturb-Bench", "single-cell perturbation and mechanism-fidelity benchmarking", "https://github.com/mindflow-cn/scDrugPerturb-Bench", "Use benchmark datasets/results under their stated terms.", "benchmark"),
    ResearchTool("DeepSpot", "virtual spatial transcriptomics from H&E, including single-cell resolution", "https://github.com/ratschlab/DeepSpot", "Verify model/data license before commercial use.", "spatial"),
)


def get_tool(name: str) -> Optional[ResearchTool]:
    key = name.casefold()
    return next((tool for tool in TOOLS if tool.name.casefold() == key), None)


def list_tools(category: Optional[str] = None) -> list[ResearchTool]:
    if category is None:
        return list(TOOLS)
    key = category.casefold()
    return [tool for tool in TOOLS if tool.category.casefold() == key]
