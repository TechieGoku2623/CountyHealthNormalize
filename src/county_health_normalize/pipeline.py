"""Normalization pipeline orchestration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from county_health_normalize.adapters import SourceAdapter, get_adapter
from county_health_normalize.errors import ValidationBatchError
from county_health_normalize.schema import CANONICAL_COLUMNS, NormalizedCountyHealthRow

logger = logging.getLogger(__name__)


def normalize_frame(
    frame: pd.DataFrame,
    *,
    source: str = "generic_csv",
    adapter: SourceAdapter | None = None,
    strict: bool = True,
    default_source_name: str | None = None,
) -> pd.DataFrame:
    """
    Normalize a raw DataFrame into the canonical county-health schema.

    Returns a DataFrame with CANONICAL_COLUMNS. Invalid rows are dropped when
    strict=False; otherwise a ValidationBatchError is raised.
    """
    active = adapter or get_adapter(source)
    intermediate = active.to_intermediate(frame)
    if default_source_name:
        intermediate = intermediate.copy()
        intermediate["source"] = intermediate["source"].fillna(default_source_name)
        intermediate.loc[intermediate["source"].astype(str).str.strip() == "", "source"] = (
            default_source_name
        )

    validated_rows: list[dict[str, Any]] = []
    failures: list[str] = []

    for index, raw in enumerate(intermediate.to_dict(orient="records")):
        payload = dict(raw)
        if isinstance(payload.get("metadata"), str):
            try:
                payload["metadata"] = json.loads(payload["metadata"])
            except json.JSONDecodeError:
                payload["metadata"] = {"raw_metadata": payload["metadata"]}
        if payload.get("as_of") in ("", None) or (
            isinstance(payload.get("as_of"), float) and pd.isna(payload.get("as_of"))
        ):
            payload["as_of"] = None
        try:
            model = NormalizedCountyHealthRow.model_validate(payload)
            record = model.model_dump()
            record["as_of"] = record["as_of"].isoformat() if record["as_of"] else None
            record["metadata"] = json.dumps(record["metadata"], sort_keys=True)
            validated_rows.append(record)
        except Exception as exc:  # noqa: BLE001 - collect validation failures
            message = f"row {index}: {exc}"
            failures.append(message)
            logger.debug("validation failure: %s", message)

    if failures and strict:
        preview = "; ".join(failures[:5])
        raise ValidationBatchError(
            f"{len(failures)} row(s) failed validation: {preview}",
            failures=failures,
        )
    if failures:
        logger.warning("dropped %s invalid row(s)", len(failures))

    result = pd.DataFrame(validated_rows, columns=list(CANONICAL_COLUMNS))
    return result.sort_values(["year", "fips", "metric_id"]).reset_index(drop=True)


def normalize_csv(
    input_path: Path | str,
    output_path: Path | str | None = None,
    *,
    source: str = "generic_csv",
    strict: bool = True,
) -> pd.DataFrame:
    path = Path(input_path)
    frame = pd.read_csv(path)
    normalized = normalize_frame(frame, source=source, strict=strict, default_source_name=path.stem)
    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        normalized.to_csv(out, index=False)
        logger.info("wrote %s rows to %s", len(normalized), out)
    return normalized
