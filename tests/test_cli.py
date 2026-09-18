from __future__ import annotations

from pathlib import Path

from county_health_normalize.cli import main
from county_health_normalize.pipeline import normalize_csv


def test_normalize_sample_csv(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text(
        "fips,state_name,county_name,year,adult_obesity,uninsured,population,source\n"
        "06037,california,los angeles,2023,28.4,10.2,9829544,chr_sample\n"
        "17031,illinois,cook,2023,31.1,9.8,5275541,chr_sample\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    result = normalize_csv(raw, out, strict=True)
    assert out.exists()
    assert len(result) == 4


def test_cli_normalize(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text(
        "fips,state_name,county_name,year,adult_obesity,source\n"
        "48201,texas,harris,2023,33.5,cli\n",
        encoding="utf-8",
    )
    out = tmp_path / "normalized.csv"
    code = main(["normalize", str(raw), "-o", str(out), "--strict"])
    assert code == 0
    assert out.exists()
