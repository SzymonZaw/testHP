# Hand digital twin — stages 1–10

The `dev/next-cleanup` branch now treats the first ten stages as an evidence-acquisition pipeline. The API stores metadata, lineage and validation state; it does not fabricate missing measurements or clinical conclusions.

| Stage | Goal | Minimum real input | Stored evidence |
|---|---|---|---|
| 1 | Canonical data model | Subject, hand, timepoint | IDs, acquisition time, provenance, quality, confidence |
| 2 | Photo acquisition | Five calibrated-view assets | camera/lens/distance/lighting/scale/orientation |
| 3 | Calibration + 2D geometry | Camera calibration + scale reference | camera model, intrinsics/distortion, scale, reprojection error |
| 4 | Hand segmentation | Source photo + mask/model output | hand/finger/region labels, mask asset, model/version/confidence |
| 5 | 3D hand surface | >=2 registered views for a reconstruction worker | source lineage, coordinate frame, mesh/texture asset when actually produced |
| 6 | Internal anatomy | MRI/US/CT study | modality, study/asset, voxel spacing, acquisition metadata, frame |
| 7 | Multimodal registration | Source + target objects and transform | transform, frames, error and confidence |
| 8 | Histology | Tissue sample + slide/image | sample location, tissue type, staining, slide metadata, frame |
| 9 | Tissue segmentation | Histology image + tissue mask | labels, mask, method/version/confidence |
| 10 | Tissue pathology | Evidence-linked annotation | classification, evidence IDs, method, confidence, interpretation |

## Canonical hierarchy

`Subject -> Hand -> Timepoint -> Acquisition -> Dataset -> Observation`

All downstream records should be traceable to a subject, hand and timepoint. Spatial evidence uses one canonical `HAND_COORDINATE_SYSTEM` rather than independent module-specific coordinate systems.

## Important boundary

A registered metadata record is **not** proof that the corresponding algorithm has run. In particular, a planned reconstruction is not a mesh, and a pathology annotation is not a clinical diagnosis. Real outputs must carry their source object IDs, method/version, quality and confidence.

## API surface

- `GET /api/hand/data-model` — canonical schema and required evidence envelope.
- `GET /api/hand/data-registry` — persisted stage records.
- `GET /api/hand/validate` — contract validation plus real-data validation as separate sections.
- `POST /api/hand/validate` — legacy five-view validator remains available.
- `POST /api/hand/subjects` — stage 1 identity/timepoint registration.
- `POST /api/hand/photo-acquisitions` — stage 2 acquisition metadata.
- `POST /api/hand/photo-calibrations` — stage 3 calibration.
- `POST /api/hand/segmentations` — stage 4 segmentation result registration.
- `POST /api/hand/reconstructions` — stage 5 reconstruction result/plan registration.
- `POST /api/hand/imaging` — stage 6 MRI/US/CT registration.
- `POST /api/hand/registrations` — stage 7 multimodal registration.
- `POST /api/hand/histology` — stage 8 histology registration.
- `POST /api/hand/tissue-segmentations` — stage 9 tissue segmentation.
- `POST /api/hand/tissue-pathology` — stage 10 evidence-linked pathology annotation.

Real images continue to enter through the existing upload/photo pipeline. These stage APIs record the scientific metadata needed to make those assets reproducible and linkable later.
