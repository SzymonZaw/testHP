"""Lightweight, dependency-free benchmark orchestration primitives.

Adapters for heavy external models can plug into this interface without vendoring
model weights into testHP. The runner records provenance and uncertainty metadata
rather than treating any model output as ground truth.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping


@dataclass(frozen=True)
class ModelResult:
    model: str
    task: str
    score: float
    sample_count: int
    uncertainty: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkReport:
    task: str
    results: tuple[ModelResult, ...]

    def ranked(self) -> tuple[ModelResult, ...]:
        return tuple(sorted(self.results, key=lambda r: r.score, reverse=True))


class BenchmarkRunner:
    """Run compatible model adapters against the same input and collect results."""

    def run(
        self,
        task: str,
        cases: Iterable[Any],
        adapters: Mapping[str, Callable[[Any], ModelResult]],
    ) -> BenchmarkReport:
        cases = tuple(cases)
        results: list[ModelResult] = []
        for name, adapter in adapters.items():
            outputs = [adapter(case) for case in cases]
            if not outputs:
                continue
            # Adapters return normalized per-case scores; aggregate conservatively.
            score = sum(item.score for item in outputs) / len(outputs)
            uncertainty_values = [item.uncertainty for item in outputs if item.uncertainty is not None]
            uncertainty = (
                sum(uncertainty_values) / len(uncertainty_values)
                if uncertainty_values else None
            )
            results.append(
                ModelResult(
                    model=name,
                    task=task,
                    score=score,
                    sample_count=len(outputs),
                    uncertainty=uncertainty,
                    provenance={"adapter": name},
                )
            )
        return BenchmarkReport(task=task, results=tuple(results))
