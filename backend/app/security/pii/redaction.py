from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Mapping

from .models import PIIMatch, PIIRedactionResult, RedactionRecord, RedactionStrategy

DEFAULT_HASH_SALT = "phase1-pii-guardrails"
DEFAULT_STRATEGY = RedactionStrategy.MASK


def _normalize_overrides(
    strategy_overrides: Mapping[str, RedactionStrategy | str] | None,
) -> dict[str, RedactionStrategy]:
    if not strategy_overrides:
        return {}
    normalized: dict[str, RedactionStrategy] = {}
    for entity_type, strategy in strategy_overrides.items():
        normalized[entity_type.upper()] = strategy if isinstance(strategy, RedactionStrategy) else RedactionStrategy(strategy)
    return normalized


def _mask_characters(value: str, visible_indexes: set[int] | None = None) -> str:
    visible_indexes = visible_indexes or set()
    return "".join(
        character if index in visible_indexes or not character.isalnum() else "*"
        for index, character in enumerate(value)
    )


def _alnum_indexes(value: str) -> list[int]:
    return [index for index, character in enumerate(value) if character.isalnum()]


def _partial_generic(value: str, keep_start: int = 1, keep_end: int = 1) -> str:
    indexes = _alnum_indexes(value)
    if len(indexes) <= keep_start + keep_end:
        return _mask_characters(value)
    trailing = set(indexes[-keep_end:]) if keep_end else set()
    visible = set(indexes[:keep_start]) | trailing
    return _mask_characters(value, visible)


def _partial_phone_like(value: str, keep_last_digits: int = 4) -> str:
    visible: set[int] = set()
    remaining = keep_last_digits
    for index in range(len(value) - 1, -1, -1):
        if value[index].isdigit() and remaining > 0:
            visible.add(index)
            remaining -= 1
    return _mask_characters(value, visible)


def _partial_email(value: str) -> str:
    if "@" not in value:
        return _partial_generic(value)
    local_part, domain = value.split("@", 1)
    masked_local = _partial_generic(local_part, keep_start=1, keep_end=0)
    if "." in domain:
        host, dot, suffix = domain.rpartition(".")
        masked_host = _partial_generic(host, keep_start=1, keep_end=0)
        return f"{masked_local}@{masked_host}{dot}{suffix}"
    return f"{masked_local}@{_partial_generic(domain, keep_start=1, keep_end=0)}"


def _partial_ipv4(value: str) -> str:
    octets = value.split(".")
    if len(octets) != 4:
        return _partial_generic(value)
    return f"***.***.***.{octets[-1]}"


def _hash_value(entity_type: str, value: str, hash_salt: str) -> str:
    payload = f"{hash_salt}:{entity_type}:{value}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    return f"<{entity_type}_HASH:{digest}>"


class SyntheticValueFactory:
    def __init__(self) -> None:
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._cache: dict[tuple[str, str], str] = {}

    def replacement_for(self, match: PIIMatch) -> str:
        cache_key = (match.entity_type, match.text)
        if cache_key in self._cache:
            return self._cache[cache_key]
        self._counters[match.entity_type] += 1
        replacement = f"<{match.entity_type}_SYNTHETIC_{self._counters[match.entity_type]:04d}>"
        self._cache[cache_key] = replacement
        return replacement


def _resolve_strategy(
    match: PIIMatch,
    strategy_overrides: Mapping[str, RedactionStrategy],
) -> RedactionStrategy:
    if match.entity_type in strategy_overrides:
        return strategy_overrides[match.entity_type]
    if "DEFAULT" in strategy_overrides:
        return strategy_overrides["DEFAULT"]
    return DEFAULT_STRATEGY


def _replacement_for_match(
    match: PIIMatch,
    strategy: RedactionStrategy,
    synthetic_factory: SyntheticValueFactory,
    hash_salt: str,
) -> str:
    if strategy == RedactionStrategy.MASK:
        return _mask_characters(match.text)
    if strategy == RedactionStrategy.HASH:
        return _hash_value(match.entity_type, match.text, hash_salt=hash_salt)
    if strategy == RedactionStrategy.SYNTHETIC:
        return synthetic_factory.replacement_for(match)
    if match.entity_type == "EMAIL":
        return _partial_email(match.text)
    if match.entity_type in {"PHONE", "SSN", "CREDIT_CARD"}:
        return _partial_phone_like(match.text)
    if match.entity_type == "IPV4":
        return _partial_ipv4(match.text)
    return _partial_generic(match.text, keep_start=1, keep_end=1)


def redact_text(
    text: str,
    matches: list[PIIMatch],
    strategy_overrides: Mapping[str, RedactionStrategy | str] | None = None,
    hash_salt: str = DEFAULT_HASH_SALT,
) -> PIIRedactionResult:
    if not matches:
        return PIIRedactionResult(
            text=text,
            redacted_text=text,
            matches=[],
            redactions=[],
        )

    synthetic_factory = SyntheticValueFactory()
    normalized_overrides = _normalize_overrides(strategy_overrides)
    redacted_text = text
    redactions_by_span: dict[tuple[int, int], RedactionRecord] = {}

    for match in sorted(matches, key=lambda item: (item.start, item.end), reverse=True):
        strategy = _resolve_strategy(match, normalized_overrides)
        replacement = _replacement_for_match(match, strategy, synthetic_factory, hash_salt)
        redacted_text = f"{redacted_text[:match.start]}{replacement}{redacted_text[match.end:]}"
        redactions_by_span[(match.start, match.end)] = RedactionRecord(
            match=match,
            strategy=strategy,
            replacement=replacement,
        )

    ordered_redactions = [
        redactions_by_span[match.span]
        for match in sorted(matches, key=lambda item: (item.start, item.end))
    ]
    return PIIRedactionResult(
        text=text,
        redacted_text=redacted_text,
        matches=list(matches),
        redactions=ordered_redactions,
    )
