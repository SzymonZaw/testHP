# Reference datasets for the Digital Twin

These are **reference inputs**, not a substitute for a subject-specific twin. They should be registered as `SpatialSource` entries with their original identifier, version/access date and license.

## 1. NIH 3D — healthy adult human hand template

**Best starting point for a real anatomical reference hand.**

- Dataset: NIH 3D 3DPX-017237, *3D Model of An Anatomical Template of Healthy Adult Human Hand*.
- The template was built from T1-weighted MR images of 27 healthy adult hands from 21 subjects and segmented with 3D Slicer.
- The NIH page provides a downloadable 3D model and version history; the current processed version includes GLB support.
- This is an anatomical template, not a scan of the user's own hand.

Reference: https://3d.nih.gov/entries/3DPX-017237

## 2. NIH 3D — segmented hand/wrist bones

- Dataset: NIH 3D 3DPX-017249, *Bones of the Healthy Adult Human Hand/Wrist*.
- Derived from the healthy-adult hand template and segmented so the hand bones are represented separately from surrounding anatomy.
- License shown by NIH 3D: GNU GPLv3.
- Useful for validating the 3D loading, coordinate handling and region/geometry mapping pipeline, but it is not a complete soft-tissue hand.

Reference: https://3d.nih.gov/entries/3DPX-017249

## 3. HandCT — computational CT hand model

- Zenodo dataset: *HandCT: hands-on computational dataset for X-Ray Computed Tomography*.
- DOI: 10.5281/zenodo.6473101.
- Contains a meshed hand model plus reproducible Blender/Python tooling for CT simulation.
- Useful for computational imaging experiments and testing geometry/coordinate pipelines.
- It is a computational/anatomical phantom, not a subject-specific clinical scan.

Reference: https://zenodo.org/records/6473101

## 4. Digital human forearm and hand

- Open-access anatomical dataset described in *The digital human forearm and hand*.
- The study used 7T MRI and CT of an un-embalmed cadaveric arm and produced 3D geometrical models of bones, cartilage, muscle and muscle pathways, plus physiological measurements.
- Useful as a richer anatomical/biomechanical reference than a surface-only hand mesh.

Reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC6183001/

## 5. Human skin spatial / single-cell reference

- GEO GSE241124: *Spatiotemporal Single-Cell Roadmap of Human Skin Wound Healing (Spatial)*.
- Human in-vivo skin wound samples were profiled at multiple healing stages with spatial transcriptomics.
- GEO also lists the corresponding single-cell series GSE241132.
- These datasets are valuable for designing the molecular/cellular data model and longitudinal semantics, but they are **skin datasets, not hand-cell spatial scans**. Do not map their cells directly onto a hand mesh without a scientifically justified registration method.

References:
- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241124
- https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241132

## Recommended order for this project

1. Use the NIH 3DPX-017237 hand template to prove the real-asset pipeline.
2. Add the NIH segmented bone model to prove geometry IDs and segmentation handling.
3. Use HandCT for reproducible spatial/CT experiments.
4. Add the digital forearm/hand dataset when deeper tissue geometry is needed.
5. Keep human skin spatial/single-cell datasets in the molecular reference layer until a valid spatial registration method exists.
6. For a user's personal Digital Twin, prioritize their own 3D scan / imaging / laboratory data and preserve provenance rather than replacing it with a population template.

## Scientific rule

A reference dataset can establish that a geometry, measurement or molecular observation exists in that source. It cannot establish that the same observation is true for a specific user. The application must therefore keep `source`, `provenance`, `dataset version`, `coordinate system` and `validation status` attached to every imported reference.
