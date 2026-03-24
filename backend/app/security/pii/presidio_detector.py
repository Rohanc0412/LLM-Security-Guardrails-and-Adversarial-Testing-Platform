from __future__ import annotations

import importlib
from typing import Any, Callable

from .models import DetectorSource, PIIMatch


class PresidioDetector:
    ENTITY_MAPPING = {
        "EMAIL_ADDRESS": "EMAIL",
        "PHONE_NUMBER": "PHONE",
        "US_SSN": "SSN",
        "CREDIT_CARD": "CREDIT_CARD",
        "IP_ADDRESS": "IPV4",
        "DATE_TIME": "DATE",
        "PERSON": "PERSON",
    }

    def __init__(
        self,
        language: str = "en",
        analyzer_provider: Callable[[], Any] | None = None,
    ) -> None:
        self.language = language
        self._analyzer_provider = analyzer_provider
        self._analyzer: Any | None = None
        self._load_failed = False

    def _load_analyzer(self) -> Any | None:
        if self._analyzer is not None:
            return self._analyzer
        if self._load_failed:
            return None
        if self._analyzer_provider is not None:
            try:
                self._analyzer = self._analyzer_provider()
            except Exception:
                self._load_failed = True
                return None
            if self._analyzer is None:
                self._load_failed = True
                return None
            return self._analyzer
        try:
            module = importlib.import_module("presidio_analyzer")
        except ImportError:
            self._load_failed = True
            return None
        engine_class = getattr(module, "AnalyzerEngine", None)
        if engine_class is None:
            self._load_failed = True
            return None
        try:
            self._analyzer = engine_class()
        except Exception:
            self._load_failed = True
            return None
        return self._analyzer

    def detect(self, text: str) -> list[PIIMatch]:
        if not text or not any(character.isalnum() for character in text):
            return []

        analyzer = self._load_analyzer()
        if analyzer is None:
            return []

        try:
            results = analyzer.analyze(text=text, language=self.language)
        except Exception:
            return []

        matches: list[PIIMatch] = []
        for result in results or ():
            raw_type = getattr(result, "entity_type", "")
            entity_type = self.ENTITY_MAPPING.get(raw_type)
            if entity_type is None:
                continue

            start = int(getattr(result, "start", 0))
            end = int(getattr(result, "end", start))
            if start < 0 or end <= start or end > len(text):
                continue

            explanation = getattr(result, "analysis_explanation", None)
            metadata = {
                DetectorSource.PRESIDIO.value: {
                    "entity_type": raw_type,
                    "language": self.language,
                }
            }
            if explanation is not None:
                recognizer = getattr(explanation, "recognizer", None) or getattr(explanation, "recognizer_name", None)
                if recognizer:
                    metadata[DetectorSource.PRESIDIO.value]["recognizer"] = str(recognizer)
                pattern_name = getattr(explanation, "pattern_name", None)
                if pattern_name:
                    metadata[DetectorSource.PRESIDIO.value]["pattern_name"] = str(pattern_name)

            matches.append(
                PIIMatch(
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    text=text[start:end],
                    score=float(getattr(result, "score", 0.0) or 0.0),
                    primary_source=DetectorSource.PRESIDIO,
                    source_metadata=metadata,
                )
            )
        return matches
