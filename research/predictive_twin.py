"""Research-stage primitives for a multiscale predictive biological twin.

The implementations in this module are explicit *research scaffolds*. They
provide state contracts, deterministic baselines and simulation plumbing, but
do not diagnose disease, prescribe treatment, establish a validated biological
age, or demonstrate safe human lifespan extension.

The architecture is deliberately multiscale:

    molecular -> cell -> tissue -> organ -> organism

and supports both bottom-up aggregation and top-down contextual modulation.
Validated scientific models can replace the deterministic baselines without
changing the surrounding data contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Sequence


def _bounded(value: float, name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


@dataclass(frozen=True)
class MolecularState:
    """Normalized molecular state used by the research simulator."""

    dna_integrity: float = 1.0
    epigenetic_stability: float = 1.0
    gene_expression_health: float = 1.0
    protein_homeostasis: float = 1.0
    metabolic_health: float = 1.0

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            _bounded(value, name)


@dataclass(frozen=True)
class CellState:
    """Cell state with backward-compatible observable and molecular inputs."""

    cell_id: str
    health_signals: Mapping[str, float] = field(default_factory=dict)
    age_signals: Mapping[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    molecular: MolecularState = field(default_factory=MolecularState)
    function: float = 1.0
    damage: float = 0.0
    repair: float = 1.0
    senescence: float = 0.0

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id cannot be empty")
        for name in ("function", "damage", "repair", "senescence", "confidence"):
            _bounded(getattr(self, name), name)


@dataclass(frozen=True)
class CellHealthAssessment:
    cell_id: str
    health_index: float
    status: str
    confidence: float
    evidence: tuple[str, ...]
    validated: bool = False


class CellHealthModel:
    """Transparent research baseline for cell-state assessment."""

    def assess(self, state: CellState) -> CellHealthAssessment:
        values = [float(v) for v in state.health_signals.values()]
        if any(v < 0.0 or v > 1.0 for v in values):
            raise ValueError("health signals must be normalized to [0, 1]")
        if not values:
            return CellHealthAssessment(state.cell_id, 0.0, "insufficient_evidence", state.confidence, (), False)
        score = sum(values) / len(values)
        if state.confidence < 0.5:
            status = "insufficient_evidence"
        elif score >= 0.75:
            status = "research_favorable"
        elif score >= 0.45:
            status = "research_uncertain"
        else:
            status = "research_concerning"
        return CellHealthAssessment(state.cell_id, score, status, state.confidence, tuple(state.health_signals.keys()), False)


@dataclass(frozen=True)
class CellAgeEstimate:
    cell_id: str
    biological_age: float | None
    confidence: float
    missing_signals: tuple[str, ...]
    research_only: bool = True


class CellAgeModel:
    """Research-only estimator using caller-supplied calibrated features."""

    def __init__(self, weights: Mapping[str, float], intercept: float = 0.0):
        if not weights:
            raise ValueError("at least one age feature is required")
        self.weights = dict(weights)
        self.intercept = float(intercept)

    def estimate(self, state: CellState) -> CellAgeEstimate:
        missing = tuple(k for k in self.weights if k not in state.age_signals)
        if missing:
            return CellAgeEstimate(state.cell_id, None, state.confidence, missing)
        age = self.intercept + sum(self.weights[k] * float(state.age_signals[k]) for k in self.weights)
        return CellAgeEstimate(state.cell_id, float(age), state.confidence, ())


@dataclass(frozen=True)
class TissueState:
    """Aggregated tissue state with explicit cellular composition."""

    tissue_id: str
    cell_states: tuple[CellState, ...]
    function: float
    damage: float
    inflammation: float
    confidence: float

    @classmethod
    def from_cells(cls, tissue_id: str, cells: Sequence[CellState]) -> "TissueState":
        if not tissue_id.strip():
            raise ValueError("tissue_id cannot be empty")
        if not cells:
            raise ValueError("at least one cell is required")
        n = len(cells)
        function = sum(c.function for c in cells) / n
        damage = sum(c.damage for c in cells) / n
        inflammation = min(1.0, sum(c.senescence + c.damage for c in cells) / (2 * n))
        confidence = sum(c.confidence for c in cells) / n
        return cls(tissue_id, tuple(cells), function, damage, inflammation, confidence)


@dataclass(frozen=True)
class OrganState:
    """Organ-level state aggregated from one or more tissue states."""

    organ_id: str
    tissue_states: tuple[TissueState, ...]
    function: float
    reserve: float
    confidence: float

    @classmethod
    def from_tissues(cls, organ_id: str, tissues: Sequence[TissueState]) -> "OrganState":
        if not tissues:
            raise ValueError("at least one tissue is required")
        n = len(tissues)
        function = sum(t.function for t in tissues) / n
        reserve = max(0.0, min(1.0, function * (1.0 - sum(t.damage for t in tissues) / n)))
        confidence = sum(t.confidence for t in tissues) / n
        return cls(organ_id, tuple(tissues), function, reserve, confidence)


@dataclass(frozen=True)
class OrganismState:
    """Whole-person research state assembled from organ-level states."""

    subject_id: str
    organs: tuple[OrganState, ...]
    global_function: float
    reserve: float
    confidence: float

    @classmethod
    def from_organs(cls, subject_id: str, organs: Sequence[OrganState]) -> "OrganismState":
        if not subject_id.strip():
            raise ValueError("subject_id cannot be empty")
        if not organs:
            raise ValueError("at least one organ is required")
        n = len(organs)
        function = sum(o.function for o in organs) / n
        reserve = sum(o.reserve for o in organs) / n
        confidence = sum(o.confidence for o in organs) / n
        return cls(subject_id, tuple(organs), function, reserve, confidence)


@dataclass(frozen=True)
class MechanisticState:
    """Compact dynamic state used by the deterministic research baseline."""

    function: float
    damage: float
    repair: float
    senescence: float

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            _bounded(value, name)


@dataclass(frozen=True)
class MechanisticTrace:
    """One simulation step with bottom-up and top-down context."""

    time_years: float
    molecular: MolecularState
    cell: MechanisticState
    tissue_function: float
    organ_function: float
    organism_function: float


class MechanisticSimulator:
    """Deterministic toy dynamics establishing the multiscale contract."""

    def step(self, state: MechanisticState, years: float = 1.0) -> MechanisticState:
        if years < 0:
            raise ValueError("years must be non-negative")
        damage = min(1.0, state.damage + 0.02 * years - 0.01 * state.repair * years)
        repair = max(0.0, min(1.0, state.repair - 0.005 * years + 0.01 * state.function))
        senescence = max(0.0, min(1.0, state.senescence + 0.01 * damage * years))
        function = max(0.0, min(1.0, state.function - 0.015 * damage * years - 0.01 * senescence * years))
        return MechanisticState(function, damage, repair, senescence)

    def simulate_multiscale(
        self,
        molecular: MolecularState,
        cell: MechanisticState,
        *,
        years: float,
        tissue_context: float = 1.0,
        organ_context: float = 1.0,
        organism_context: float = 1.0,
        step_years: float = 1.0,
    ) -> tuple[MechanisticTrace, ...]:
        if years < 0 or step_years <= 0:
            raise ValueError("years must be >= 0 and step_years must be > 0")
        for name, value in {"tissue_context": tissue_context, "organ_context": organ_context, "organism_context": organism_context}.items():
            _bounded(value, name)
        traces: list[MechanisticTrace] = []
        current = cell
        elapsed = 0.0
        while elapsed < years:
            step = min(step_years, years - elapsed)
            current = self.step(current, step)
            feedback = (tissue_context + organ_context + organism_context) / 3.0
            function = max(0.0, min(1.0, current.function * (0.8 + 0.2 * feedback)))
            current = MechanisticState(function, current.damage, current.repair, current.senescence)
            elapsed += step
            tissue_function = max(0.0, min(1.0, current.function * tissue_context))
            organ_function = max(0.0, min(1.0, tissue_function * organ_context))
            organism_function = max(0.0, min(1.0, organ_function * organism_context))
            traces.append(MechanisticTrace(elapsed, molecular, current, tissue_function, organ_function, organism_function))
        return tuple(traces)


@dataclass(frozen=True)
class LongHorizonPrediction:
    horizon_years: float
    state: MechanisticState
    model_version: str
    uncertainty: float
    validated: bool = False


class LongHorizonPredictor:
    """Research scenarios for 5, 20, 50, 100+ year horizons."""

    DEFAULT_HORIZONS = (5.0, 20.0, 50.0, 100.0)

    def __init__(self, simulator: MechanisticSimulator, model_version: str = "toy-v1"):
        self.simulator = simulator
        self.model_version = model_version

    def predict(self, initial: MechanisticState, horizon_years: float, step_years: float = 1.0) -> LongHorizonPrediction:
        if horizon_years < 0 or step_years <= 0:
            raise ValueError("horizon_years must be >= 0 and step_years must be > 0")
        state = initial
        remaining = float(horizon_years)
        while remaining > 0:
            step = min(step_years, remaining)
            state = self.simulator.step(state, step)
            remaining -= step
        uncertainty = min(1.0, 0.05 + 0.003 * float(horizon_years))
        return LongHorizonPrediction(float(horizon_years), state, self.model_version, uncertainty, False)

    def forecast_standard_horizons(self, initial: MechanisticState, step_years: float = 1.0) -> tuple[LongHorizonPrediction, ...]:
        return tuple(self.predict(initial, h, step_years) for h in self.DEFAULT_HORIZONS)


@dataclass(frozen=True)
class RejuvenationTarget:
    node_id: str
    priority: float
    rationale: tuple[str, ...]
    action: str
    confidence: float
    evidence_status: str


class RejuvenationPlanner:
    """Ranks research candidates; it never prescribes a therapy."""

    def rank(self, nodes: Iterable[Mapping[str, object]]) -> tuple[RejuvenationTarget, ...]:
        results: list[RejuvenationTarget] = []
        for node in nodes:
            node_id = str(node.get("node_id", ""))
            if not node_id:
                raise ValueError("node_id is required")
            priority = _bounded(float(node.get("priority", 0.0)), "priority")
            confidence = _bounded(float(node.get("confidence", 0.0)), "confidence")
            evidence = _bounded(float(node.get("evidence", 0.0)), "evidence")
            rationale = tuple(str(x) for x in node.get("rationale", ()))
            requested = str(node.get("action", "monitor"))
            if evidence < 0.5 or confidence < 0.5:
                action = "insufficient_evidence"
                evidence_status = "insufficient_evidence"
            elif requested == "rejuvenate":
                action = "research_candidate_rejuvenation"
                evidence_status = "research_candidate"
            else:
                action = requested
                evidence_status = "research_candidate"
            results.append(RejuvenationTarget(node_id, priority, rationale, action, confidence, evidence_status))
        return tuple(sorted(results, key=lambda x: x.priority, reverse=True))


@dataclass
class WholeBodyTwin:
    """Hierarchical container for organism -> organ -> tissue -> cell nodes."""

    nodes: Dict[str, Mapping[str, object]] = field(default_factory=dict)
    model_version: str = "schema-v1"

    LEVELS = ("organism", "organ", "tissue", "cell", "molecular")

    def add_node(self, node_id: str, *, parent_id: str | None = None, level: str = "unknown", state: Mapping[str, object] | None = None) -> None:
        if not node_id.strip():
            raise ValueError("node_id cannot be empty")
        if level not in self.LEVELS and level != "unknown":
            raise ValueError(f"unsupported level: {level}")
        if parent_id is not None and parent_id not in self.nodes:
            raise KeyError(f"unknown parent_id: {parent_id}")
        self.nodes[node_id] = {"parent_id": parent_id, "level": level, "state": dict(state or {})}

    def descendants(self, node_id: str) -> tuple[str, ...]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        found: list[str] = []
        frontier = [node_id]
        while frontier:
            parent = frontier.pop(0)
            children = [n for n, data in self.nodes.items() if data.get("parent_id") == parent]
            found.extend(children)
            frontier.extend(children)
        return tuple(found)

    def ancestors(self, node_id: str) -> tuple[str, ...]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        found: list[str] = []
        current = self.nodes[node_id].get("parent_id")
        while current is not None:
            found.append(str(current))
            current = self.nodes[str(current)].get("parent_id")
        return tuple(found)


@dataclass(frozen=True)
class LongevityScenario:
    """Research scenario; not a promise or prediction of lifespan."""

    target_years: float
    predicted_function: float
    uncertainty: float
    model_version: str
    interpretation: str = "research_scenario_only"


class LongevityScenarioModel:
    """Converts long-horizon state projections into explicit research scenarios."""

    def __init__(self, predictor: LongHorizonPredictor):
        self.predictor = predictor

    def scenario(self, initial: MechanisticState, target_years: float) -> LongevityScenario:
        prediction = self.predictor.predict(initial, target_years)
        return LongevityScenario(target_years, prediction.state.function, prediction.uncertainty, prediction.model_version)


@dataclass(frozen=True)
class ClinicalValidationPlan:
    """Gate model readiness through increasingly demanding validation phases."""

    phases: tuple[str, ...] = (
        "unit_and_deterministic_validation",
        "analytical_validation",
        "benchmark_dataset_validation",
        "internal_validation",
        "external_validation",
        "longitudinal_cohort_validation",
        "prospective_validation",
        "clinical_utility",
        "safety_and_regulatory_review",
    )
    status: str = "not_validated"
    required: bool = True

    def next_phase(self, completed: Sequence[str]) -> str | None:
        done = set(completed)
        return next((phase for phase in self.phases if phase not in done), None)

    def is_clinically_ready(self, completed: Sequence[str]) -> bool:
        return all(phase in set(completed) for phase in self.phases)
