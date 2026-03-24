from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Callable

Validator = Callable[[str], bool]
DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d",
    "%b %d",
)
MONTH_NAMES = (
    "Jan(?:uary)?",
    "Feb(?:ruary)?",
    "Mar(?:ch)?",
    "Apr(?:il)?",
    "May",
    "Jun(?:e)?",
    "Jul(?:y)?",
    "Aug(?:ust)?",
    "Sep(?:tember)?",
    "Oct(?:ober)?",
    "Nov(?:ember)?",
    "Dec(?:ember)?",
)


@dataclass(frozen=True, slots=True)
class RegexPattern:
    name: str
    entity_type: str
    expression: str
    score: float
    flags: int = re.IGNORECASE
    validator: Validator | None = None


@dataclass(frozen=True, slots=True)
class CompiledRegexPattern:
    name: str
    entity_type: str
    expression: str
    score: float
    regex: re.Pattern[str]
    validator: Validator | None = None


def _digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def _luhn_checksum(digits: str) -> bool:
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        value = int(digit)
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _validate_credit_card(value: str) -> bool:
    digits = _digits_only(value)
    if len(digits) < 13 or len(digits) > 19:
        return False
    if len(set(digits)) == 1:
        return False
    return _luhn_checksum(digits)


def _validate_phone(value: str) -> bool:
    digits = _digits_only(value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return len(digits) == 10


def _validate_ssn(value: str) -> bool:
    digits = _digits_only(value)
    if len(digits) != 9:
        return False
    area = int(digits[0:3])
    group = int(digits[3:5])
    serial = int(digits[5:9])
    if area == 0 or group == 0 or serial == 0:
        return False
    if area == 666 or area >= 900:
        return False
    return True


def _validate_ipv4(value: str) -> bool:
    octets = value.split(".")
    if len(octets) != 4:
        return False
    return all(octet.isdigit() and 0 <= int(octet) <= 255 for octet in octets)


def _validate_date(value: str) -> bool:
    value = value.strip()
    for candidate in DATE_FORMATS:
        try:
            datetime.strptime(value, candidate)
            return True
        except ValueError:
            continue
    return False


@lru_cache(maxsize=1)
def get_pattern_definitions() -> tuple[RegexPattern, ...]:
    month_pattern = "|".join(MONTH_NAMES)
    return (
        RegexPattern(
            name="email",
            entity_type="EMAIL",
            expression=r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,63}\b",
            score=0.99,
        ),
        RegexPattern(
            name="phone",
            entity_type="PHONE",
            expression=r"(?<!\w)(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?!\w)",
            score=0.96,
            validator=_validate_phone,
        ),
        RegexPattern(
            name="ssn",
            entity_type="SSN",
            expression=r"(?<!\d)(?:\d{3}-\d{2}-\d{4}|\d{9})(?!\d)",
            score=0.99,
            validator=_validate_ssn,
        ),
        RegexPattern(
            name="credit_card",
            entity_type="CREDIT_CARD",
            expression=r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)",
            score=0.98,
            validator=_validate_credit_card,
        ),
        RegexPattern(
            name="ipv4",
            entity_type="IPV4",
            expression=r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)",
            score=0.97,
            validator=_validate_ipv4,
        ),
        RegexPattern(
            name="date",
            entity_type="DATE",
            expression=rf"\b(?:\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}/\d{{1,2}}/\d{{2,4}}|(?:{month_pattern})\s+\d{{1,2}}(?:,\s*\d{{4}})?)\b",
            score=0.90,
            validator=_validate_date,
        ),
    )


@lru_cache(maxsize=1)
def get_compiled_patterns() -> tuple[CompiledRegexPattern, ...]:
    compiled: list[CompiledRegexPattern] = []
    for pattern in get_pattern_definitions():
        compiled.append(
            CompiledRegexPattern(
                name=pattern.name,
                entity_type=pattern.entity_type,
                expression=pattern.expression,
                score=pattern.score,
                regex=re.compile(pattern.expression, pattern.flags),
                validator=pattern.validator,
            )
        )
    return tuple(compiled)
