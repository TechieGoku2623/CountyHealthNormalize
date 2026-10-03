"""Normalize one ordinary county and one small-cell county."""

from __future__ import annotations

import asyncio
import logging

from .engine import CountyHealthNormalizer


def _county(
    name: str, counts: tuple[int, int, int], pops: tuple[int, int, int]
) -> dict:
    return {
        "county": name,
        "bands": [
            {"age": age, "pop": pop, "cases": cases}
            for age, pop, cases in zip(("0-17", "18-64", "65+"), pops, counts)
        ],
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    records = [
        _county("A", (2, 20, 40), (10_000, 40_000, 8_000)),
        _county("B", (1, 1, 1), (5_000, 5_000, 5_000)),
    ]
    report = asyncio.run(CountyHealthNormalizer().run(records))
    logging.getLogger(__name__).info("%s", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
