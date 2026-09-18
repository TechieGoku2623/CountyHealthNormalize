"""Canonical schema for normalized county health records."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator


class NormalizedCountyHealthRow(BaseModel):
    """Stable analytics-ready row for a single county and reporting period."""

    state_fips: str = Field(..., min_length=2, max_length=2, pattern=r"^\d{2}$")
    county_fips: str = Field(..., min_length=3, max_length=3, pattern=r"^\d{3}$")
    fips: str = Field(..., min_length=5, max_length=5, pattern=r"^\d{5}$")
    state_name: str = Field(..., min_length=2)
    county_name: str = Field(..., min_length=1)
    year: int = Field(..., ge=1900, le=2100)
    metric_id: str = Field(..., min_length=1)
    metric_name: str = Field(..., min_length=1)
    value: float | None = None
    unit: str | None = None
    population: int | None = Field(default=None, ge=0)
    source: str = Field(..., min_length=1)
    as_of: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("state_name", "county_name", "metric_id", "metric_name", "source")
    @classmethod
    def strip_and_require(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be blank")
        return cleaned

    @field_validator("fips")
    @classmethod
    def fips_matches_parts(cls, value: str, info) -> str:
        state = info.data.get("state_fips")
        county = info.data.get("county_fips")
        if state and county and value != f"{state}{county}":
            raise ValueError("fips must equal state_fips + county_fips")
        return value


# Column order used for CSV / Parquet exports.
CANONICAL_COLUMNS: tuple[str, ...] = (
    "state_fips",
    "county_fips",
    "fips",
    "state_name",
    "county_name",
    "year",
    "metric_id",
    "metric_name",
    "value",
    "unit",
    "population",
    "source",
    "as_of",
    "metadata",
)
