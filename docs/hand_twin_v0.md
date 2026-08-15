# Hand digital twin v0

## Purpose

`/api/hand/twin` exposes the first structured spatial representation of the personal hand input. It is deliberately a **spatial evidence container**, not a biological prediction model.

## Current representation

The v0 twin contains:

- explicit identity placeholders for subject, session and timepoint;
- a declared identity rule preventing filenames from creating subject links;
- stable anatomical regions: wrist, palm, thumb, index, middle, ring and little finger;
- landmark-index definitions for each region;
- observations attached to regions;
- source-file provenance;
- technical visibility/review priority;
- coordinate-space declarations;
- explicit slots for future tissue, cellular, molecular and non-image evidence;
- an evidence boundary describing what is and is not currently observed.

## Why this is important

The twin is now the beginning of the spatial contract needed for the later workflow:

```text
own_cohort image
      ↓
hand landmarks
      ↓
stable region ID
      ↓
region observation
      ↓
ROI
      ↓
future deeper measurement
      ↓
tissue / cell / molecular evidence
```

The same region ID is intended to become the anchor for later observations. This is preferable to linking data by filename or by visual similarity.

## Identity is intentionally not inferred

The current twin returns:

```text
subject = null
session = null
timepoint = null
identity_status = not_registered
```

This is intentional. Longitudinal monitoring cannot be implemented correctly until the system has an explicit subject/session/timepoint registration contract.

## Current limitations

The v0 twin does not yet provide:

- calibrated millimetre-scale geometry;
- surface mesh reconstruction;
- persistent storage across runs;
- longitudinal comparison;
- tissue/cellular/molecular observations;
- biological-age estimation;
- pathology or disease classification.

## Next step: H5

The next implementation should be the **baseline/identity layer**:

1. register a subject;
2. register an acquisition session;
3. register a timepoint;
4. associate a hand observation with that identity;
5. persist the observation;
6. allow the same anatomical region to be compared across later runs.

Only after that contract exists should a region be described as having changed over time.
