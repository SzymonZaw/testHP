# H5 — Own-cohort hand vision

This stage is the first concrete bridge between `data/raw/hand/own_cohort` and the longitudinal hand observation model.

## What it does

For each supported image it computes:

- image width and height;
- mean brightness and simple RGB contrast;
- number of detected hands;
- MediaPipe handedness and confidence;
- normalized hand bounding-box geometry;
- 21 normalized hand landmarks per detected hand;
- zone centroids and spans for wrist, thumb and four fingers;
- normalized 3D landmark-chain length for each finger.

The measurements are converted into the project's `HandObservation` shape by `observations_from_analysis()`.

## What it deliberately does not do

This stage does **not**:

- diagnose disease;
- estimate biological age;
- claim cellular damage;
- infer a subject identity from image similarity;
- infer longitudinal continuity between images;
- claim that a geometric difference is pathological.

A zone ranking later in the pipeline must therefore mean **"worth inspecting more closely"**, not **"diseased"**.

## Current input

The repository currently contains three images in `data/raw/hand/own_cohort`.
The analysis can be run locally with:

```powershell
python scripts/analyze_own_hand.py --root data/raw/hand/own_cohort --subject own_cohort --session session-001 --timepoint T0
```

The command writes a JSON research record to `data/longitudinal/own_hand_vision_T0.json`.

## Important subject-linking rule

The `--subject` value is an explicit research label supplied by the operator. It is never inferred from the photographs. If several people are present in a folder, they should be assigned different subject/session identifiers before longitudinal comparison.

## Next step

Integrate this analyzer into the FastAPI research pipeline so that the dashboard can show:

`own_cohort image → detected hand → landmark geometry → zones → measured observations → review priority`

Only after this works reliably should we add temporal comparison and then depth/video/multimodal hand data.
