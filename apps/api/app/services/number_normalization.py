"""Programmatic number normalization for source facts."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedNumber:
    value_raw: str
    value_normalized: float
    unit: str


NUMBER_PATTERN = re.compile(
    r"^\s*(?P<number>[+-]?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?))\s*"
    r"(?P<scale>万亿|亿|万)?\s*(?P<unit>.*)$"
)

SCALE_MULTIPLIERS = {
    "万亿": 1_000_000_000_000.0,
    "亿": 100_000_000.0,
    "万": 10_000.0,
}


def normalize_number(value_raw: str) -> NormalizedNumber | None:
    match = NUMBER_PATTERN.match(value_raw)
    if not match:
        return None

    number_text = match.group("number").replace(",", "")
    try:
        value = float(number_text)
    except ValueError:
        return None
    scale = match.group("scale")
    if scale:
        value *= SCALE_MULTIPLIERS[scale]

    unit = match.group("unit").strip()
    return NormalizedNumber(
        value_raw=value_raw.strip(),
        value_normalized=value,
        unit=unit,
    )
