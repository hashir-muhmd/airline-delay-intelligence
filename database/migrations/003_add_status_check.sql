-- database/migrations/003_add_status_check.sql
-- Restricts flights.status to known valid values, catching bad/unexpected
-- data early rather than silently accepting anything.

BEGIN;

ALTER TABLE flights
    ADD CONSTRAINT status_valid_values
    CHECK (status IN ('scheduled', 'active', 'landed', 'cancelled', 'diverted', 'incident'));

COMMIT;