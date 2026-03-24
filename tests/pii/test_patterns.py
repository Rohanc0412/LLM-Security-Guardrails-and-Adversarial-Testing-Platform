from __future__ import annotations

from backend.app.security.pii.patterns import get_compiled_patterns, get_pattern_definitions


def test_pattern_definitions_are_cached() -> None:
    assert get_pattern_definitions() is get_pattern_definitions()


def test_compiled_patterns_are_cached() -> None:
    assert get_compiled_patterns() is get_compiled_patterns()


def test_pattern_library_covers_required_categories() -> None:
    entity_types = {pattern.entity_type for pattern in get_pattern_definitions()}
    assert {"EMAIL", "PHONE", "SSN", "CREDIT_CARD", "IPV4", "DATE"} <= entity_types
