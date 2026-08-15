# Research interface contract — Stage 14

The interface should expose the evidence trail and progressive analysis path.

## Main workflow

```text
1. Register/select data
2. Validate inputs
3. Show available analyses
4. Run modality-specific analysis
5. Inspect observations
6. Inspect derived features
7. Select region/sample of interest
8. Request deeper analysis
9. Compare timepoints
10. Inspect cross-modal evidence
11. Inspect provenance and limitations
12. Export run
```

## Result presentation

Every result should visibly distinguish:

- **Observed** — directly measured from input.
- **Derived** — calculated from observations.
- **Interpreted** — biological meaning supported by a validated method.
- **Unavailable** — required evidence or analysis is missing.
- **Warning** — input exists but quality or validation is insufficient.

## Progressive navigation

The UI should support the future macro-to-micro workflow:

`organism/fragment → zone → tissue → cell → molecular/non-image evidence`

The next level should be opened only when the necessary evidence exists.

## Digital twin view

The twin should provide:

- anatomical/spatial zones,
- current observations,
- longitudinal history,
- priority/attention markers,
- links to deeper analyses,
- evidence provenance.

A priority marker means “inspect further”, not “diagnosis”.

## Research transparency

The interface must show why a result is available, unavailable or uncertain. It should never replace a missing modality with an apparently normal state.
