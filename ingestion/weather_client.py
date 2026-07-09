# ingestion/weather_client.py
"""
Pulls current weather for each tracked airport from OpenWeatherMap.
Free tier = 1,000 calls/day, so this can run hourly without any rate-limit concerns.
"""

import requests
from datetime import datetime
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL, TRACKED_AIRPORTS


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

    return {
        "airport_code": airport["code"],
        "recorded_at": datetime.utcfromtimestamp(payload.get("dt", datetime.utcnow().timestamp())),
        "temperature_c": main.get("temp"),
        "wind_speed_ms": wind.get("speed"),
        "visibility_m": payload.get("visibility"),
        "precipitation_mm": rain.get("1h", 0.0),
        "condition_code": weather.get("main"),
    }


def fetch_all_tracked_weather() -> list[dict]:
    return [fetch_weather_for_airport(airport) for airport in TRACKED_AIRPORTS]


if __name__ == "__main__":
    snapshots = fetch_all_tracked_weather()
    for s in snapshots:
        print(s)
