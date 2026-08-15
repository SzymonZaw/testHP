# H5 — Longitudinal hand tracking

H5 introduces the first data model for monitoring the same hand over multiple observations.

## Model

Every observation is attached to:

- `subject_id` — the organism/person being monitored;
- `session_id` — one acquisition/measurement session;
- `timepoint` — e.g. `T0`, `T1`, `T2`;
- `hand_id` — stable identifier for the hand instance;
- `laterality` — left/right/unknown;
- `zone` — wrist, palm, thumb, index, middle, ring or little;
- `observation_type` and `metric` — what was actually measured;
- `source_file` — provenance when known.

## Evidence boundary

H5 deliberately stores **observations**, not diagnoses. A measured change such as `+1.2 mm` or `+8%` is not automatically converted into "disease", "aging" or another biological conclusion.

The comparison endpoint therefore returns:

1. baseline value;
2. current value;
3. absolute delta;
4. relative change when defined;
5. a review priority for zones with the largest measured change.

The interpretation field remains `null` until a validated modality-specific analysis is implemented.

## API

- `GET /api/hand/schema` — current H5 contract;
- `POST /api/hand/observations` — record one measured observation;
- `GET /api/hand/subjects/{subject_id}` — retrieve all stored timepoints for a subject;
- `POST /api/hand/compare` — compare baseline observations with current observations.

Observations are stored locally in `data/longitudinal/hand_observations.jsonl` and are not committed to GitHub.

## Next stage

H5 is the temporal identity/data layer. The next implementation should connect real `own_cohort` images to stable hand landmarks and zone geometry, then populate H5 observations automatically rather than manually.
