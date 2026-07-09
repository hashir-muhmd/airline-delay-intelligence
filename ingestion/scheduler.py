# ingestion/scheduler.py
"""
Runs the ingestion jobs on a schedule:
- AviationStack: a few times a day (respects 100 req/month free tier)
- OpenWeatherMap: hourly (well within 1,000 req/day free tier)

Run with: python scheduler.py
Leave this running in a terminal (or set up as a background service later)
so historical data accumulates continuously.
"""

import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

from db import get_connection, insert_flight, insert_weather_snapshot
from aviationstack_client import fetch_all_tracked_flights
from weather_client import fetch_all_tracked_weather

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


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

    # AviationStack: 3x/day -> roughly every 8 hours
    scheduler.add_job(run_flight_ingestion, "interval", hours=8, id="flight_ingestion")

    # OpenWeatherMap: hourly
    scheduler.add_job(run_weather_ingestion, "interval", hours=1, id="weather_ingestion")

    logger.info("Ingestion scheduler starting. Running an initial pass now...")
    run_flight_ingestion()
    run_weather_ingestion()

    logger.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
