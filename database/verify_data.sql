-- database/verify_data.sql
-- Quick health-check queries to confirm the ingestion pipeline is working
-- and see what data has accumulated so far.
-- Run individual queries with: psql -U postgres -d airline_delay_intelligence -c "<query>"

-- Row counts across all core tables
SELECT 'flights' AS table_name, COUNT(*) FROM flights
UNION ALL
SELECT 'weather_snapshots', COUNT(*) FROM weather_snapshots
UNION ALL
SELECT 'airports', COUNT(*) FROM airports
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'cascade_links', COUNT(*) FROM cascade_links;

-- Sample of recent flights
SELECT flight_number, origin, destination, status, scheduled_departure, delay_minutes
FROM flights
ORDER BY fetched_at DESC
LIMIT 20;

-- Destinations discovered so far via auto-created airport stubs
SELECT code, name
FROM airports
WHERE name IS NULL
ORDER BY code;

-- Most recent weather snapshot per airport
SELECT airport_code, recorded_at, temperature_c, condition_code
FROM weather_snapshots
ORDER BY recorded_at DESC
LIMIT 10;

-- Flights by status, to see the mix of scheduled/active/landed/delayed
SELECT status, COUNT(*)
FROM flights
GROUP BY status
ORDER BY COUNT(*) DESC;