"""Age-adjust county rates and suppress small cells.

Rates are per 100,000. The reference age mix is a fixed standard
(0-17, 18-64, 65+), not the batch itself. A county with fewer than
five cases is suppressed: its rate is not published. A published rate
at least twice the median of the published set is flagged.
"""

from __future__ import annotations

import statistics
from typing import Iterable, Mapping

from .exceptions import EngineKernelException

BANDS = ("0-17", "18-64", "65+")
REFERENCE = {"0-17": 0.22, "18-64": 0.62, "65+": 0.16}
SUPPRESS_BELOW = 5


class CountyHealthNormalizer:
    """Publish age-adjusted rates for counties that clear the small-cell rule."""

    async def run(self, records: Iterable[Mapping[str, object]]) -> dict[str, object]:
        rows = list(records)
        if not rows:
            raise EngineKernelException("empty batch")
        prepared: list[dict[str, object]] = []
        suppressed = 0
        for row in rows:
            county = str(row.get("county", "")).strip()
            if not county:
                raise EngineKernelException("county id is empty")
            bands = self._bands(row.get("bands"))
            cases = sum(item[2] for item in bands)
            population = sum(item[1] for item in bands)
            if cases < SUPPRESS_BELOW:
                suppressed += 1
                continue
            crude = cases / population * 100_000
            adjusted = (
                sum((item[2] / item[1]) * REFERENCE[item[0]] for item in bands)
                * 100_000
            )
            prepared.append(
                {
                    "county": county,
                    "crude_per_100k": round(crude, 3),
                    "adjusted_per_100k": round(adjusted, 3),
                }
            )
        median = None
        flagged: list[str] = []
        if prepared:
            median = statistics.median(
                float(item["adjusted_per_100k"]) for item in prepared
            )
            cutoff = 2 * median
            flagged = [
                str(item["county"])
                for item in prepared
                if float(item["adjusted_per_100k"]) >= cutoff
            ]
        return {
            "counties": len(rows),
            "suppressed": suppressed,
            "published": prepared,
            "flagged": flagged,
            "median_adjusted": None if median is None else round(median, 3),
        }

    def _bands(self, raw: object) -> list[tuple[str, int, int]]:
        if not isinstance(raw, list) or len(raw) != 3:
            raise EngineKernelException("bands must be the three standard age groups")
        found: dict[str, tuple[int, int]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise EngineKernelException("band must be a mapping")
            age = str(item.get("age", ""))
            if age not in REFERENCE or age in found:
                raise EngineKernelException("band age is missing or repeated")
            pop = item.get("pop")
            cases = item.get("cases")
            if isinstance(pop, bool) or isinstance(cases, bool):
                raise EngineKernelException("population and cases must be integers")
            if not isinstance(pop, int) or not isinstance(cases, int):
                raise EngineKernelException("population and cases must be integers")
            if pop < 0 or cases < 0 or cases > pop:
                raise EngineKernelException(
                    "cases must sit inside a non-negative population"
                )
            if pop == 0:
                raise EngineKernelException("age band population is zero")
            found[age] = (pop, cases)
        return [(age, found[age][0], found[age][1]) for age in BANDS]
