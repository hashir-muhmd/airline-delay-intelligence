# Database

PostgreSQL schema and migrations. Runs locally — see the root `README.md`'s "Deployment history" section for why (previously ran live on Railway alongside the ingestion service, through August 2026).

## Tables

- `airports` — airport metadata (name, city, country, coordinates, hub flag).
  Seeded with DOH; enriched via `scripts/enrich_airports.py`.
- `flights` — core flight + delay data. Unique on
  `(flight_number, scheduled_departure)` to avoid duplicate rows on repeated
  polling. Includes `aircraft_icao24` (see migration 004 below) as the
  working aircraft identifier, since `aircraft_registration` is confirmed
  permanently null on AviationStack's free tier.
- `weather_snapshots` — airport weather tied to timestamps.
- `predictions` — schema defined for model outputs over time; **not yet
  populated** — the ML layer that would write to this table hasn't been
  built yet.
- `cascade_links` — schema defined for aircraft rotation links for cascade
  modeling; **not yet populated**. Also includes `aircraft_icao24`
  (migration 005).

All timestamp columns are `TIMESTAMPTZ`. See `schema.sql` for full column
definitions and constraints.

## Migrations

Applied in order:

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
4. `004_add_aircraft_icao24.sql` — adds `aircraft_icao24` to `flights`.
   `aircraft_registration` was found to be permanently null on
   AviationStack's free tier (confirmed via direct raw API testing, not a
   parsing bug); `aircraft_icao24` (the Mode-S transponder hex code) is
   populated and serves the same purpose as a per-aircraft identifier for
   cascade linking.
5. `005_add_cascade_icao24.sql` — adds the same `aircraft_icao24` column to
   `cascade_links`, for consistency with `flights`.

A separate, larger data-quality fix — correcting a timezone mislabeling bug
in the ingestion client (see `ingestion/README.md`) — required backfilling
~5,100 historical rows on the (now-retired) Railway-hosted database. That
backfill was run as a direct, transaction-wrapped `psql` statement
(`BEGIN` → verify with `SELECT` against known-good reference data →
`COMMIT`) rather than as a committed migration file, per the working
agreement that production data changes always go through that
verify-then-commit pattern.

## Local dataset note

Following Railway's trial expiry (see root `README.md`), development moved
to a local Postgres instance. That instance was restored from an earlier
local snapshot (~400 flight rows, pre-dating migrations 004/005) rather than
the larger dataset that had accumulated on Railway (~6,800+ rows). All 5
migrations have since been re-applied locally, bringing the schema fully
up to date; local ingestion is accumulating fresh data again from that
smaller starting point.

## Running migrations

```bash
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/migrations/001_add_timestamptz.sql
psql "$DATABASE_URL" -f database/migrations/002_add_indexes.sql
psql "$DATABASE_URL" -f database/migrations/003_add_status_check.sql
psql "$DATABASE_URL" -f database/migrations/004_add_aircraft_icao24.sql
psql "$DATABASE_URL" -f database/migrations/005_add_cascade_icao24.sql
```

`verify_data.sql` contains ad-hoc queries used to sanity-check data quality
(e.g. timezone correctness, delay-value plausibility) after ingestion or
migrations run.

## Status

Schema and all five migrations are applied and current on the local
database. `predictions` and `cascade_links` exist as defined tables ready
to receive data once the ML layer that would populate them (cascade model,
prediction serving) is built — both currently blocked on data volume, see
`ml/README.md`.