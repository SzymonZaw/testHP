# Observation management — stages 1–5

## Source of truth

The biological observation workflow is now explicit:

```text
Digital Twin spatial target
        ↓
GET/POST/PATCH /api/observations
        ↓
backend/observation_registry.py
        ↓
core.observation.Observation
        ↓
subject + timepoint + anatomical location + biological level + value
```

The persistent manual-observation registry lives under `data/registry/manual_observations/`.
It is separate from `data/registry/spatial_evidence.json`: spatial evidence describes source evidence, while an Observation describes an explicit biological statement.

## Domain contract

Every manual observation requires:

- `subject_id`
- `timepoint`
- `spatial_id`
- `biological_level`: `macro | tissue | cellular | molecular`
- `name`
- `value`

It may additionally carry modality, source, notes, evidence id and source measurement ids.

The core `Observation` model keeps these biological dimensions as first-class metadata while remaining backward compatible with existing ingestion code.

## UI workflow

The Digital Twin contains **Zarządzanie danymi → Obserwacje**. The selected spatial target from the navigator is the target used by the form and list.

Implemented actions:

1. list observations for the current target and timepoint;
2. add a biological observation;
3. open full details, including evidence reference and version history;
4. edit an observation;
5. retain an audit entry and increment the observation version on every edit.

Archiving, longitudinal comparison and automatic Digital Twin state updates are deliberately outside stages 1–5 and remain follow-up work.
