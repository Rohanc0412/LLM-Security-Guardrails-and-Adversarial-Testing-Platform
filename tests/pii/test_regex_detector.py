from __future__ import annotations

from backend.app.security.pii.regex_detector import RegexDetector


def test_regex_detector_detects_required_pii_types() -> None:
    text = """
    Contact jane.doe@example.com
    Phone +1 (212) 555-0100
    SSN 123-45-6789
    Card 4111 1111 1111 1111
    IP 192.168.10.4
    Date 2025-05-11
    """
    matches = RegexDetector().detect(text)
    entity_types = {match.entity_type for match in matches}

    assert {"EMAIL", "PHONE", "SSN", "CREDIT_CARD", "IPV4", "DATE"} <= entity_types
    assert any(match.source_metadata["regex"]["pattern_name"] == "email" for match in matches if match.entity_type == "EMAIL")


def test_regex_detector_rejects_invalid_values() -> None:
    text = """
    Not a valid SSN 000-00-0000
    Not a valid card 4111 1111 1111 1112
    Not a valid IP 999.999.999.999
    """
    matches = RegexDetector().detect(text)

    assert all(match.entity_type != "SSN" for match in matches)
    assert all(match.entity_type != "CREDIT_CARD" for match in matches)
    assert all(match.entity_type != "IPV4" for match in matches)


def test_regex_detector_returns_empty_for_empty_input() -> None:
    assert RegexDetector().detect("") == []
