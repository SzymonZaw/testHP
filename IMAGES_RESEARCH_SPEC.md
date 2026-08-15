# Images modality — research specification

## Scope

`data/raw/images/` represents the **macroscopic skin level**: ordinary/high-quality camera imagery and directly related non-microscopic evidence. It is the surface-level complement to the deeper tissue (`wsi`) and molecular (`rna`) modalities.

The current conceptual groups are:

- `normal_skin/` — healthy/reference skin,
- `aging_skin/` — visible changes associated with ageing,
- `lesions/` — skin abnormalities not primarily defined by ageing,
- `pathology/` — historical/ambiguous category; its exact scientific scope must be confirmed before it receives a biological task.

## Scientific questions

The image modality should answer progressively:

1. Is the image usable?
2. What skin region is visible?
3. What measurable surface characteristics are present?
4. Which regions differ from an appropriate reference or personal baseline?
5. Is there a candidate area requiring closer inspection?
6. What deeper evidence is needed to distinguish normal variation, ageing-related change and pathology?

## Information map

| Level | Information | Result type |
|---|---|---|
| Input | format, size, readability, dimensions | observation |
| Image | colour, brightness, contrast, noise, focus proxies | observation |
| Surface | texture, pigmentation, local colour variation | observation/feature |
| Region | lesion/skin-region geometry and spatial distribution | feature |
| Longitudinal | change of the same region over time | observation/trend |
| Interpretation | ageing/pathology-compatible signal | validated interpretation only |

## Dataset roles

### `normal_skin`
Reference distribution for ordinary skin appearance and measurement variability. It should help define what is normal within the relevant acquisition conditions; it should not be treated as a universal healthy baseline for every person.

### `aging_skin`
Reference material for ageing-associated visible changes. It should support research into which measurable surface features correlate with ageing, but it must not be used to infer a person's biological age from appearance alone without validation.

### `lesions`
Reference material for non-ageing skin abnormalities. It can support development and benchmarking of lesion localization/characterization methods.

### `pathology`
Do not assign a final biological task until the actual files and provenance are audited. The directory name alone is insufficient evidence of scientific scope.

## Analysis ladder

```text
I0  input audit
 ↓
I1  image quality
 ↓
I2  skin-region detection / segmentation
 ↓
I3  colour + texture + geometry measurements
 ↓
I4  local region/lesion candidate detection
 ↓
I5  reference/personal-baseline comparison
 ↓
I6  longitudinal change
 ↓
I7  deeper-resolution request (WSI/microscopy/lab)
 ↓
I8  validated biological interpretation
```

## Required output

The future result should report:

- acquisition quality,
- visible/analyzed skin area,
- measured surface features,
- candidate regions of interest,
- comparison baseline/reference,
- longitudinal change where repeated data exist,
- uncertainty,
- recommended deeper measurement,
- provenance.

A lesion candidate is not a diagnosis. A difference from `normal_skin` is not automatically disease. A difference from `aging_skin` is not automatically accelerated ageing.

## Completion criterion

The image phase is ready to feed into `wsi/` when the system can reproducibly locate and measure skin regions, identify transparent ROIs, preserve their spatial coordinates and request deeper evidence without making unsupported biological claims.
