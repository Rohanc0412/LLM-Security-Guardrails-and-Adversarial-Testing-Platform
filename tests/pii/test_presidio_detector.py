from __future__ import annotations

import importlib
from types import SimpleNamespace

from backend.app.security.pii.presidio_detector import PresidioDetector


def test_presidio_detector_normalizes_results_and_metadata() -> None:
    load_count = {"count": 0}

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

    def analyzer_provider() -> FakeAnalyzer:
        load_count["count"] += 1
        return FakeAnalyzer()

    detector = PresidioDetector(analyzer_provider=analyzer_provider)
    matches = detector.detect("Email jane@example.com")
    detector.detect("Email jane@example.com")

    assert len(matches) == 1
    assert load_count["count"] == 1
    assert matches[0].entity_type == "EMAIL"
    assert matches[0].source_metadata["presidio"]["recognizer"] == "EmailRecognizer"
    assert matches[0].source_metadata["presidio"]["pattern_name"] == "email"


def test_presidio_detector_handles_analyzer_errors() -> None:
    class BrokenAnalyzer:
        def analyze(self, text: str, language: str):
            raise RuntimeError("boom")

    detector = PresidioDetector(analyzer_provider=BrokenAnalyzer)
    assert detector.detect("Email jane@example.com") == []


def test_presidio_detector_returns_empty_when_dependency_is_missing(monkeypatch) -> None:
    import_attempts = {"count": 0}

    def fake_import(name: str):
        if name == "presidio_analyzer":
            import_attempts["count"] += 1
            raise ImportError
        return importlib.import_module(name)

    monkeypatch.setattr("backend.app.security.pii.presidio_detector.importlib.import_module", fake_import)

    detector = PresidioDetector()
    assert detector.detect("Email jane@example.com") == []
    assert detector.detect("Email jane@example.com") == []
    assert import_attempts["count"] == 1


def test_presidio_detector_filters_invalid_and_unsupported_results() -> None:
    class FakeAnalyzer:
        def analyze(self, text: str, language: str):
            return [
                SimpleNamespace(entity_type="UNKNOWN", start=0, end=5, score=0.1, analysis_explanation=None),
                SimpleNamespace(entity_type="EMAIL_ADDRESS", start=-1, end=5, score=0.9, analysis_explanation=None),
                SimpleNamespace(entity_type="EMAIL_ADDRESS", start=6, end=200, score=0.9, analysis_explanation=None),
                SimpleNamespace(entity_type="EMAIL_ADDRESS", start=6, end=22, score=0.88, analysis_explanation=None),
            ]

    detector = PresidioDetector(analyzer_provider=FakeAnalyzer)
    matches = detector.detect("Email jane@example.com")

    assert len(matches) == 1
    assert matches[0].text == "jane@example.com"
