# Database

PostgreSQL schema and migrations. Deployed on Railway, running live in
production alongside the ingestion service.

## Tables

- `airports` — airport metadata (name, city, country, coordinates, hub flag).
  Seeded with DOH; enriched via `scripts/enrich_airports.py`.
- `flights` — core flight + delay data. Unique on
  `(flight_number, scheduled_departure)` to avoid duplicate rows on repeated
  polling.
- `weather_snapshots` — airport weather tied to timestamps.
- `predictions` — schema defined for model outputs over time; **not yet
  populated** — the ML layer that would write to this table hasn't been
  built yet.
- `cascade_links` — schema defined for aircraft/crew rotation links for
  cascade modeling; **not yet populated**, same reason as `predictions`.

All timestamp columns are `TIMESTAMPTZ`. See `schema.sql` for full column
definitions and constraints.

## Migrations

Applied in order against the live database:

1. `001_add_timestamptz.sql` — converts flight/weather/prediction/cascade
   timestamp columns from plain `TIMESTAMP` to `TIMESTAMPTZ`. The original
   schema used `TIMESTAMP` while the Python client sent timezone-aware UTC
   values, so Postgres was silently dropping the offset. Fixed by reattaching
   the correct UTC zone to existing rows without shifting the underlying
   instant.
2. `002_add_indexes.sql` — adds indexes on `(origin, scheduled_departure)`,
   `(destination, scheduled_departure)`, and `(airport_code, recorded_at)` to
   speed up common query patterns as the tables grow.
3. `003_add_status_check.sql` — restricts `flights.status` to a known set of
   valid values (`scheduled`, `active`, `landed`, `cancelled`, `diverted`,
   `incident`), catching bad/unexpected data early.

A separate, larger data-quality fix — correcting a timezone mislabeling bug
in the ingestion client (see `ingestion/README.md`) — required backfilling
~5,100 historical rows. That backfill was run as a direct, transaction-wrapped
`psql` statement (`BEGIN` → verify with `SELECT` against known-good reference
data → `COMMIT`) rather than as a committed migration file, per the working
agreement that production data changes always go through that
verify-then-commit pattern.

## Running migrations

```bash
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/migrations/001_add_timestamptz.sql
psql "$DATABASE_URL" -f database/migrations/002_add_indexes.sql
psql "$DATABASE_URL" -f database/migrations/003_add_status_check.sql
```

`verify_data.sql` contains ad-hoc queries used to sanity-check data quality
(e.g. timezone correctness, delay-value plausibility) after ingestion or
migrations run.

## Status

Schema and all three migrations are live in production. `predictions` and
`cascade_links` exist as defined tables ready to receive data once the ML
layer (not yet started — blocked on data volume) is built.