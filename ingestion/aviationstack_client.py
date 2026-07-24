# ingestion/aviationstack_client.py
"""
Pulls live flight status from AviationStack for tracked airports.

Free tier = 100 requests/month, so this is designed to be called a few times
a day (see config.AVIATIONSTACK_POLLS_PER_DAY), pulling departures and arrivals
for each tracked airport in as few calls as possible. Each call can return up
to 100 flights, so a single call captures a full snapshot of airport activity.
"""

import logging
import re
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from config import AVIATIONSTACK_API_KEY, AVIATIONSTACK_BASE_URL, TRACKED_AIRPORTS

logger = logging.getLogger(__name__)

_UTC = ZoneInfo("UTC")

# AviationStack usually sends an IANA timezone name (e.g. "Asia/Qatar"), but
# for some stations it instead sends a raw numeric UTC offset (e.g. "+8",
# "-5", "+05:30"). This regex catches that second format.
_OFFSET_RE = re.compile(r"^([+-])(\d{1,2})(?::?(\d{2}))?$")


def _resolve_timezone(timezone_name):
    """
    Resolve a timezone field from AviationStack into a usable tzinfo,
    whether it's an IANA name or a raw numeric UTC offset. Returns None if
    it can't be resolved (missing, or a format we don't recognize).
    """
    if not timezone_name:
        return None
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        pass
    match = _OFFSET_RE.match(timezone_name.strip())
    if match:
        sign, hours, minutes = match.groups()
        delta = timedelta(hours=int(hours), minutes=int(minutes) if minutes else 0)
        if sign == "-":
            delta = -delta
        return timezone(delta)
    return None


def _parse_datetime(value, timezone_name=None):
    """
    Parse an AviationStack scheduled/actual timestamp.

    AviationStack tags these timestamps with a UTC offset (or trailing "Z"),
    but the wall-clock value is actually the STATION'S OWN LOCAL TIME, not
    true UTC -- confirmed by cross-checking QR87 (DOH departure) and AT5741
    (Perth->DOH arrival) against Hamad International's own live flight-status
    site. So we discard the (incorrect) offset AviationStack attaches, keep
    only the naive date/time, and localize it ourselves using the
    `timezone` field AviationStack provides on each departure/arrival block
    (either an IANA name like "Asia/Qatar", or sometimes a raw numeric
    offset like "+8" -- see _resolve_timezone above).
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    naive_local = parsed.replace(tzinfo=None)

    station_tz = _resolve_timezone(timezone_name)
    if station_tz is None:
        logger.warning(
            "Could not resolve station timezone %r for timestamp %r; "
            "storing naive value as UTC (may be wrong -- investigate this flight).",
            timezone_name, value,
        )
        return naive_local.replace(tzinfo=_UTC)

    return naive_local.replace(tzinfo=station_tz).astimezone(_UTC)


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

    departure_tz = departure.get("timezone")
    arrival_tz = arrival.get("timezone")

    scheduled_departure = _parse_datetime(departure.get("scheduled"), departure_tz)
    actual_departure = _parse_datetime(departure.get("actual"), departure_tz)
    scheduled_arrival = _parse_datetime(arrival.get("scheduled"), arrival_tz)
    actual_arrival = _parse_datetime(arrival.get("actual"), arrival_tz)

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