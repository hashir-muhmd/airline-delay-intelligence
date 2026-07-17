# ingestion/weather_client.py
"""
Pulls current weather for each tracked airport from OpenWeatherMap.
Free tier = 1,000 calls/day, so this can run hourly without any rate-limit concerns.
"""

import logging
import requests
from datetime import datetime, timezone
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL, TRACKED_AIRPORTS

logger = logging.getLogger(__name__)


def fetch_weather_for_airport(airport: dict) -> dict:
    params = {
        "lat": airport["lat"],
        "lon": airport["lon"],
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    response = requests.get(OPENWEATHER_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    main = payload.get("main", {})
    wind = payload.get("wind", {})
    weather = (payload.get("weather") or [{}])[0]
    rain = payload.get("rain", {})

    recorded_ts = payload.get("dt", datetime.now(timezone.utc).timestamp())

    return {
        "airport_code": airport["code"],
        "recorded_at": datetime.fromtimestamp(recorded_ts, tz=timezone.utc),
        "temperature_c": main.get("temp"),
        "wind_speed_ms": wind.get("speed"),
        "visibility_m": payload.get("visibility"),
        "precipitation_mm": rain.get("1h", 0.0),
        "condition_code": weather.get("main"),
    }


def fetch_all_tracked_weather() -> list[dict]:
    """
    Fetches weather for every tracked airport. Each airport is isolated in
    its own try/except so one failure (timeout, bad response, etc.) doesn't
    abort the whole batch and lose weather data for every other airport.
    """
    snapshots = []
    for airport in TRACKED_AIRPORTS:
        try:
            snapshots.append(fetch_weather_for_airport(airport))
        except Exception:
            logger.exception(f"Failed to fetch weather for airport {airport.get('code')}")
    return snapshots


if __name__ == "__main__":
    weather_snapshots = fetch_all_tracked_weather()
    for s in weather_snapshots:
        print(s)