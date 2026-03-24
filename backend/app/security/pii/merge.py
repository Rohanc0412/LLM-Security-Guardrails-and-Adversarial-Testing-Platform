from __future__ import annotations

from .context import is_contextual_false_positive
from .models import DetectorSource, PIIMatch

SOURCE_BONUS = {
    DetectorSource.REGEX: 0.10,
    DetectorSource.PRESIDIO: 0.06,
    DetectorSource.SPACY: 0.03,
}

ENTITY_BONUS = {
    "EMAIL": 0.16,
    "PHONE": 0.15,
    "SSN": 0.15,
    "CREDIT_CARD": 0.15,
    "IPV4": 0.15,
    "DATE": 0.08,
    "PERSON": 0.05,
}

PRECISE_TYPES = frozenset({"EMAIL", "PHONE", "SSN", "CREDIT_CARD", "IPV4"})


def _match_rank(match: PIIMatch) -> float:
    corroboration_bonus = min(len(match.sources) - 1, 3) * 0.03
    source_bonus = SOURCE_BONUS.get(match.primary_source, 0.0)
    entity_bonus = ENTITY_BONUS.get(match.entity_type, 0.0)
    length_bonus = min(match.length, 32) / 1000
    return match.score + corroboration_bonus + source_bonus + entity_bonus + length_bonus


def _merge_exact_duplicates(existing: PIIMatch, incoming: PIIMatch) -> PIIMatch:
    metadata = {key: dict(value) for key, value in existing.source_metadata.items()}
    for source, details in incoming.source_metadata.items():
        metadata[source] = dict(details)

    combined_sources = tuple(dict.fromkeys((*existing.sources, *incoming.sources)))
    if _match_rank(incoming) > _match_rank(existing):
        primary_source = incoming.primary_source
        score = incoming.score
    else:
        primary_source = existing.primary_source
        score = existing.score

    return PIIMatch(
        entity_type=existing.entity_type,
        start=existing.start,
        end=existing.end,
        text=existing.text,
        score=max(existing.score, incoming.score, score),
        primary_source=primary_source,
        sources=combined_sources,
        source_metadata=metadata,
    )


def _prefers_precise_match(left: PIIMatch, right: PIIMatch) -> bool:
    return left.entity_type in PRECISE_TYPES and right.entity_type not in PRECISE_TYPES


def _choose_preferred(left: PIIMatch, right: PIIMatch) -> PIIMatch:
    if _prefers_precise_match(left, right):
        return left
    if _prefers_precise_match(right, left):
        return right

    left_rank = _match_rank(left)
    right_rank = _match_rank(right)
    if abs(left_rank - right_rank) < 0.03 and left.length != right.length:
        return left if left.length > right.length else right
    return left if left_rank >= right_rank else right


def merge_pii_matches(text: str, matches: list[PIIMatch]) -> list[PIIMatch]:
    exact_matches: dict[tuple[int, int, str, str], PIIMatch] = {}
    for match in matches:
        if not match.text:
            continue
        if is_contextual_false_positive(text, match):
            continue
        key = (match.start, match.end, match.entity_type, match.text.lower())
        if key in exact_matches:
            exact_matches[key] = _merge_exact_duplicates(exact_matches[key], match)
        else:
            exact_matches[key] = match

    sorted_matches = sorted(
        exact_matches.values(),
        key=lambda item: (item.start, item.end, -_match_rank(item)),
    )

    merged: list[PIIMatch] = []
    for candidate in sorted_matches:
        if not merged:
            merged.append(candidate)
            continue
        current = merged[-1]
        if candidate.start >= current.end:
            merged.append(candidate)
            continue
        preferred = _choose_preferred(current, candidate)
        merged[-1] = preferred

    return merged
