"""Metric catalog used to map source fields onto stable metric ids."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    metric_id: str
    metric_name: str
    unit: str | None = None
    aliases: tuple[str, ...] = ()


DEFAULT_METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        metric_id="premature_death",
        metric_name="Premature Death",
        unit="years_of_potential_life_lost_rate",
        aliases=("years_of_potential_life_lost_rate", "ypll", "premature death"),
    ),
    MetricDefinition(
        metric_id="poor_or_fair_health",
        metric_name="Poor or Fair Health",
        unit="percent",
        aliases=("poor_or_fair_health", "% fair/poor", "fair_or_poor_health"),
    ),
    MetricDefinition(
        metric_id="adult_obesity",
        metric_name="Adult Obesity",
        unit="percent",
        aliases=("adult_obesity", "obesity", "% obese"),
    ),
    MetricDefinition(
        metric_id="uninsured",
        metric_name="Uninsured",
        unit="percent",
        aliases=("uninsured", "% uninsured", "uninsured_adults"),
    ),
    MetricDefinition(
        metric_id="primary_care_physicians",
        metric_name="Primary Care Physicians",
        unit="ratio",
        aliases=("primary_care_physicians", "pcp_ratio", "primary care physicians"),
    ),
)


def build_alias_index(
    metrics: tuple[MetricDefinition, ...] = DEFAULT_METRICS,
) -> dict[str, MetricDefinition]:
    index: dict[str, MetricDefinition] = {}
    for metric in metrics:
        keys = {metric.metric_id, metric.metric_name, *metric.aliases}
        for key in keys:
            index[_normalize_key(key)] = metric
    return index


def resolve_metric(
    raw_name: object,
    *,
    index: dict[str, MetricDefinition] | None = None,
) -> MetricDefinition | None:
    lookup = index or build_alias_index()
    return lookup.get(_normalize_key(raw_name))


def _normalize_key(value: object) -> str:
    return " ".join(str(value or "").strip().lower().replace("-", " ").replace("_", " ").split())
