from __future__ import annotations

from backend.app.security.pii.models import DetectorSource, PIIMatch, RedactionStrategy
from backend.app.security.pii.service import PIIService


class StubDetector:
    def __init__(self, matches: list[PIIMatch]) -> None:
        self._matches = matches

    def detect(self, text: str) -> list[PIIMatch]:
        return list(self._matches)


def _match(text: str, span_text: str, entity_type: str, source: DetectorSource, score: float = 0.9) -> PIIMatch:
    start = text.index(span_text)
    end = start + len(span_text)
    return PIIMatch(
        entity_type=entity_type,
        start=start,
        end=end,
        text=span_text,
        score=score,
        primary_source=source,
        source_metadata={source.value: {"source_name": source.value}},
    )


def test_service_detect_merges_multi_source_matches() -> None:
    text = "We will email jane@example.com"
    regex_match = _match(text, "jane@example.com", "EMAIL", DetectorSource.REGEX, 0.99)
    presidio_match = _match(text, "jane@example.com", "EMAIL", DetectorSource.PRESIDIO, 0.88)
    false_positive = _match(text, "will", "PERSON", DetectorSource.SPACY, 0.60)

    service = PIIService(
        regex_detector=StubDetector([regex_match]),
        spacy_detector=StubDetector([false_positive]),
        presidio_detector=StubDetector([presidio_match]),
    )

    result = service.detect(text)

    assert result.total_matches == 1
    assert set(result.matches[0].sources) == {DetectorSource.REGEX, DetectorSource.PRESIDIO}
    assert result.detectors_run == (
        DetectorSource.REGEX,
        DetectorSource.SPACY,
        DetectorSource.PRESIDIO,
    )


def test_service_redact_supports_strategy_overrides() -> None:
    text = "Email jane@example.com and SSN 123-45-6789"
    email = _match(text, "jane@example.com", "EMAIL", DetectorSource.REGEX, 0.99)
    ssn = _match(text, "123-45-6789", "SSN", DetectorSource.REGEX, 0.99)

    service = PIIService(
        regex_detector=StubDetector([email, ssn]),
        spacy_detector=StubDetector([]),
        presidio_detector=StubDetector([]),
        enable_spacy=False,
        enable_presidio=False,
        hash_salt="fixed-salt",
    )

    result = service.redact(
        text,
        strategy_overrides={
            "EMAIL": RedactionStrategy.PARTIAL,
            "SSN": RedactionStrategy.HASH,
        },
    )

    assert "j***@e******.com" in result.redacted_text
    assert "<SSN_HASH:" in result.redacted_text


def test_service_detect_and_redact_handles_empty_and_already_redacted_text() -> None:
    service = PIIService(
        regex_detector=StubDetector([]),
        spacy_detector=StubDetector([]),
        presidio_detector=StubDetector([]),
        enable_spacy=False,
        enable_presidio=False,
    )

    assert service.detect("").total_matches == 0
    assert service.detect_and_redact("[EMAIL_REDACTED]").redacted_text == "[EMAIL_REDACTED]"
