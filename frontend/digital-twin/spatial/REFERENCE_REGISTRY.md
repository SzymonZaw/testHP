# Digital Twin Reference Registry

The registry separates public reference resources from subject-specific user evidence.

## Current references

| datasetId | Role | Scope |
|---|---|---|
| `nih3d-3DPX-017237` | reference, template | Healthy adult human hand 3D anatomical template |
| `nih3d-3DPX-017249` | reference, template | Hand/wrist bone geometry |
| `openneuro` | reference | Imaging/data-organization reference; individual datasets require separate review |
| `human-protein-atlas` | reference | Gene/protein and cell-type molecular reference |

## Policy

1. A reference dataset is not user evidence.
2. A reference/template must not be copied into `biologicalState`.
3. Population-level molecular information must not be assigned to a specific user cell without supporting evidence.
4. Dataset-specific licensing and provenance must be preserved.
5. Coordinate systems must be verified before spatial registration.
6. `training_data` and `user_evidence` are explicit roles and must not be inferred from a URL.
7. Missing user evidence remains `NOT ESTABLISHED`; a reference dataset does not fill that gap automatically.

## Intended architecture

```text
Reference Registry
       |
       +--> anatomy / imaging / molecular reference
       |
       v
 model / atlas / registration support
       |
       +----------------------+
                              |
User-owned data --------------+--> Digital Twin
                              |
                              +--> evidence / state
```

The registry is therefore a provenance layer, not a biological inference engine.
