from __future__ import annotations

import pytest

from county_health_normalize.geo import normalize_fips, title_case_place


def test_normalize_fips_from_full_code() -> None:
    assert normalize_fips(fips="6037") == ("06", "037", "06037")


def test_normalize_fips_from_parts() -> None:
    assert normalize_fips(state_fips=6, county_fips=37) == ("06", "037", "06037")


def test_normalize_fips_rejects_incomplete() -> None:
    with pytest.raises(ValueError):
        normalize_fips(state_fips=6)


def test_title_case_place() -> None:
    assert title_case_place("los angeles") == "Los Angeles"
    assert title_case_place("washington dc") == "Washington DC"
