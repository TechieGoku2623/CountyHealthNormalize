"""Checks for age adjustment and small-cell suppression."""

from __future__ import annotations

import asyncio
import sys

from .engine import CountyHealthNormalizer
from .exceptions import EngineKernelException


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


async def _checks() -> list[str]:
    failures: list[str] = []
    engine = CountyHealthNormalizer()
    report = await engine.run(
        [
            _county("A", (2, 20, 40), (10_000, 40_000, 8_000)),
            _county("B", (1, 1, 1), (5_000, 5_000, 5_000)),
            _county("D", (1, 10, 80), (1_000, 2_000, 500)),
            _county("E", (4, 25, 10), (20_000, 50_000, 10_000)),
        ]
    )
    if report["suppressed"] != 1:
        failures.append(f"suppressed {report['suppressed']}")
    if report["flagged"] != ["D"]:
        failures.append(f"flagged {report['flagged']}")
    published = {row["county"]: row for row in report["published"]}
    if published["A"]["adjusted_per_100k"] != 115.4:
        failures.append(f"adjusted {published['A']}")
    try:
        await engine.run([_county("Z", (2, 1, 0), (1, 10, 10))])
    except EngineKernelException:
        pass
    else:
        failures.append("cases above population did not raise")
    return failures


def main() -> int:
    failures = asyncio.run(_checks())
    if failures:
        print("\n".join(failures))
        return 1
    print("county-health-normalize checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
