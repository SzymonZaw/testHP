# Manual real inputs still needed

The synthetic fixtures cover text/metadata structure only. The following real files should be supplied manually when available.

## A. `data/raw/hand/own_cohort/`

Minimum useful set:

- [ ] one full dorsal-view photograph of the right hand
- [ ] one palmar-view photograph
- [ ] one lateral/oblique photograph
- [ ] one closer photograph of the fingers/palm
- [ ] one photograph including the wrist
- [ ] repeat the same views at a later timepoint T1
- [ ] keep capture conditions reasonably comparable between T0 and T1

Recommended metadata:

- subject ID
- session ID
- timepoint
- hand side
- device
- capture date/time
- optional anatomical region
- optional distance/lighting notes

Do not use the public `InterHand2_6M` images as T0/T1 personal observations.

## B. `data/raw/hand/media/`

- [ ] one valid MP4 or MOV video, 5–15 seconds
- [ ] 1080p if possible
- [ ] approximately 30 FPS
- [ ] one slow open/close hand movement
- [ ] one finger movement sequence
- [ ] optionally one rotation of the hand

The current `moov atom not found` messages indicate that some existing video files are empty or invalid. Replace those placeholders with real playable videos.

## C. `data/raw/images/`

For testing macroscopic skin analysis:

- [ ] independent normal-skin images
- [ ] ageing-related skin images
- [ ] lesion images
- [ ] verified SCIN/clinical-image examples if `pathology/scin` is retained
- [ ] metadata/provenance for each group

Important: `normal_skin` currently contains duplicate JPEG content matching `aging_skin`; replace it before using it as an independent reference set.

## D. `data/raw/wsi/`

- [ ] at least one real WSI/DICOM object that can be opened
- [ ] preferably a real whole-slide or sufficiently representative tiled specimen
- [ ] metadata including specimen/sample ID
- [ ] magnification or pixel spacing where available
- [ ] provenance

The existing TCGA-SKCM files are useful for technical DICOM testing but are not a full WSI benchmark.

## E. `data/raw/rna/`

- [ ] real expression matrix
- [ ] matching sample metadata
- [ ] explicit sample IDs
- [ ] explicit subject/specimen linkage where legitimately available
- [ ] timepoint where longitudinal data exist

Do not infer that a public GEO/TCGA sample belongs to `own_cohort` merely because it is processed in the same run.

## F. Optional non-image measurements

Useful future hand inputs include:

- temperature
- grip strength
- range of motion
- skin hydration
- perfusion/blood-flow measurements
- pressure/sensor streams
- other laboratory or structured numerical measurements

These should be introduced through explicit modality and provenance metadata rather than being encoded as arbitrary text fields.

## Scientific rule

A missing real input should remain `unavailable`. Do not replace it with synthetic values in `data/raw/` and do not interpret synthetic fixtures as health evidence.