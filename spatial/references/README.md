# Spatial references

The registry points to real external scientific sources rather than fabricating spatial data.

## NIH hand

Use the NIH 3D hand template as a **reference geometry**. It is based on MRI data from healthy adult hands and is suitable as a geometric baseline.

Do not infer region IDs merely from mesh appearance. A validated annotation/segmentation must supply the mapping:

```text
geometryId -> regionId
```

## HuBMAP / HRA

Use HRA/HuBMAP for multiscale anatomical terminology, spatial registration concepts and public spatial/cellular datasets. Experimental data must retain donor/sample/dataset provenance.

## Personal Digital Twin

The user flow should support either:

- upload/import of the user's own GLB/GLTF/STL/NIfTI/segmentation/metadata;
- a public reference asset as a non-personal baseline;
- later registration of the user's measurements to a reference coordinate system.

Never merge reference observations into the personal subject record without an explicit registration/provenance relationship.
