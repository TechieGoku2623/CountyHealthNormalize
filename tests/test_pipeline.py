from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

from county_health_normalize.metrics import resolve_metric
from county_health_normalize.pipeline import normalize_frame
from county_health_normalize.schema import NormalizedCountyHealthRow


def test_resolve_metric_aliases() -> None:
    metric = resolve_metric("% obese")
    assert metric is not None
    assert metric.metric_id == "adult_obesity"


def test_normalize_wide_frame() -> None:
    frame = pd.DataFrame(
        [
            {
                "fips": "06037",
                "state_name": "california",
                "county_name": "los angeles",
                "year": 2023,
                "adult_obesity": "28.4",
                "uninsured": "10.2",
                "population": "100",
                "source": "unit_test",
            }
        ]
    )
    result = normalize_frame(frame, strict=True)
    assert len(result) == 2
    assert set(result["metric_id"]) == {"adult_obesity", "uninsured"}
    assert result.iloc[0]["fips"] == "06037"
    assert result.iloc[0]["state_name"] == "California"


def test_normalize_long_frame() -> None:
    frame = pd.DataFrame(
        [
            {
                "state_fips": "17",
                "county_fips": "031",
                "state_name": "Illinois",
                "county_name": "Cook",
                "year": 2022,
                "metric_name": "Poor or Fair Health",
                "value": 15.5,
                "source": "unit_test",
            }
        ]
    )
    result = normalize_frame(frame, strict=True)
    assert len(result) == 1
    assert result.iloc[0]["metric_id"] == "poor_or_fair_health"


def test_schema_rejects_mismatched_fips() -> None:
    with pytest.raises(ValidationError):
        NormalizedCountyHealthRow(
            state_fips="06",
            county_fips="037",
            fips="17031",
            state_name="California",
            county_name="Los Angeles",
            year=2023,
            metric_id="adult_obesity",
            metric_name="Adult Obesity",
            source="test",
        )
