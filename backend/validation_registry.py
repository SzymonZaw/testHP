"""Ground-truth and validation metadata registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationRecord:
    model_id: str
    training_dataset: str | None = None
    validation_dataset: str | None = None
    test_dataset: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    population: str | None = None
    tissue: str | None = None
    cell_type: str | None = None
    validation_status: str = "not_validated"


class ValidationRegistry:
    def __init__(self) -> None:
        self._records: dict[str, ValidationRecord] = {}

    def register(self, record: ValidationRecord) -> None:
        self._records[record.model_id] = record

    def get(self, model_id: str) -> ValidationRecord | None:
        return self._records.get(model_id)

    def status(self, model_id: str) -> str:
        record = self.get(model_id)
        return record.validation_status if record else "not_validated"


registry = ValidationRegistry()
