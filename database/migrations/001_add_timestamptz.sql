-- database/migrations/001_add_timestamptz.sql
--
-- Problem: schema.sql declared datetime columns as TIMESTAMP (no timezone),
-- but the Python client always sends timezone-aware UTC datetimes. Postgres
-- silently drops the offset on a plain TIMESTAMP column, so values were being
-- stored assuming they were already "local" with no zone attached.
--
-- Fix: convert each column to TIMESTAMPTZ. Since every existing row was
-- written as UTC, we tell Postgres to interpret the naive stored values as
-- UTC (`AT TIME ZONE 'UTC'`) rather than as the session/server timezone -
-- this reattaches the correct offset without shifting the underlying instant.
--
-- Run against your configured DATABASE_URL, e.g.:
--   psql "$DATABASE_URL" -f database/migrations/001_add_timestamptz.sql

BEGIN;

ALTER TABLE flights
    ALTER COLUMN scheduled_departure TYPE TIMESTAMPTZ USING scheduled_departure AT TIME ZONE 'UTC',
    ALTER COLUMN actual_departure    TYPE TIMESTAMPTZ USING actual_departure    AT TIME ZONE 'UTC',
    ALTER COLUMN scheduled_arrival   TYPE TIMESTAMPTZ USING scheduled_arrival   AT TIME ZONE 'UTC',
    ALTER COLUMN actual_arrival      TYPE TIMESTAMPTZ USING actual_arrival      AT TIME ZONE 'UTC',
    ALTER COLUMN fetched_at          TYPE TIMESTAMPTZ USING fetched_at         AT TIME ZONE 'UTC',
    ALTER COLUMN fetched_at          SET DEFAULT NOW();

ALTER TABLE weather_snapshots
    ALTER COLUMN recorded_at TYPE TIMESTAMPTZ USING recorded_at AT TIME ZONE 'UTC',
    ALTER COLUMN fetched_at  TYPE TIMESTAMPTZ USING fetched_at  AT TIME ZONE 'UTC',
    ALTER COLUMN fetched_at  SET DEFAULT NOW();

ALTER TABLE predictions
    ALTER COLUMN predicted_at TYPE TIMESTAMPTZ USING predicted_at AT TIME ZONE 'UTC',
    ALTER COLUMN predicted_at SET DEFAULT NOW();

ALTER TABLE cascade_links
    ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC',
    ALTER COLUMN created_at SET DEFAULT NOW();

COMMIT;
