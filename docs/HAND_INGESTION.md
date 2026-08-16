# Hand image ingestion

The multiscale pipeline now treats `data/raw/hand/own_cohort/<timepoint>/` as a first-class source for the Digital Twin.

Supported standardized views are:

- `front.jpg`
- `back.jpg`
- `thumb.jpg`
- `side_left.jpg`
- `side_right.jpg`

For each supplied image the pipeline records only acquisition and surface observations (view, dimensions, pixel count, mean brightness and mean dynamic range). These are evidence records linked to `subject_id`, `timepoint` and a conservative hand zone.

The ingestion layer deliberately does **not** diagnose disease, ageing or cellular state. A view filename is not treated as proof of a biological abnormality.

For `T0`, these records are inserted into the Digital Twin history and evidence collections. The same mechanism can ingest `T1` later, enabling a subsequent T0→T1 change layer without changing the raw-data layout.
