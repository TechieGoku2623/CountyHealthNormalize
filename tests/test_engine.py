"""Unit tests for county rate normalization."""

from __future__ import annotations

import unittest

from county_health_normalize import CountyHealthNormalizer, EngineKernelException


def county(name: str, counts: tuple[int, int, int], pops: tuple[int, int, int]) -> dict:
    return {
        "county": name,
        "bands": [
            {"age": age, "pop": pop, "cases": cases}
            for age, pop, cases in zip(("0-17", "18-64", "65+"), pops, counts)
        ],
    }


class CountyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.engine = CountyHealthNormalizer()

    async def test_small_cell_is_suppressed(self) -> None:
        report = await self.engine.run([county("B", (1, 1, 1), (5_000, 5_000, 5_000))])
        self.assertEqual(report["suppressed"], 1)
        self.assertEqual(report["published"], [])
        self.assertIsNone(report["median_adjusted"])

    async def test_age_adjusted_rate(self) -> None:
        report = await self.engine.run(
            [county("A", (2, 20, 40), (10_000, 40_000, 8_000))]
        )
        row = report["published"][0]
        self.assertEqual(row["adjusted_per_100k"], 115.4)
        self.assertEqual(row["crude_per_100k"], 106.897)

    async def test_outlier_is_flagged(self) -> None:
        report = await self.engine.run(
            [
                county("A", (2, 20, 40), (10_000, 40_000, 8_000)),
                county("D", (1, 10, 80), (1_000, 2_000, 500)),
                county("E", (4, 25, 10), (20_000, 50_000, 10_000)),
            ]
        )
        self.assertEqual(report["flagged"], ["D"])

    async def test_cases_above_population_raise(self) -> None:
        with self.assertRaises(EngineKernelException):
            await self.engine.run([county("Z", (2, 1, 0), (1, 10, 10))])


if __name__ == "__main__":
    unittest.main()
