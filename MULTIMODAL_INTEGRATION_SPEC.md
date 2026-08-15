# Multimodal integration — research specification

## Purpose

This document closes the scientific-definition pass across `hand/`, `images/`, `wsi/` and `rna/`. The modalities are complementary, but they must not be fused merely because they concern similar biology.

## Biological scale map

```text
HAND / IMAGES
macroscopic appearance, geometry, motion, visible surface
          ↓
WSI
 tissue architecture + cellular morphology + spatial organization
          ↓
RNA
 molecular / transcriptomic state
          ↓
CELLULAR + NON-IMAGE DATA
 specific cellular and biochemical state when available
```

The hand digital twin provides the spatial organization for the investigated fragment. WSI and RNA provide deeper evidence only when their specimen/sample/spatial relationship is explicit.

## Evidence path

A final multimodal claim should be traceable as:

```text
subject
  ↓
timepoint
  ↓
anatomical region / ROI
  ↓
image observation
  ↓
tissue/specimen observation
  ↓
cellular observation
  ↓
molecular sample
  ↓
validated interpretation
```

If any required link is missing, the system reports the relationship as unavailable rather than guessing it.

## What each modality contributes

| Modality | Primary question | Typical level |
|---|---|---|
| `hand` | What is the macroscopic state of the investigated fragment and where should we inspect next? | organism fragment / region |
| `images` | What measurable surface changes are present? | macroscopic skin |
| `wsi` | What is happening in tissue architecture and cellular morphology? | tissue / cell |
| `rna` | What is happening at the molecular/transcriptomic level? | molecular |

## Final state representation

The unified state should retain separate dimensions:

- **normal/reference evidence**,
- **disease-related evidence**,
- **ageing-related evidence**,
- **functional/motion evidence**,
- **molecular evidence**,
- **spatial location**,
- **timepoint/trajectory**, 
- **uncertainty**, 
- **missing evidence**.

There should be no universal score that hides these dimensions.

## Cross-modal rules

### Allowed

- link observations through an explicit subject/sample/specimen identifier;
- link a deeper measurement to a hand/image ROI through explicit spatial provenance;
- compare repeated measurements when timepoints and acquisition definitions are known;
- use one modality to prioritize a deeper measurement in another modality.

### Not allowed

- infer subject identity from dataset names;
- treat public datasets as longitudinal observations of the user's subject;
- call a visible difference a disease;
- call a molecular signature “age” without a validated model/assay;
- call a cell cancerous without appropriate validated evidence;
- treat missing data as a negative finding.

## Integration ladder

```text
M0  independent modality audits
 ↓
M1  common provenance + identifiers
 ↓
M2  spatial registration
 ↓
M3  temporal registration
 ↓
M4  cross-modal ROI selection
 ↓
M5  tissue/cell/molecular evidence aggregation
 ↓
M6  disease vs ageing evidence separation
 ↓
M7  longitudinal multimodal change
 ↓
M8  validated unified research report
```

## Final project result

The intended final product is a **transparent biological evidence map** of an organism or selected fragment:

- what was observed,
- where it was observed,
- at which biological level,
- what changed over time,
- which regions require deeper investigation,
- what disease-related evidence exists,
- what ageing-related evidence exists,
- what evidence is missing,
- and which exact measurements support each conclusion.

The system should be able to stop at any level and explicitly say: **insufficient evidence for deeper interpretation**.
