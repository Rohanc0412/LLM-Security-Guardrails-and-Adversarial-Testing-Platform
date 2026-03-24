from __future__ import annotations

from typing import Mapping, Protocol

from .merge import merge_pii_matches
from .models import DetectorSource, PIIDetectionResult, PIIMatch, PIIRedactionResult, RedactionStrategy
from .presidio_detector import PresidioDetector
from .redaction import DEFAULT_HASH_SALT, redact_text
from .regex_detector import RegexDetector
from .spacy_detector import SpacyDetector


class Detector(Protocol):
    def detect(self, text: str) -> list[PIIMatch]:
        ...


class PIIService:
    def __init__(
        self,
        regex_detector: Detector | None = None,
        spacy_detector: Detector | None = None,
        presidio_detector: Detector | None = None,
        enable_spacy: bool = True,
        enable_presidio: bool = True,
        hash_salt: str = DEFAULT_HASH_SALT,
    ) -> None:
        self.regex_detector = regex_detector or RegexDetector()
        self.spacy_detector = spacy_detector or SpacyDetector()
        self.presidio_detector = presidio_detector or PresidioDetector()
        self.enable_spacy = enable_spacy
        self.enable_presidio = enable_presidio
        self.hash_salt = hash_salt

    def detect(self, text: str) -> PIIDetectionResult:
        detectors_run = [DetectorSource.REGEX]
        matches = self.regex_detector.detect(text)

        if self.enable_spacy:
            detectors_run.append(DetectorSource.SPACY)
            matches.extend(self.spacy_detector.detect(text))

        if self.enable_presidio:
            detectors_run.append(DetectorSource.PRESIDIO)
            matches.extend(self.presidio_detector.detect(text))

        merged_matches = merge_pii_matches(text, matches)
        return PIIDetectionResult(
            text=text,
            matches=merged_matches,
            detectors_run=tuple(detectors_run),
        )

    def redact(
        self,
        text: str,
        strategy_overrides: Mapping[str, RedactionStrategy | str] | None = None,
    ) -> PIIRedactionResult:
        detection_result = self.detect(text)
        return redact_text(
            text=text,
            matches=detection_result.matches,
            strategy_overrides=strategy_overrides,
            hash_salt=self.hash_salt,
        )

    def detect_and_redact(
        self,
        text: str,
        strategy_overrides: Mapping[str, RedactionStrategy | str] | None = None,
    ) -> PIIRedactionResult:
        return self.redact(text, strategy_overrides=strategy_overrides)
