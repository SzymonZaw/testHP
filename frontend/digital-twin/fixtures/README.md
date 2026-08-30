# Frontend fixtures boundary

Fixtures are test/development inputs only. Production UI must receive `AnalysisResult` through the canonical API boundary and then `DigitalTwinState`.

Allowed:

```text
fixtures/ → tests / local development
```

Forbidden:

```text
fixtures/ → production result rendering
```

Fixtures must never be presented as validated biological findings. In particular, synthetic biological age, health labels, intervention priorities, and molecular states must be explicitly marked as fixtures and must not be used as fallback values for missing backend data.
