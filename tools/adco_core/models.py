"""Typed records for evidence-first ADCO workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceChunk:
    chunk_id: str
    source_event_id: str
    source_path: str
    media_type: str
    page: int | None
    slide: int | None
    start_line: int | None
    end_line: int | None
    text: str
    sha256: str
    inspection_status: str
    field_path: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceChunk":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: payload.get(key) for key in allowed})


@dataclass(frozen=True)
class FactInventoryItem:
    fact_key: str
    state: str
    value: str
    evidence_refs: list[str]
    confidence: float
    owner: str
    blocking: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "FactInventoryItem":
        return cls(
            fact_key=str(payload.get("fact_key", "")),
            state=str(payload.get("state", "")),
            value=str(payload.get("value", "")),
            evidence_refs=[str(item) for item in payload.get("evidence_refs", [])],
            confidence=float(payload.get("confidence", 0.0)),
            owner=str(payload.get("owner", "")),
            blocking=bool(payload.get("blocking", False)),
        )
