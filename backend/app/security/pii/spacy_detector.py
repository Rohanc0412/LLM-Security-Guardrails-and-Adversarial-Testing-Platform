from __future__ import annotations

import importlib
from typing import Any, Callable

from .models import DetectorSource, PIIMatch


class SpacyDetector:
    LABEL_MAPPING = {
        "PERSON": "PERSON",
        "DATE": "DATE",
    }

    LABEL_SCORES = {
        "PERSON": 0.62,
        "DATE": 0.58,
    }

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        loader: Callable[[], Any] | None = None,
    ) -> None:
        self.model_name = model_name
        self._loader = loader
        self._nlp: Any | None = None

    def _load_model(self) -> Any | None:
        if self._nlp is not None:
            return self._nlp
        if self._loader is not None:
            self._nlp = self._loader()
            return self._nlp
        try:
            spacy = importlib.import_module("spacy")
        except ImportError:
            return None
        try:
            self._nlp = spacy.load(self.model_name)
        except Exception:
            return None
        return self._nlp

    def detect(self, text: str) -> list[PIIMatch]:
        if not text:
            return []

        nlp = self._load_model()
        if nlp is None:
            return []

        try:
            document = nlp(text)
        except Exception:
            return []

        matches: list[PIIMatch] = []
        for entity in getattr(document, "ents", ()):
            entity_type = self.LABEL_MAPPING.get(getattr(entity, "label_", ""))
            if entity_type is None:
                continue
            start = int(getattr(entity, "start_char", 0))
            end = int(getattr(entity, "end_char", start))
            if end <= start:
                continue
            label = getattr(entity, "label_", "")
            metadata = {
                DetectorSource.SPACY.value: {
                    "label": label,
                    "model_name": self.model_name,
                }
            }
            matches.append(
                PIIMatch(
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    text=text[start:end],
                    score=self.LABEL_SCORES.get(label, 0.55),
                    primary_source=DetectorSource.SPACY,
                    source_metadata=metadata,
                )
            )
        return matches
