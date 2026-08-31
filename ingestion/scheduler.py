# ingestion/scheduler.py
"""
Runs the ingestion jobs on a schedule:
- AviationStack: once a day (respects 100 req/month free tier; 60 calls/month)
- OpenWeatherMap: hourly (well within 1,000 req/day free tier)

Run with: python scheduler.py
Leave this running in a terminal (or set up as a background service later)
so historical data accumulates continuously.
"""

import time
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

from db import get_connection, insert_flight, insert_weather_snapshot
from aviationstack_client import fetch_all_tracked_flights
from weather_client import fetch_all_tracked_weather

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# If the most recent flight ingestion happened within this window, skip the
# startup poll. Prevents burning API quota on every process restart
# (whether from a local terminal restart or, previously, a Railway
# redeploy) -- without this check, every restart would trigger an
# immediate poll on top of the normal 24-hour interval, silently
# multiplying AviationStack calls.
STARTUP_POLL_SKIP_WINDOW_HOURS = 20


def _get_last_flight_fetch_time():
    """
    Returns the most recent fetched_at timestamp from the flights table,
    or None if the table is empty or the query fails for any reason.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(fetched_at) FROM flights;")
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        logger.exception(
            "Could not check last flight fetch time; proceeding with startup poll to be safe."
        )
        return None
    finally:
        conn.close()


def _should_skip_startup_poll():
    last_fetch = _get_last_flight_fetch_time()
    if last_fetch is None:
        return False  # no data yet, or check failed -> don't skip, be safe

    if last_fetch.tzinfo is None:
        last_fetch = last_fetch.replace(tzinfo=timezone.utc)

    age = datetime.now(timezone.utc) - last_fetch
    if age < timedelta(hours=STARTUP_POLL_SKIP_WINDOW_HOURS):
        logger.info(
            "Last flight ingestion was %s ago (< %sh threshold); skipping startup poll.",
            age, STARTUP_POLL_SKIP_WINDOW_HOURS,
        )
        return True
    return False


def run_flight_ingestion():
    logger.info("Running AviationStack ingestion...")
    try:
        flights = fetch_all_tracked_flights()
        conn = get_connection()
        try:
            for flight in flights:
                insert_flight(conn, flight)
            logger.info(f"Inserted/updated {len(flights)} flight records.")
        finally:
            conn.close()
    except Exception:
        logger.exception("Flight ingestion failed")


def run_weather_ingestion():
    logger.info("Running OpenWeatherMap ingestion...")
    try:
        snapshots = fetch_all_tracked_weather()
        conn = get_connection()
        try:
            for snapshot in snapshots:
                insert_weather_snapshot(conn, snapshot)
            logger.info(f"Inserted {len(snapshots)} weather snapshots.")
        finally:
            conn.close()
    except Exception:
        logger.exception("Weather ingestion failed")


if __name__ == "__main__":
    scheduler = BlockingScheduler()

    # AviationStack: 1x/day -> every 24 hours
    scheduler.add_job(run_flight_ingestion, "interval", hours=24, id="flight_ingestion")

    # OpenWeatherMap: hourly
    scheduler.add_job(run_weather_ingestion, "interval", hours=1, id="weather_ingestion")

    logger.info("Ingestion scheduler starting.")

    if _should_skip_startup_poll():
        logger.info("Skipping initial flight poll (recent data already present).")
    else:
        logger.info("Running an initial flight poll now...")
        run_flight_ingestion()

    # Weather is cheap (1,000 req/day free tier), so always run it on startup.
    run_weather_ingestion()

    logger.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")