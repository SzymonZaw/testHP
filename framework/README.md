# testHP framework

The framework is the operational layer around the existing research modules. It does not replace the biological-analysis code.

## Quick start

From the repository root:

```bash
python -m framework status
python -m framework doctor
python -m framework run
```

### `status`

Scans `data/raw` and reports which datasets are actually present. Missing optional datasets are shown but do not stop the project.

### `doctor`

Checks the discovered data and imports for the core project packages. Use this first after installing dependencies or adding a new dataset.

### `run`

Runs a deterministic framework smoke test. It verifies the common observation → quality filter → digital biological twin contract and writes a JSON report under `reports/framework/`.

This command deliberately does **not** pretend to run a dataset-specific model when an adapter is not available.

## Design

```text
user
  ↓
framework CLI
  ├── data discovery
  ├── readiness / diagnostics
  ├── orchestration
  ├── smoke validation
  └── machine-readable report
          ↓
existing testHP modules
  core → analysis → integration → organism/digital twin
                       ↓
                    validation
                       ↓
                      audit
```

The next extension point is modality adapters. They can register dataset-specific loaders/preprocessors without changing the user-facing CLI.
