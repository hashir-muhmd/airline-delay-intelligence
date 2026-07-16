-- database/migrations/002_add_indexes.sql
-- Adds indexes to speed up common query patterns (origin/destination lookups,
-- time-range queries) as the flights and weather_snapshots tables grow.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_flights_origin_departure
    ON flights (origin, scheduled_departure);

CREATE INDEX IF NOT EXISTS idx_flights_destination_departure
    ON flights (destination, scheduled_departure);

CREATE INDEX IF NOT EXISTS idx_weather_airport_recorded
    ON weather_snapshots (airport_code, recorded_at);

COMMIT;