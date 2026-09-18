"""Source adapters that map raw frames into a common intermediate shape."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

import pandas as pd

from county_health_normalize.errors import AdapterError
from county_health_normalize.geo import normalize_fips, title_case_place
from county_health_normalize.metrics import MetricDefinition, build_alias_index, resolve_metric


class SourceAdapter(ABC):
    """Convert a vendor-specific frame into long-form intermediate records."""

    name: str

    @abstractmethod
    def to_intermediate(self, frame: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class GenericCsvAdapter(SourceAdapter):
    """
    Accepts either long-form or wide-form CSV data.

    Expected geography columns (any of):
      - fips
      - state_fips + county_fips
      - State FIPS + County FIPS

    Long-form metric columns:
      - metric / metric_name / measure
      - value / raw_value

    Wide-form: remaining numeric columns become metrics.
    """

    name = "generic_csv"

    def __init__(self, column_map: Mapping[str, str] | None = None) -> None:
        self.column_map = {k.lower(): v for k, v in (column_map or {}).items()}
        self._metric_index = build_alias_index()

    def to_intermediate(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return _empty_intermediate()

        working = frame.copy()
        working.columns = [_canonicalize_column(c, self.column_map) for c in working.columns]

        try:
            geo = working.apply(_extract_geo, axis=1, result_type="expand")
        except Exception as exc:  # noqa: BLE001 - surface as adapter error
            raise AdapterError(f"failed to parse geography columns: {exc}") from exc
        overlapping = [c for c in geo.columns if c in working.columns]
        working = working.drop(columns=overlapping, errors="ignore")
        working = pd.concat([working, geo], axis=1)

        if "year" not in working.columns:
            raise AdapterError("input must include a year column")

        long_metric_col = next(
            (c for c in ("metric", "metric_name", "measure") if c in working.columns),
            None,
        )
        if long_metric_col and "value" in working.columns:
            records = self._from_long(working, long_metric_col)
        else:
            records = self._from_wide(working)

        if not records:
            raise AdapterError("no metric values found in input")
        return pd.DataFrame.from_records(records)

    def _from_long(self, working: pd.DataFrame, metric_col: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for row in working.to_dict(orient="records"):
            metric = resolve_metric(row[metric_col], index=self._metric_index)
            records.append(
                _record_from_parts(
                    row,
                    metric,
                    raw_metric=row[metric_col],
                    value=row.get("value"),
                )
            )
        return records

    def _from_wide(self, working: pd.DataFrame) -> list[dict[str, Any]]:
        reserved = {
            "state_fips",
            "county_fips",
            "fips",
            "state_name",
            "county_name",
            "year",
            "population",
            "source",
            "as_of",
            "unit",
            "value",
            "metric",
            "metric_name",
            "measure",
        }
        metric_cols = [c for c in working.columns if c not in reserved]
        records: list[dict[str, Any]] = []
        for row in working.to_dict(orient="records"):
            for col in metric_cols:
                metric = resolve_metric(col, index=self._metric_index)
                records.append(_record_from_parts(row, metric, raw_metric=col, value=row.get(col)))
        return records


ADAPTERS: dict[str, type[SourceAdapter]] = {
    GenericCsvAdapter.name: GenericCsvAdapter,
}


def get_adapter(name: str, **kwargs: Any) -> SourceAdapter:
    try:
        adapter_cls = ADAPTERS[name]
    except KeyError as exc:
        known = ", ".join(sorted(ADAPTERS))
        raise AdapterError(f"unknown adapter {name!r}; known: {known}") from exc
    return adapter_cls(**kwargs)


def _canonicalize_column(name: object, column_map: Mapping[str, str]) -> str:
    raw = str(name).strip()
    key = raw.lower()
    if key in column_map:
        return column_map[key]
    replacements = {
        "state fips": "state_fips",
        "county fips": "county_fips",
        "state code": "state_fips",
        "county code": "county_fips",
        "county": "county_name",
        "state": "state_name",
        "raw value": "value",
        "measure": "metric_name",
        "metric": "metric_name",
    }
    return replacements.get(key, key.replace(" ", "_"))


def _extract_geo(row: pd.Series) -> dict[str, str]:
    state, county, fips = normalize_fips(
        fips=row.get("fips"),
        state_fips=row.get("state_fips"),
        county_fips=row.get("county_fips"),
    )
    return {
        "state_fips": state,
        "county_fips": county,
        "fips": fips,
        "state_name": title_case_place(row.get("state_name") or row.get("state") or ""),
        "county_name": title_case_place(row.get("county_name") or row.get("county") or ""),
    }


def _record_from_parts(
    row: dict[str, Any],
    metric: MetricDefinition | None,
    *,
    raw_metric: object,
    value: object,
) -> dict[str, Any]:
    metric_id = metric.metric_id if metric else _slug(raw_metric)
    metric_name = metric.metric_name if metric else str(raw_metric).strip()
    unit = row.get("unit") or (metric.unit if metric else None)
    return {
        "state_fips": row["state_fips"],
        "county_fips": row["county_fips"],
        "fips": row["fips"],
        "state_name": row.get("state_name") or "",
        "county_name": row.get("county_name") or "",
        "year": int(row["year"]),
        "metric_id": metric_id,
        "metric_name": metric_name,
        "value": _to_float(value),
        "unit": unit,
        "population": _to_int(row.get("population")),
        "source": str(row.get("source") or "generic_csv"),
        "as_of": row.get("as_of"),
        "metadata": {"raw_metric": str(raw_metric)},
    }


def _empty_intermediate() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
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
        ]
    )


def _to_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(",", "")
    if text == "" or text.lower() in {"na", "n/a", "null", "none", "."}:
        return None
    return float(text)


def _to_int(value: object) -> int | None:
    number = _to_float(value)
    return None if number is None else int(number)


def _slug(value: object) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value).strip())
    return "_".join(part for part in text.split("_") if part) or "unknown_metric"
