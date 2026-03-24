from typing import Any, Literal

from pydantic import BaseModel, Field

RedactionStrategy = Literal["mask", "hash", "partial", "synthetic"]
DetectorSource = Literal["regex", "spacy", "presidio"]


class PiiMatchResponse(BaseModel):
    entity_type: str
    start: int
    end: int = Field(description="Exclusive end index for the detected span.")
    text: str
    score: float
    primary_source: DetectorSource
    sources: list[DetectorSource] = Field(default_factory=list)
    source_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)


class PiiRedactionRecordResponse(BaseModel):
    entity_type: str
    start: int
    end: int
    strategy: RedactionStrategy
    replacement: str


class PiiDetectRequest(BaseModel):
    text: str = Field(description="Raw text to inspect for PII.")


class PiiDetectResponse(BaseModel):
    status: Literal["ok"]
    total_matches: int = 0
    detectors_run: list[DetectorSource] = Field(default_factory=list)
    matches: list[PiiMatchResponse] = Field(default_factory=list)


class PiiRedactRequest(BaseModel):
    text: str = Field(description="Raw text to redact.")
    strategy_overrides: dict[str, RedactionStrategy] | None = None


class PiiRedactResponse(BaseModel):
    status: Literal["ok"]
    redacted_text: str
    total_matches: int = 0
    matches: list[PiiMatchResponse] = Field(default_factory=list)
    redactions: list[PiiRedactionRecordResponse] = Field(default_factory=list)
