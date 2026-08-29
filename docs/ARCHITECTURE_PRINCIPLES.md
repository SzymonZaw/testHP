# Architecture Principles

This document defines several architectural corrections that are important for the long-term biological scope of `testHP`.

## 8. Spatial hierarchy is not the biological model

The project may use a spatial hierarchy for navigation and addressing, but the biological system itself must **not** be modelled as a simple parent → child tree.

A useful spatial path can look like:

```text
HAND
 ↓
REGION
 ↓
TISSUE
 ↓
CELL
 ↓
MOLECULAR EVIDENCE
```

This is useful for the **spatial coordinate system** and the user interface. It is not a sufficient representation of biological relationships.

Biology is better represented as a combination of spatial hierarchy and a graph of relationships:

```text
                         MOLECULAR STATE
                       /       |        \
                      /        |         \
                   CELL ←────→ CELL ←────→ CELL
                    ↓  \       |        /  ↓
                    ↓   \      ↓       /   ↓
                 TISSUE ←────→ TISSUE ←────→ TISSUE
                    \            |            /
                     \           ↓           /
                      └──────── ORGAN ───────┘
                              ↓     ↓
                           SYSTEM ↔ SYSTEM
```

A cell can be influenced by:

- neighbouring cells,
- extracellular matrix,
- vascular supply,
- immune cells and immune signalling,
- endocrine/hormonal signals,
- metabolites and systemic metabolism,
- mechanical and physical environment,
- signals originating from distant tissues or organs.

Therefore:

```text
spatial parent → spatial child
```

must describe **where something is**, not automatically **what biologically causes or determines it**.

### Architectural rule

The Digital Biological Twin should maintain at least two complementary structures:

```text
SPATIAL MODEL
    ↓
where is the observation?

BIOLOGICAL RELATIONSHIP GRAPH
    ↓
how is this entity related to other entities?
```

The spatial tree is authoritative for location and navigation. The relationship graph is authoritative for biological associations, interactions and dependencies.

A deeper spatial node must never automatically inherit biological conclusions from its parent. Evidence must be explicitly linked to the relevant entity, location and timepoint.

---

## 16. Decision layer is downstream of evidence and validation

The repository may contain planning, decision and audit infrastructure, but these components must not be treated as proof that the system is ready to make medical decisions.

The dependency chain should be:

```text
WHAT DID WE MEASURE?
        ↓
HOW WELL DID WE MEASURE IT?
        ↓
WHAT DOES THE EVIDENCE SUPPORT?
        ↓
WHAT REMAINS UNKNOWN?
        ↓
HOW VALIDATED IS THE INFERENCE?
        ↓
WHAT SHOULD BE INVESTIGATED NEXT?
        ↓
ONLY THEN: DECISION SUPPORT
```

Before any result can influence a decision, the system should be able to answer:

> **What exactly was measured?**

> **Where and when was it measured?**

> **Which modality and measurement method were used?**

> **What was the measurement quality?**

> **What inference was applied?**

> **What evidence supports that inference?**

> **What are the uncertainty and evidence gaps?**

> **Has the inference been independently validated?**

A decision layer must therefore be treated as a **downstream consumer of validated evidence**, not as an upstream feature that converts uncertain measurements into recommendations.

The research system should prefer:

```text
INSUFFICIENT EVIDENCE
```

over an unsupported recommendation.

Similarly, `planning` should primarily identify the **next measurement that would reduce uncertainty**, rather than prematurely prescribing an intervention.

The audit layer should preserve the complete chain from evidence to inference to decision-support output.

---

## 18. Evidence-grounded and anti-hallucination architecture

The anti-hallucination principle applies to the whole inference pipeline, not only to generative AI.

Every material biological claim should be traceable to the evidence and computation that produced it.

A target claim record should contain at least:

```text
CLAIM
│
├── claim_id
├── subject / entity ID
├── spatial location
├── timepoint
├── evidence IDs
├── measurement IDs
├── modality
├── preprocessing / quality information
├── model / method
├── model version
├── training population / dataset
├── reference population / dataset
├── derived features
├── assumptions
├── confidence
├── uncertainty
├── evidence coverage
├── evidence gaps
└── validation status
```

The system should support a user-visible evidence chain:

```text
CLAIM
  ↓
INFERENCE
  ↓
FEATURES
  ↓
MEASUREMENTS
  ↓
RAW / SOURCE EVIDENCE
```

For example, when the system reports a `senescent-like` signal for a cell, the user should be able to inspect **why** that signal exists:

```text
senescent-like
      ↓
features used
      ↓
measurements available
      ↓
source evidence
      ↓
model + version
      ↓
validation / uncertainty
```

The system must never silently convert missing evidence into a negative finding.

For example:

```text
DNA damage
    ↓
not measured
    ↓
NOT "no DNA damage"
    ↓
INSUFFICIENT EVIDENCE
```

Likewise, a model prediction is not itself a measurement. The data model should preserve the distinction between:

```text
OBSERVED
MEASURED
DERIVED
INFERRED
PREDICTED
UNKNOWN
```

This provenance chain is required even when no generative model is involved.

---

## 19. "I don't know" is a first-class biological result

The user interface should communicate uncertainty and missing evidence as clearly as positive findings.

A target single-cell view should look conceptually like:

```text
CELL #12831

Identity
██████████ 98%

Morphology
█████████░ 91%

Viability
███████░░░ 73%

Senescence
████░░░░░░ 41%
⚠ insufficient evidence

DNA damage
?
NOT MEASURED

Biological age
?
CANNOT ESTIMATE

Overall state
INSUFFICIENT EVIDENCE
```

The exact visualisation can change, but the semantics must remain.

### Required UI semantics

The interface should distinguish at least:

```text
MEASURED
ESTIMATED
INFERRED
NOT MEASURED
INSUFFICIENT EVIDENCE
CONFLICTING EVIDENCE
LOW CONFIDENCE
OUTSIDE VALIDATION DOMAIN
```

These states should never be collapsed into a single numerical score.

For example:

```text
DNA damage = 0
```

is fundamentally different from:

```text
DNA damage = NOT MEASURED
```

and:

```text
DNA damage = UNKNOWN / INSUFFICIENT EVIDENCE
```

is different from both.

### No false precision

A single number such as:

```text
CELL HEALTH: 72%
```

should not be presented as the primary biological truth unless the underlying construct has a clearly defined target, calibration, reference population, uncertainty model and independent validation.

The preferred representation is the evidence profile:

```text
cell state
+ measurements
+ derived features
+ supported inferences
+ uncertainty
+ missing evidence
+ validation status
```

A summary score may eventually be provided as a convenience, but it must remain subordinate to the evidence profile and must never conceal uncertainty.

---

## Architectural consequence

These four principles imply a broader rule for the entire project:

```text
SPATIAL HIERARCHY
        +
BIOLOGICAL RELATIONSHIP GRAPH
        +
EVIDENCE / PROVENANCE GRAPH
        +
TEMPORAL HISTORY
        +
UNCERTAINTY
        ↓
BIOLOGICAL STATE
        ↓
VALIDATED INFERENCE
        ↓
RESEARCH DECISION SUPPORT
```

The Digital Biological Twin should therefore be understood as a **multi-layer evidence and relationship system**, not as a nested tree of increasingly detailed scores.

The implementation should preserve these distinctions from the data model through the API, analysis pipeline and UI.
