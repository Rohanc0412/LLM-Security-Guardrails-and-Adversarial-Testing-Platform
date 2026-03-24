from __future__ import annotations

from .models import DetectorSource, PIIMatch
from .patterns import get_compiled_patterns


class RegexDetector:
    def __init__(self) -> None:
        self._patterns = get_compiled_patterns()

    def detect(self, text: str) -> list[PIIMatch]:
        if not text:
            return []

        matches: list[PIIMatch] = []
        for pattern in self._patterns:
            for regex_match in pattern.regex.finditer(text):
                value = regex_match.group(0)
                if pattern.validator and not pattern.validator(value):
                    continue
                metadata = {
                    DetectorSource.REGEX.value: {
                        "pattern_name": pattern.name,
                        "expression": pattern.expression,
                    }
                }
                matches.append(
                    PIIMatch(
                        entity_type=pattern.entity_type,
                        start=regex_match.start(),
                        end=regex_match.end(),
                        text=value,
                        score=pattern.score,
                        primary_source=DetectorSource.REGEX,
                        source_metadata=metadata,
                    )
                )
        return matches
