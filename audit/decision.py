"""Evidence-first, auditable research decision records."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


Decision = Literal["measure_again", "request_modality", "expert_review", "insufficient_evidence", "continue_monitoring"]


@dataclass(frozen=True)
class EvidenceRef:
    source: str
    value: str
    model_version: Optional[str] = None


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    created_at: datetime
    decision: Decision
    rationale: str
    evidence: tuple[EvidenceRef, ...] = ()
    reviewer: Optional[str] = None


class DecisionAuditLog:
    """Append-only in-memory audit log for research workflows."""

    def __init__(self) -> None:
        self._records: list[DecisionRecord] = []

    def append(self, record: DecisionRecord) -> None:
        if any(item.decision_id == record.decision_id for item in self._records):
            raise ValueError("decision_id already exists")
        self._records.append(record)

    def records(self) -> tuple[DecisionRecord, ...]:
        return tuple(self._records)
