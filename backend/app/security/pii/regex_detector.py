from __future__ import annotations

from .models import DetectorSource, PIIMatch
from .patterns import get_compiled_patterns

DATE_HINTS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def _should_scan_pattern(entity_type: str, text: str, lowered_text: str, has_digit: bool) -> bool:
    if entity_type == "EMAIL":
        return "@" in text and "." in text
    if entity_type in {"PHONE", "SSN", "CREDIT_CARD"}:
        return has_digit
    if entity_type == "IPV4":
        return has_digit and "." in text
    if entity_type == "DATE":
        return has_digit or any(hint in lowered_text for hint in DATE_HINTS)
    return True


class RegexDetector:
    def __init__(self) -> None:
        self._patterns = get_compiled_patterns()

    def detect(self, text: str) -> list[PIIMatch]:
        if not text:
            return []

        lowered_text = text.lower()
        has_digit = any(character.isdigit() for character in text)
        matches: list[PIIMatch] = []
        for pattern in self._patterns:
            if not _should_scan_pattern(pattern.entity_type, text, lowered_text, has_digit):
                continue
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
