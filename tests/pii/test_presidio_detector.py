from __future__ import annotations

from types import SimpleNamespace

from backend.app.security.pii.presidio_detector import PresidioDetector


def test_presidio_detector_normalizes_results_and_metadata() -> None:
    class FakeAnalyzer:
        def analyze(self, text: str, language: str):
            return [
                SimpleNamespace(
                    entity_type="EMAIL_ADDRESS",
                    start=6,
                    end=22,
                    score=0.88,
                    analysis_explanation=SimpleNamespace(recognizer="EmailRecognizer", pattern_name="email"),
                )
            ]

    detector = PresidioDetector(analyzer_provider=FakeAnalyzer)
    matches = detector.detect("Email jane@example.com")

    assert len(matches) == 1
    assert matches[0].entity_type == "EMAIL"
    assert matches[0].source_metadata["presidio"]["recognizer"] == "EmailRecognizer"
    assert matches[0].source_metadata["presidio"]["pattern_name"] == "email"


def test_presidio_detector_handles_analyzer_errors() -> None:
    class BrokenAnalyzer:
        def analyze(self, text: str, language: str):
            raise RuntimeError("boom")

    detector = PresidioDetector(analyzer_provider=BrokenAnalyzer)
    assert detector.detect("Email jane@example.com") == []
