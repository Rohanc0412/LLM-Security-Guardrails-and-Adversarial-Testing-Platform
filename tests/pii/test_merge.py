from __future__ import annotations

from backend.app.security.pii.merge import merge_pii_matches
from backend.app.security.pii.models import DetectorSource, PIIMatch


def _make_match(
    text: str,
    span_text: str,
    entity_type: str,
    source: DetectorSource,
    score: float,
    start: int | None = None,
) -> PIIMatch:
    actual_start = text.index(span_text) if start is None else start
    actual_end = actual_start + len(span_text)
    return PIIMatch(
        entity_type=entity_type,
        start=actual_start,
        end=actual_end,
        text=text[actual_start:actual_end],
        score=score,
        primary_source=source,
        source_metadata={source.value: {"source_name": source.value}},
    )


def test_merge_deduplicates_exact_duplicates_and_preserves_sources() -> None:
    text = "Email jane@example.com"
    regex_match = _make_match(text, "jane@example.com", "EMAIL", DetectorSource.REGEX, 0.99)
    presidio_match = _make_match(text, "jane@example.com", "EMAIL", DetectorSource.PRESIDIO, 0.91)

    merged = merge_pii_matches(text, [regex_match, presidio_match])

    assert len(merged) == 1
    assert set(merged[0].sources) == {DetectorSource.REGEX, DetectorSource.PRESIDIO}
    assert "regex" in merged[0].source_metadata
    assert "presidio" in merged[0].source_metadata


def test_merge_prefers_precise_match_over_generic_overlap() -> None:
    text = "Reach jane@example.com today"
    email_match = _make_match(text, "jane@example.com", "EMAIL", DetectorSource.REGEX, 0.99)
    person_match = _make_match(text, "jane@example.com", "PERSON", DetectorSource.SPACY, 0.70)

    merged = merge_pii_matches(text, [person_match, email_match])

    assert len(merged) == 1
    assert merged[0].entity_type == "EMAIL"


def test_merge_filters_common_false_positives_with_context_hooks() -> None:
    text = "We will review it in June 2024."
    will_match = _make_match(text, "will", "PERSON", DetectorSource.SPACY, 0.65)
    june_person_match = _make_match(text, "June", "PERSON", DetectorSource.SPACY, 0.65)
    june_date_match = _make_match(text, "June", "DATE", DetectorSource.SPACY, 0.60)

    merged = merge_pii_matches(text, [will_match, june_person_match, june_date_match])

    assert len(merged) == 1
    assert merged[0].entity_type == "DATE"
    assert merged[0].text == "June"
