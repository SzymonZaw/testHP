from datetime import datetime

import pytest

from core.anatomy import AnatomicalLocation
from core.observation import Observation
from digital_twin.observation_mapper import SpatialObservationMapper
from digital_twin.observation_pipeline import ObservationPipeline
from digital_twin.spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, TissueRegion


def build_model() -> HandSpatialModel:
    model = HandSpatialModel()
    region = HandRegion(region_id="palm", name="Palm", side="left")
    tissue = TissueRegion(tissue_id="skin-1", tissue_type="skin", region_id="palm")
    tissue.add_cell(CellLocation(
        cell_id="cell-1",
        position=SpatialPoint(1.0, 2.0, 3.0),
        tissue_id="skin-1",
        cell_type="keratinocyte",
        confidence=0.98,
    ))
    region.add_tissue(tissue)
    model.add_region(region)
    return model


def make_observation() -> Observation:
    return Observation(
        id="obs-1",
        subject_id="subject-1",
        timepoint_id="t0",
        name="cell morphology",
        value={"nucleus_area": 42.0},
        observed_at=datetime(2026, 1, 1),
        anatomical_location=AnatomicalLocation(
            id="cell-1", name="Cell 1", level="cell", parent_id="skin-1"
        ),
        biological_level="cellular",
        modality="microscopy",
    )


def test_pipeline_ingests_and_indexes_cell_observation():
    pipeline = ObservationPipeline(SpatialObservationMapper(build_model()))

    record = pipeline.ingest(make_observation())

    assert record.spatial_context["region_id"] == "palm"
    assert record.spatial_context["tissue_id"] == "skin-1"
    assert record.spatial_context["cell_id"] == "cell-1"
    assert pipeline.for_cell("cell-1") == [record]
    assert pipeline.for_timepoint("t0") == [record]


def test_pipeline_rejects_duplicate_observation_id():
    pipeline = ObservationPipeline(SpatialObservationMapper(build_model()))
    observation = make_observation()

    pipeline.ingest(observation)

    with pytest.raises(ValueError, match="already ingested"):
        pipeline.ingest(observation)
