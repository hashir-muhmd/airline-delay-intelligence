# ingestion/aviationstack_client.py
"""
Pulls live flight status from AviationStack for tracked airports.

Free tier = 100 requests/month, so this is designed to be called a few times
a day (see config.AVIATIONSTACK_POLLS_PER_DAY), pulling departures and arrivals
for each tracked airport in as few calls as possible. Each call can return up
to 100 flights, so a single call captures a full snapshot of airport activity.
"""

import requests
from datetime import datetime
from config import AVIATIONSTACK_API_KEY, AVIATIONSTACK_BASE_URL, TRACKED_AIRPORTS


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _compute_delay_minutes(scheduled, actual):
    if not scheduled or not actual:
        return None
    return int((actual - scheduled).total_seconds() // 60)


def _flight_to_row(raw: dict) -> dict:
    departure = raw.get("departure", {}) or {}
    arrival = raw.get("arrival", {}) or {}
    flight = raw.get("flight", {}) or {}
    airline = raw.get("airline", {}) or {}
    aircraft = raw.get("aircraft", {}) or {}

    scheduled_departure = _parse_datetime(departure.get("scheduled"))
    actual_departure = _parse_datetime(departure.get("actual"))
    scheduled_arrival = _parse_datetime(arrival.get("scheduled"))
    actual_arrival = _parse_datetime(arrival.get("actual"))

    return {
        "flight_number": flight.get("iata") or flight.get("icao") or "UNKNOWN",
        "airline": airline.get("name"),
        "origin": departure.get("iata"),
        "destination": arrival.get("iata"),
        "scheduled_departure": scheduled_departure,
        "actual_departure": actual_departure,
        "scheduled_arrival": scheduled_arrival,
        "actual_arrival": actual_arrival,
        "aircraft_registration": aircraft.get("registration"),
        "status": raw.get("flight_status"),
        "delay_minutes": _compute_delay_minutes(scheduled_departure, actual_departure),
    }


def fetch_flights_for_airport(airport_code: str, direction: str = "dep") -> list[dict]:
    """
    direction: 'dep' for departures, 'arr' for arrivals
    """
    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        f"{direction}_iata": airport_code,
        "limit": 100,
    }
    response = requests.get(AVIATIONSTACK_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"AviationStack error: {payload['error']}")

    raw_flights = payload.get("data", [])
    return [_flight_to_row(f) for f in raw_flights]


def fetch_all_tracked_flights() -> list[dict]:
    """
    Pulls departures and arrivals for every tracked airport.
    Each airport = 2 API calls (departures + arrivals), so keep TRACKED_AIRPORTS
    short given the 100-request/month free tier.
    """
    all_flights = []
    for airport in TRACKED_AIRPORTS:
        code = airport["code"]
        all_flights.extend(fetch_flights_for_airport(code, direction="dep"))
        all_flights.extend(fetch_flights_for_airport(code, direction="arr"))
    return all_flights


if __name__ == "__main__":
    flights = fetch_all_tracked_flights()
    print(f"Fetched {len(flights)} flights")
    for f in flights[:5]:
        print(f)
