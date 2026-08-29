# Simulation, Predictive Digital Twin, Long-term Aging and Whole Body

Scope: stages 9–12. These are research architecture specifications. They are not validated clinical functionality.

## 9. Simulation

Goal: evaluate explicitly defined future scenarios from a measured current state.

```text
Current
 ├── no intervention
 ├── scenario A
 └── scenario B
          ↓
     Future state
```

### Requirements

1. Freeze and version the current-state snapshot used as simulation input.
2. Define each scenario explicitly, including assumptions and intervention parameters.
3. Use validated transition/dynamics models rather than arbitrary rules.
4. Record model version, training data, calibration and applicable domain.
5. Propagate input uncertainty through the simulation.
6. Produce future-state distributions, not unjustified point predictions.
7. Compare scenarios using predefined metrics.
8. Keep simulated outcomes clearly separated from observed evidence.

No scenario should be interpreted as a recommended treatment merely because the simulated outcome is favorable.

## 10. Predictive Digital Twin

Goal: forecast future states from the current longitudinal twin.

```text
Current
 ↓
5 years
 ↓
10 years
 ↓
20 years
 ↓
50 years
```

### Requirements

- Short-, medium- and long-horizon predictive models where data support them.
- Time-dependent prediction intervals and uncertainty propagation.
- Calibration and prospective validation.
- Out-of-distribution detection and explicit unsupported-horizon handling.
- Separation of observed history from predicted future.
- Versioned model/data/evidence provenance.

Longer horizons must not be presented with the same confidence as near-term forecasts. This remains a research layer until prospective validation demonstrates useful predictive performance.

## 11. Long-term Aging

Goal: model different biological rates of change across levels of organization.

```text
Cells
 ↓
Tissues
 ↓
Structures
 ↓
Person
```

### Requirements

1. Estimate aging trajectories from longitudinal data.
2. Allow different rates for cell types, tissues and structures.
3. Represent known aging-related covariates and confounding factors.
4. Personalize trajectories only when sufficient individual history exists.
5. Use longitudinal datasets with appropriate follow-up duration.
6. Update models as new observations arrive while preserving prior model versions.
7. Quantify increasing uncertainty with prediction horizon.
8. Validate trajectories on independent longitudinal data.

The model must not assume that one biological clock or one aging rate applies uniformly across the organism.

## 12. Whole Body

Goal: extend the validated hand architecture to additional organs and ultimately a coordinated Human Digital Twin.

```text
HAND
SKIN
MUSCLE
BONE
BLOOD
HEART
BRAIN
LIVER
KIDNEY
...
       ↓
HUMAN DIGITAL TWIN
```

### Requirements

1. Add additional organs incrementally, starting with a clearly defined second domain.
2. Reuse common identity, spatial, temporal, evidence and uncertainty contracts.
3. Define organ-specific models without erasing organ-specific biological differences.
4. Represent cross-organ relationships only where supported by evidence.
5. Establish shared temporalization and provenance.
6. Aggregate validated local findings into a system-level state with uncertainty propagation.
7. Validate each organ and each cross-organ relationship independently before system-level claims.

Whole-body integration is an architectural target, not evidence that a clinically complete Human Digital Twin currently exists.

## Cross-stage invariant

```text
Observed state
      ↓
Validated model
      ↓
Scenario / prediction
      ↓
Uncertainty
      ↓
Future state distribution
```

Simulated and predicted states must always remain distinguishable from observed biological measurements.
