"""Subject identity for longitudinal biological monitoring."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Person:
    id: str
    birth_date: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Person id cannot be empty")
