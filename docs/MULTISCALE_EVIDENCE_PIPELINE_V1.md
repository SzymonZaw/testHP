# Multiscale Evidence Pipeline v1

This is the implementation target for connecting the user's upload to the Hand Digital Twin without inventing unavailable biological evidence.

## End-to-end contract

```text
USER DATA
  |
  +--> acquisition/QC/provenance
  |
  +--> hand imaging --------------------> hand geometry/anatomy
  |                                          |
  |                                          +--> region
  |
  +--> WSI/histology -> tissue -> cells ----+
  |                       |       |
  |                       |       +--> cell state
  |                       +----------> tissue state
  |
  +--> RNA -------------------------------> molecular state
  +--> genomics ---------------------------> genomic features
  +--> proteomics --------------------------> protein state
  +--> epigenetics -------------------------> epigenetic state
  |
  +--> reference/clinical labels ----------> ground truth
                                             |
                                             v
                                  evidence-aware fusion
                                             |
                                             v
                                   biological state
                                             |
                                  +----------+----------+
                                  |                     |
                              age estimate        health/pathology
                                  |                     |
                                  +----------+----------+
                                             |
                                             v
                                   hand-level twin state
```

## Implementation stages

### Stage 1 — acquisition contract

Implement validation for the fields in `USER_INPUT_DATA_CONTRACT_V1.md`.

The validator should reject structurally invalid uploads, but should not reject a valid package merely because optional modalities are absent.

### Stage 2 — modality adapters

Create one adapter per evidence class:

- hand images
- hand video
- hand 3D/depth
- WSI/histology
- transcriptomics
- genomics
- proteomics
- epigenetics
- reference/clinical labels

Each adapter outputs a common evidence envelope rather than directly writing a biological conclusion.

### Stage 3 — spatial hierarchy

Use explicit IDs and parent relationships:

```text
hand -> anatomical region -> tissue region -> cellular field -> cell
```

A deeper node must reference the evidence that actually supports it.

### Stage 4 — tissue/cell reconstruction

For histology:

1. image QC
2. tissue segmentation
3. cell/nucleus instance segmentation
4. cell feature extraction
5. cell-type classification
6. spatial coordinates
7. neighborhood graph
8. tissue architecture
9. registration to hand anatomy if justified

The first production-quality milestone is not perfect cell classification. It is a traceable cell table with coordinates, segmentation confidence and source region.

### Stage 5 — modality-specific biological features

Do not fuse raw modalities prematurely.

Each modality produces versioned features plus uncertainty:

```text
modality -> QC -> normalized features -> biological feature set
```

### Stage 6 — evidence fusion

Fuse only co-registered, temporally compatible evidence. The fusion layer must expose which modalities contributed to every result.

When modalities disagree, retain disagreement and uncertainty instead of selecting an arbitrary winner.

### Stage 7 — health/pathology reference

Create a benchmark layer containing real labelled samples. Separate:

- training data
- validation data
- external test data
- prospective/user data

Do not allow the same source cohort to become both training and claimed external validation.

### Stage 8 — biological age

Implement age estimates as model outputs with applicability metadata. Start with validated modality-specific clocks where evidence supports them. Only later construct tissue/region/hand composite age models.

The composite model must be trained and externally validated; it cannot be justified by averaging arbitrary age estimates.

### Stage 9 — hand-level digital twin

The hand-level state is a structured aggregation of evidence, not a single opaque score.

At minimum it should expose:

- spatial state
- tissue state
- cellular state
- molecular state
- biological-age estimates
- health/pathology evidence
- uncertainty
- provenance
- missing evidence

### Stage 10 — user result

For each requested analysis the API should return one of:

```text
SUPPORTED_WITH_EVIDENCE
INSUFFICIENT_EVIDENCE
OUT_OF_DOMAIN
PROCESSING_FAILED
```

Never return a plausible-looking biological result when required evidence is missing.

## Data readiness matrix

| Capability | Input contract | Pipeline | Real reference data | Validation |
|---|---|---|---|---|
| Hand geometry | defined | partial/implement | public 2D/3D datasets needed | benchmark needed |
| WSI -> tissue | defined | needs completion | public histology datasets available | benchmark needed |
| WSI -> cells | defined | needs completion | public single-cell/spatial/histology datasets available | benchmark needed |
| Genomics | defined | adapter + feature layer | public datasets available | domain validation needed |
| Transcriptomics | defined | adapter + feature layer | public datasets available | domain validation needed |
| Proteomics | defined | adapter + feature layer | public datasets available | domain validation needed |
| Epigenetics | defined | adapter + feature layer | public datasets available | domain validation needed |
| Healthy/disease | defined | benchmark layer needed | labelled cohorts required | external test required |
| Biological age | defined | scientific model needed | age-labelled cohorts required | external validation required |
| Hand-level fusion | defined conceptually | not scientifically complete | multimodal paired cohorts required | prospective validation required |

## Critical rule

Public datasets can be used to develop and benchmark individual components. They cannot automatically establish that a combined Hand Digital Twin works for a new user. The final system needs an explicit validation strategy and, for clinical use, appropriate clinical/regulatory evidence.
