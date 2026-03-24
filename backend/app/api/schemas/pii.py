from typing import Literal

from pydantic import BaseModel, Field

RedactionStrategy = Literal["mask", "hash", "partial", "synthetic"]


class PiiMatchShell(BaseModel):
    entity_type: str
    start: int
    end: int
    text: str | None = None
    score: float | None = None
    source: str | None = None


class PiiDetectRequest(BaseModel):
    text: str = Field(description="Raw text that will later be inspected for PII.")


class PiiDetectResponse(BaseModel):
    status: Literal["not_implemented"]
    message: str
    matches: list[PiiMatchShell] = Field(default_factory=list)


class PiiRedactRequest(BaseModel):
    text: str = Field(description="Raw text that will later be redacted.")
    strategy_overrides: dict[str, RedactionStrategy] | None = None


class PiiRedactResponse(BaseModel):
    status: Literal["not_implemented"]
    message: str
    redacted_text: str
    matches: list[PiiMatchShell] = Field(default_factory=list)
