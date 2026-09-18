"""FIPS and geography helpers."""

from __future__ import annotations

import re

_NON_DIGIT = re.compile(r"\D+")


def digits_only(value: object) -> str:
    return _NON_DIGIT.sub("", str(value or ""))


def normalize_state_fips(value: object) -> str:
    digits = digits_only(value).zfill(2)
    if len(digits) > 2:
        digits = digits[-2:]
    if len(digits) != 2:
        raise ValueError(f"invalid state FIPS: {value!r}")
    return digits


def normalize_county_fips(value: object) -> str:
    digits = digits_only(value)
    if len(digits) >= 5:
        # Accept full FIPS and take county portion.
        digits = digits[-3:]
    digits = digits.zfill(3)
    if len(digits) != 3:
        raise ValueError(f"invalid county FIPS: {value!r}")
    return digits


def normalize_fips(
    *,
    fips: object | None = None,
    state_fips: object | None = None,
    county_fips: object | None = None,
) -> tuple[str, str, str]:
    """Return (state_fips, county_fips, fips) from partial inputs."""
    if fips is not None and str(fips).strip():
        digits = digits_only(fips).zfill(5)
        if len(digits) != 5:
            raise ValueError(f"invalid FIPS: {fips!r}")
        return digits[:2], digits[2:], digits

    if state_fips is None or county_fips is None:
        raise ValueError("provide fips or both state_fips and county_fips")

    state = normalize_state_fips(state_fips)
    county = normalize_county_fips(county_fips)
    return state, county, f"{state}{county}"


def title_case_place(name: object) -> str:
    text = " ".join(str(name or "").split())
    if not text:
        return text
    # Preserve common acronyms.
    parts = []
    for token in text.replace("-", " - ").split():
        if token.upper() in {"DC", "US", "USA"}:
            parts.append(token.upper())
        elif token == "-":
            parts.append("-")
        else:
            parts.append(token.capitalize())
    return " ".join(parts).replace(" - ", "-")
