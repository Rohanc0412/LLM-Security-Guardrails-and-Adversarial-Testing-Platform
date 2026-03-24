from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DetectorSource(StrEnum):
    REGEX = "regex"
    SPACY = "spacy"
    PRESIDIO = "presidio"


class RedactionStrategy(StrEnum):
    MASK = "mask"
    HASH = "hash"
    PARTIAL = "partial"
    SYNTHETIC = "synthetic"


def _dedupe_sources(primary: DetectorSource, sources: tuple[DetectorSource, ...]) -> tuple[DetectorSource, ...]:
    ordered: list[DetectorSource] = []
    for source in (primary, *sources):
        if source not in ordered:
            ordered.append(source)
    return tuple(ordered)


@dataclass(slots=True)
class PIIMatch:
    entity_type: str
    start: int
    end: int
    text: str
    score: float
    primary_source: DetectorSource
    sources: tuple[DetectorSource, ...] = field(default_factory=tuple)
    source_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("start must be non-negative")
        if self.end < self.start:
            raise ValueError("end must be greater than or equal to start")
        self.sources = _dedupe_sources(self.primary_source, self.sources)
        self.source_metadata = {key: dict(value) for key, value in self.source_metadata.items()}
        self.source_metadata.setdefault(self.primary_source.value, {})

    @property
    def length(self) -> int:
        return self.end - self.start

    @property
    def span(self) -> tuple[int, int]:
        return (self.start, self.end)


@dataclass(slots=True)
class PIIDetectionResult:
    text: str
    matches: list[PIIMatch]
    detectors_run: tuple[DetectorSource, ...]

    @property
    def total_matches(self) -> int:
        return len(self.matches)


@dataclass(slots=True)
class RedactionRecord:
    match: PIIMatch
    strategy: RedactionStrategy
    replacement: str


@dataclass(slots=True)
class PIIRedactionResult:
    text: str
    redacted_text: str
    matches: list[PIIMatch]
    redactions: list[RedactionRecord]

