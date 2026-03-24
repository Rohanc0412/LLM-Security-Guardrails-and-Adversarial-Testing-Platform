from __future__ import annotations

import importlib
from types import SimpleNamespace

from backend.app.security.pii.spacy_detector import SpacyDetector


def test_spacy_detector_lazy_loads_once_and_normalizes_entities() -> None:
    load_count = {"count": 0}

    class FakeNLP:
        def __call__(self, text: str) -> SimpleNamespace:
            return SimpleNamespace(
                ents=[
                    SimpleNamespace(label_="PERSON", start_char=0, end_char=5),
                    SimpleNamespace(label_="DATE", start_char=9, end_char=13),
                ]
            )

    def loader() -> FakeNLP:
        load_count["count"] += 1
        return FakeNLP()

    detector = SpacyDetector(loader=loader)
    first = detector.detect("Alice on June")
    second = detector.detect("Alice on June")

    assert load_count["count"] == 1
    assert [match.entity_type for match in first] == ["PERSON", "DATE"]
    assert second


def test_spacy_detector_returns_empty_when_dependency_is_missing(monkeypatch) -> None:
    def fake_import(name: str):
        if name == "spacy":
            raise ImportError
        return importlib.import_module(name)

    monkeypatch.setattr("backend.app.security.pii.spacy_detector.importlib.import_module", fake_import)

    assert SpacyDetector().detect("Alice") == []
