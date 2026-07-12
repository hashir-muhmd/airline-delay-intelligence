# ingestion/config.py
"""
Central config for the ingestion service.
Add more airports here later (DXB, SIN, LHR, etc.) once the DOH pipeline is validated.
"""

import os
from dotenv import load_dotenv

load_dotenv()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/airline_delay_intelligence")

# Airports tracked by the ingestion service.
# code: IATA code, lat/lon: for weather lookups
TRACKED_AIRPORTS = [
    {"code": "DOH", "name": "Hamad International Airport", "lat": 25.2731, "lon": 51.6081, "is_hub": True},
]

# AviationStack free tier = 100 requests/month.
# Each call returns up to 100 flights for a given airport query, so we poll
# infrequently but broadly (departures + arrivals) rather than per-flight.
# 1 poll/day × 2 calls/airport × 1 airport × 30 days = 60 calls/month (safe margin).
AVIATIONSTACK_POLLS_PER_DAY = 1  # once daily
AVIATIONSTACK_BASE_URL = "http://api.aviationstack.com/v1/flights"

# OpenWeatherMap free tier = 1,000 calls/day, so this can run far more often.
OPENWEATHER_POLLS_PER_DAY = 24  # hourly
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
