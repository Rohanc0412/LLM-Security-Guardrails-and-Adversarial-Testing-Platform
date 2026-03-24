from __future__ import annotations

from backend.app.security.pii.models import DetectorSource, PIIMatch, RedactionStrategy
from backend.app.security.pii.redaction import redact_text


def _match(text: str, span_text: str, entity_type: str) -> PIIMatch:
    start = text.index(span_text)
    end = start + len(span_text)
    return PIIMatch(
        entity_type=entity_type,
        start=start,
        end=end,
        text=span_text,
        score=0.99,
        primary_source=DetectorSource.REGEX,
        source_metadata={"regex": {"pattern_name": entity_type.lower()}},
    )


def test_redaction_hash_is_deterministic() -> None:
    text = "Email jane@example.com"
    matches = [_match(text, "jane@example.com", "EMAIL")]

    first = redact_text(text, matches, strategy_overrides={"EMAIL": RedactionStrategy.HASH}, hash_salt="fixed-salt")
    second = redact_text(text, matches, strategy_overrides={"EMAIL": RedactionStrategy.HASH}, hash_salt="fixed-salt")

    assert first.redacted_text == second.redacted_text
    assert first.redactions[0].replacement.startswith("<EMAIL_HASH:")


def test_redaction_partial_preserves_useful_structure() -> None:
    text = "Email jane.doe@example.com and phone (212) 555-0100"
    matches = [
        _match(text, "jane.doe@example.com", "EMAIL"),
        _match(text, "(212) 555-0100", "PHONE"),
    ]

    result = redact_text(
        text,
        matches,
        strategy_overrides={
            "EMAIL": RedactionStrategy.PARTIAL,
            "PHONE": RedactionStrategy.PARTIAL,
        },
    )

    assert "j***.***@e******.com" in result.redacted_text
    assert "(***) ***-0100" in result.redacted_text


def test_redaction_synthetic_reuses_same_placeholder_for_repeated_values() -> None:
    text = "jane@example.com and jane@example.com"
    first_start = text.index("jane@example.com")
    second_start = text.index("jane@example.com", first_start + 1)
    matches = [
        PIIMatch(
            entity_type="EMAIL",
            start=first_start,
            end=first_start + len("jane@example.com"),
            text="jane@example.com",
            score=0.99,
            primary_source=DetectorSource.REGEX,
            source_metadata={"regex": {"pattern_name": "email"}},
        ),
        PIIMatch(
            entity_type="EMAIL",
            start=second_start,
            end=second_start + len("jane@example.com"),
            text="jane@example.com",
            score=0.99,
            primary_source=DetectorSource.REGEX,
            source_metadata={"regex": {"pattern_name": "email"}},
        ),
    ]

    result = redact_text(text, matches, strategy_overrides={"EMAIL": RedactionStrategy.SYNTHETIC})

    assert result.redacted_text.count("<EMAIL_SYNTHETIC_0001>") == 2


def test_redaction_applies_replacements_end_to_start() -> None:
    text = "Email jane@example.com then SSN 123-45-6789"
    matches = [
        _match(text, "123-45-6789", "SSN"),
        _match(text, "jane@example.com", "EMAIL"),
    ]

    result = redact_text(text, matches, strategy_overrides={"DEFAULT": RedactionStrategy.MASK})

    assert result.redacted_text == "Email ****@*******.*** then SSN ***-**-****"


def test_redaction_accepts_string_strategy_overrides() -> None:
    text = "Email jane@example.com"
    matches = [_match(text, "jane@example.com", "EMAIL")]

    result = redact_text(text, matches, strategy_overrides={"EMAIL": "partial"})

    assert result.redactions[0].strategy == RedactionStrategy.PARTIAL
    assert result.redacted_text == "Email j***@e******.com"
