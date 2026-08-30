# Real spatial reference workflow

The Digital Twin distinguishes three data classes:

1. **Reference geometry** — public anatomical/cell resources used as a baseline.
2. **User geometry** — the user's own GLB/GLTF/segmentation/evidence.
3. **Registered observations** — data explicitly transformed into the user's coordinate system with provenance.

## Initial real hand reference

The first reference is the NIH 3D healthy adult human hand template, model 3DPX-017237.

- Source: https://3d.nih.gov/entries/3DPX-017237
- Download page: https://3d.nih.gov/entries/download/17237/1
- Upstream source repository: https://github.com/HegdeUSA/Hand_template
- Upstream repository is MIT licensed.

The template was constructed from T1-weighted MRI of 27 healthy adult hands from 21 subjects and exported as a segmented hand surface. It is a **real anatomical reference**, not a patient's hand.

### Important limitation

The NIH template does **not** supply the required semantic regions `palm`, `thumb`, `index`, `middle`, `ring`, `little`, and `wrist` as separate geometry IDs. Therefore the manifest must not invent those mappings.

Do **not** create region IDs from visual guesses, bounding boxes, or display labels. A real segmentation/annotation source must be supplied before region picking is considered authoritative.

## Reference tissue/cell sources

Reference sources include:

- HuBMAP / Human Reference Atlas for human tissue, spatial single-cell, multimodal assays and anatomical reference terms: https://hubmapconsortium.org/hubmap-data/
- Allen Cell Explorer for public 3D human-cell microscopy and cell-structure resources: https://www.allencell.org/

These sources are not automatically registered to the NIH hand template. They remain separate reference datasets until an explicit registration/annotation transform exists.

## Reference vs Personal Twin

`frontend/digital-twin/anatomy-tissue-model-v1.js` now exposes a small browser-side `SpatialReferenceRegistry` with separate stores:

```text
Reference datasets  -> registry.register()
Personal datasets   -> registry.registerPersonal()
```

Reference datasets are always marked:

```text
kind = reference
referenceOnly = true
```

Personal datasets are marked:

```text
kind = personal
referenceOnly = false
```

This prevents a public reference asset from silently becoming a patient's observation.

## User-owned Digital Twin import

The browser importer `window.testhpImportSpatialAsset(file, metadata)` accepts `.glb` and `.gltf` files and requires explicit metadata for:

```text
id
name
coordinateSystem
geometry[]
regionMappings[]
```

Optional metadata can provide:

```text
tissueMappings[]
cellMappings[]
evidenceMappings[]
provenance
```

The importer validates the GLB magic header or GLTF JSON before registering the asset. It does **not** infer anatomy from the mesh and does **not** manufacture missing region, tissue or cell IDs.

A region mapping has the form:

```json
{
  "geometryId": "mesh_palm",
  "regionId": "palm"
}
```

Supported canonical region IDs are:

```text
palm
thumb
index
middle
ring
little
wrist
```

## Spatial chain

The intended authoritative chain is:

```text
User GLB/GLTF + metadata
        |
        v
SpatialDataAdapter / importer
        |
        +--> coordinate system
        +--> geometry IDs
        +--> region mappings
        +--> tissue mappings
        +--> cell mappings
        +--> evidence IDs
        |
        v
Canonical State
        |
        +--> 3D picking
        +--> Tree
        +--> Inspector
        +--> Evidence
```

The adapter accepts real `geometryId -> regionId` mappings when they are present in user metadata. It does not invent missing mappings.

## Cell-level requirement

To make `Cell A17` a genuinely spatial object, import a dataset containing at minimum:

```text
cellId
x
y
z
```

and preferably a segmentation/mesh/label image plus a declared coordinate system. Then map:

```text
geometryId -> cellId -> tissueId -> regionId -> evidenceId
```

Only after that chain exists should the UI claim that a clicked 3D object is a specific biological cell.
