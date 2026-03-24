from __future__ import annotations

import re

from .models import PIIMatch

COMMON_PERSON_FALSE_POSITIVES = frozenset({"may", "june", "will"})
MONTH_PREPOSITIONS = frozenset({"in", "on", "by", "during", "through", "until", "from"})
MODAL_PREVIOUS_WORDS = frozenset({"i", "we", "you", "they", "he", "she", "it"})
MODAL_NEXT_WORDS = frozenset(
    {
        "be",
        "have",
        "need",
        "review",
        "return",
        "send",
        "confirm",
        "start",
        "continue",
        "update",
    }
)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")


def _neighbor_tokens(text: str, start: int, end: int) -> tuple[str | None, str | None]:
    previous = None
    following = None
    for token_match in TOKEN_PATTERN.finditer(text):
        token_start, token_end = token_match.span()
        if token_end <= start:
            previous = token_match.group(0).lower()
            continue
        if token_start >= end:
            following = token_match.group(0).lower()
            break
    return previous, following


def is_contextual_false_positive(text: str, match: PIIMatch) -> bool:
    token = match.text.strip().lower()
    previous, following = _neighbor_tokens(text, match.start, match.end)

    if match.entity_type == "PERSON" and token in COMMON_PERSON_FALSE_POSITIVES:
        if token == "will":
            return previous in MODAL_PREVIOUS_WORDS or following in MODAL_NEXT_WORDS
        return previous in MONTH_PREPOSITIONS or (following is not None and following.isdigit())

    if match.entity_type == "DATE" and token in {"may", "june"}:
        return following is None or not following.isdigit()

    return False
