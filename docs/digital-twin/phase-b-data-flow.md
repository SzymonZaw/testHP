# Phase B — actual data flow

The runtime foundation now has an explicit adapter boundary between ingested assets and the multimodal domain model.

```text
uploaded / imported asset
        ↓
canonical DataObject
        ↓
ModalityAcquisition
        ↓
source frame (MRI/US/etc.)
        ↓
explicit Registration
        ↓
HAND_COORDINATE_SYSTEM
        ↓
SegmentationEvidence
        ↓
AnatomicalStructure
        ↓
TissueEvidence / TissueRegion
        ↓
HistologyRegion
        ↓
CellSegmentationEvidence
        ↓
CellObject
        ↓
CellStateAssessment + Evidence
```

## Important boundary

`modality_adapters.py` does not pretend that an uploaded MRI or US study is already registered or segmented. It reports `unregistered` until a real registration is supplied. This prevents the digital twin from silently treating file coordinates as anatomical coordinates.

## Required real-world data for the next implementation layer

- MRI/US acquisition with a stable acquisition identifier.
- Hand/subject/timepoint identifiers shared with the surface dataset.
- Calibration or landmarks sufficient to estimate a transform into hand space.
- Registration quality metrics and uncertainty.
- Segmentation masks/meshes with algorithm and version provenance.
- Tissue-region annotations tied to the anatomical structure.
- Histology slide identity and sampling-region coordinates.
- Cell segmentation outputs tied to the histology/tissue region.

No biological state or clinical conclusion is inferred merely from the presence of an image.
