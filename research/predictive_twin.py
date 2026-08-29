"""Research primitives for the long-term predictive digital twin roadmap.

Important: these components provide explicit, deterministic baselines and data
contracts. They do NOT claim clinical validity, diagnose disease, or establish
that a person can safely live to a particular age. Scientific validation must
replace the placeholder models before clinical use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class CellState:
    """Observed/derived cell features on normalized research scales."""

    cell_id: str
    health_signals: Mapping[str, float] = field(default_factory=dict)
    age_signals: Mapping[str, float] = field(default_factory=dict)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class CellHealthAssessment:
    cell_id: str
    health_index: float
    status: str
    confidence: float
    evidence: tuple[str, ...]
    validated: bool = False


class CellHealthModel:
    """Transparent research baseline for cell-state assessment.

    This intentionally returns a *research index*, not a diagnosis. Inputs are
    expected to be normalized to [0, 1], where higher values mean healthier
    evidence for that signal.
    """

    def assess(self, state: CellState) -> CellHealthAssessment:
        values = [float(v) for v in state.health_signals.values()]
        if any(v < 0.0 or v > 1.0 for v in values):
            raise ValueError("health signals must be normalized to [0, 1]")
        if not values:
            return CellHealthAssessment(
                state.cell_id, 0.0, "insufficient_evidence", state.confidence, (), False
            )
        score = sum(values) / len(values)
        if state.confidence < 0.5:
            status = "insufficient_evidence"
        elif score >= 0.75:
            status = "research_favorable"
        elif score >= 0.45:
            status = "research_uncertain"
        else:
            status = "research_concerning"
        return CellHealthAssessment(
            state.cell_id, score, status, state.confidence,
            tuple(state.health_signals.keys()), False
        )


@dataclass(frozen=True)
class CellAgeEstimate:
    cell_id: str
    biological_age: float | None
    confidence: float
    missing_signals: tuple[str, ...]
    research_only: bool = True


class CellAgeModel:
    """Research-only cell-age estimator using a calibrated feature contract.

    The weights are supplied by the caller; no biological-age truth is hard
    coded into the package. This prevents a placeholder score being mistaken
    for a validated biological clock.
    """

    def __init__(self, weights: Mapping[str, float], intercept: float = 0.0):
        if not weights:
            raise ValueError("at least one age feature is required")
        self.weights = dict(weights)
        self.intercept = float(intercept)

    def estimate(self, state: CellState) -> CellAgeEstimate:
        missing = tuple(k for k in self.weights if k not in state.age_signals)
        if missing:
            return CellAgeEstimate(state.cell_id, None, state.confidence, missing)
        age = self.intercept + sum(
            self.weights[k] * float(state.age_signals[k]) for k in self.weights
        )
        return CellAgeEstimate(state.cell_id, float(age), state.confidence, ())


@dataclass(frozen=True)
class MechanisticState:
    """Small state vector for a future mechanistic model."""

    function: float
    damage: float
    repair: float
    senescence: float

    def __post_init__(self) -> None:
        values = (self.function, self.damage, self.repair, self.senescence)
        if any(v < 0.0 or v > 1.0 for v in values):
            raise ValueError("mechanistic state values must be in [0, 1]")


class MechanisticSimulator:
    """Deterministic toy dynamics used only to establish simulation contracts."""

    def step(self, state: MechanisticState, years: float = 1.0) -> MechanisticState:
        if years < 0:
            raise ValueError("years must be non-negative")
        damage = min(1.0, state.damage + 0.02 * years - 0.01 * state.repair * years)
        repair = max(0.0, min(1.0, state.repair - 0.005 * years + 0.01 * state.function))
        senescence = max(0.0, min(1.0, state.senescence + 0.01 * damage * years))
        function = max(0.0, min(1.0, state.function - 0.015 * damage * years - 0.01 * senescence * years))
        return MechanisticState(function, damage, repair, senescence)


@dataclass(frozen=True)
class LongHorizonPrediction:
    horizon_years: float
    state: MechanisticState
    model_version: str
    validated: bool = False


class LongHorizonPredictor:
    """Produces research scenarios for 20–100+ year horizons."""

    def __init__(self, simulator: MechanisticSimulator, model_version: str = "toy-v0"):
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
        return LongHorizonPrediction(horizon_years, state, self.model_version, False)


@dataclass(frozen=True)
class RejuvenationTarget:
    node_id: str
    priority: float
    rationale: tuple[str, ...]
    action: str
    confidence: float


class RejuvenationPlanner:
    """Ranks candidate nodes; it does not prescribe treatment."""

    def rank(self, nodes: Iterable[Mapping[str, object]]) -> tuple[RejuvenationTarget, ...]:
        results = []
        for node in nodes:
            node_id = str(node.get("node_id", ""))
            if not node_id:
                raise ValueError("node_id is required")
            priority = float(node.get("priority", 0.0))
            confidence = float(node.get("confidence", 0.0))
            rationale = tuple(str(x) for x in node.get("rationale", ()))
            action = str(node.get("action", "monitor"))
            if not 0 <= priority <= 1 or not 0 <= confidence <= 1:
                raise ValueError("priority and confidence must be in [0, 1]")
            results.append(RejuvenationTarget(node_id, priority, rationale, action, confidence))
        return tuple(sorted(results, key=lambda x: x.priority, reverse=True))


@dataclass
class WholeBodyTwin:
    """Hierarchical container for future whole-body predictive modelling."""

    nodes: Dict[str, Mapping[str, object]] = field(default_factory=dict)
    model_version: str = "schema-v0"

    def add_node(self, node_id: str, *, parent_id: str | None = None, level: str = "unknown", state: Mapping[str, object] | None = None) -> None:
        if not node_id.strip():
            raise ValueError("node_id cannot be empty")
        if parent_id is not None and parent_id not in self.nodes:
            raise KeyError(f"unknown parent_id: {parent_id}")
        self.nodes[node_id] = {
            "parent_id": parent_id,
            "level": level,
            "state": dict(state or {}),
        }

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


@dataclass(frozen=True)
class ClinicalValidationPlan:
    phases: tuple[str, ...] = (
        "analytical_validation",
        "internal_validation",
        "external_validation",
        "prospective_validation",
        "clinical_utility",
        "regulatory_safety_review",
    )
    status: str = "not_validated"
    required: bool = True

    def next_phase(self, completed: Sequence[str]) -> str | None:
        done = set(completed)
        return next((phase for phase in self.phases if phase not in done), None)
