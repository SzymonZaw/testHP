from __future__ import annotations

import pytest

from backend.anatomy_foundation import AnatomicalStructure, CellObject, Geometry, HandCoordinateSystem, TissueRegion
from backend.biological_state import InterpretationEvidence
from backend.data_foundation import Provenance, SpatialReference
from backend.evidence_attachment import EvidenceAttachment
from backend.multiscale_analysis_service import register_cell_research_outputs
from backend.multiscale_registry import MultiscaleRegistry


def _chain():
    registry = MultiscaleRegistry()
    frame = HandCoordinateSystem("frame", "s1", "h1", "T0")
    registry.add_coordinate_system(frame)
    sr = SpatialReference("frame", "registered", transform={"type": "identity", "version": "1"})
    anatomy = AnatomicalStructure("a", "s1", "h1", "T0", "skin", Geometry("g", "volume", "frame"), ("src",), sr, Provenance())
    tissue = TissueRegion("t", "a", "s1", "h1", "T0", "epidermis", Geometry("tg", "segmentation", "frame"), ("src",), sr, Provenance())
    cell = CellObject("c", "t", "s1", "h1", "T0", {"x": 1}, "keratinocyte", {}, {}, {}, (), ("src",), sr, Provenance())
    registry.add_anatomy(anatomy)
    registry.add_tissue(tissue)
    registry.add_cell(cell)
    evidence = InterpretationEvidence("e", ("src",), "morphology", {"area": 1}, 0.9, Provenance())
    attachment = EvidenceAttachment("att", "e", "src", "s1", "h1", "T0", "c", "cell", "histology", sr, Provenance())
    return registry, cell, attachment, evidence


def test_research_outputs_require_registered_cell():
    registry, _, attachment, evidence = _chain()
    registry.cells.clear()
    from backend.cell_analysis import CellAnalysisInput
    analysis = CellAnalysisInput("c", attachment, evidence)
    with pytest.raises(ValueError, match="existing registered cell"):
        register_cell_research_outputs(
            registry, analysis, state="normal", state_assessment_id="sa", state_confidence=.9,
            state_assessed_at="2026-08-27T00:00:00+00:00", state_provenance=Provenance(),
            state_uncertainty=__import__("backend.data_foundation", fromlist=["Uncertainty"]).Uncertainty("test", score=.1),
            age_estimate_id="age", estimated_age_years=40, age_uncertainty=__import__("backend.data_foundation", fromlist=["Uncertainty"]).Uncertainty("test", interval=(38,42)),
            age_assessed_at="2026-08-27T00:00:00+00:00", age_provenance=Provenance())


def test_analysis_input_must_target_cell():
    registry, _, attachment, evidence = _chain()
    from backend.cell_analysis import CellAnalysisInput
    bad = CellAnalysisInput("other", attachment, evidence)
    with pytest.raises(ValueError, match="target"):
        bad.validate()
