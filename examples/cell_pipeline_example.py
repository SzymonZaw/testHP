"""Minimal end-to-end example for the cell pipeline."""

import numpy as np

from core.anatomy import AnatomicalLocation
from pipelines.cell_pipeline import run_cell_pipeline


image = np.zeros((64, 64), dtype=np.float32)
image[8:16, 8:16] = 10
image[24:36, 30:42] = 10
image[45:55, 12:22] = 10

result = run_cell_pipeline(
    image,
    subject_id="example-person",
    timepoint_id="T0",
    anatomical_location=AnatomicalLocation(
        id="skin-sample",
        name="Example skin sample",
        level="tissue",
    ),
    threshold=5,
    min_area=10,
    quality=0.8,
)

print("Cells:", result.analysis["cell_count"])
print("Observations:", len(result.observations))
print("State dimensions:", result.state.dimensions)
