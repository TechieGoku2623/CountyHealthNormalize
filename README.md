# CountyHealthNormalize

Normalize county-level health indicator datasets into a **stable, analytics-ready schema**.

This repository was previously an empty placeholder. It now ships a small, extensible Python foundation so future data sources, metrics, and outputs can plug in without rewriting the core pipeline.

## Why this shape

County health feeds (County Health Rankings, CDC, census joins, custom extracts) disagree on:

- FIPS formatting (`6037` vs `06037` vs split state/county codes)
- Metric naming and units
- Wide vs long layouts
- Missing-value conventions

CountyHealthNormalize converts those inputs into one long-form table with validated types.

## Canonical schema

| Column | Description |
| --- | --- |
| `state_fips` / `county_fips` / `fips` | Zero-padded geography keys |
| `state_name` / `county_name` | Title-cased place names |
| `year` | Reporting year |
| `metric_id` / `metric_name` | Stable id + display name |
| `value` / `unit` | Measure and unit |
| `population` | Optional denominator context |
| `source` | Provenance label |
| `as_of` | Optional snapshot date |
| `metadata` | JSON bag for raw field names / extras |

## Quick start

```bash
python -m pip install -e ".[dev]"
chn normalize data/raw/sample_county_health.csv -o data/processed/sample.normalized.csv
pytest
```

Environment knobs (see `.env.example`):

- `CHN_DEFAULT_SOURCE`
- `CHN_OUTPUT_DIR`
- `CHN_STRICT`
- `CHN_LOG_LEVEL`

## Layout

```
src/county_health_normalize/
  adapters.py   # source-specific mappers (start with generic_csv)
  geo.py        # FIPS + place-name helpers
  metrics.py    # metric catalog + alias resolution
  pipeline.py   # orchestration + validation
  schema.py     # Pydantic contract
  cli.py        # `chn` entrypoint
data/raw/       # fixtures / inbound extracts
tests/          # unit + CLI coverage
.github/workflows/ci.yml
```

## Extending for production

1. **Add a source adapter** in `adapters.py` (or a new module) and register it in `ADAPTERS`.
2. **Extend `DEFAULT_METRICS`** with official ids, units, and aliases.
3. **Keep the Pydantic schema stable** — version additive fields carefully so downstream warehouses do not break.
4. **Emit Parquet / publish to a warehouse** from `normalize_frame` outputs once volume grows.
5. **Wire ingestion** (S3/GCS, scheduled CHR/CDC pulls) outside the library; keep this package focused on transform + validate.

## Future-ready checklist (next increments)

- [ ] Official County Health Rankings / CDC Wonder adapters
- [ ] Parquet + DuckDB/BigQuery export helpers
- [ ] Data contracts / schema versioning (`schema_version` column)
- [ ] Deterministic hashing for row-level lineage
- [ ] Pre-commit + typed mypy gate in CI
- [ ] Container image for reproducible batch jobs

## License

MIT
