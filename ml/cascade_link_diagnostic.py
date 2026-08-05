# ml/cascade_link_diagnostic.py
"""
Diagnostic script: checks whether the flights table currently contains any
real "cascade link" candidates -- pairs of flights sharing the same
aircraft_icao24, where one flight arrives and the same aircraft departs
again within a plausible turnaround window.

This is deliberately NOT the cascade model itself. It answers a narrower,
more honest question first: "does linking flights by aircraft_icao24 even
find anything on our real data yet?" Given icao24 capture only started
recently (see ingestion/README.md), it's entirely possible this finds zero
or very few pairs right now -- that's a genuine, useful answer, not a
failure of this script.

Definition used for a "cascade link candidate":
  - Same aircraft_icao24 on both flights (and non-null)
  - Flight A arrives at some airport
  - Flight B departs from that SAME airport
  - Flight B's scheduled_departure is AFTER flight A's scheduled_arrival
  - The gap between them is within a plausible turnaround window
    (MIN_TURNAROUND_MINUTES to MAX_TURNAROUND_MINUTES) -- too short isn't
    physically possible (no time to deplane/board), too long isn't a real
    "next leg", it's just the same aircraft's next flight days later.

Run with:
    cd ml
    python cascade_link_diagnostic.py
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# A real turnaround needs at least this much time (deplaning, cleaning,
# boarding) -- below this, it's not physically a same-aircraft next leg.
MIN_TURNAROUND_MINUTES = 30

# Above this, it's not really "the next leg" anymore -- more likely the
# aircraft sat overnight or flew elsewhere in between (which we wouldn't
# see if that other flight isn't DOH-related and thus not tracked).
MAX_TURNAROUND_MINUTES = 6 * 60  # 6 hours


def load_flights(engine) -> pd.DataFrame:
    query = """
        SELECT id, flight_number, origin, destination,
               scheduled_departure, scheduled_arrival,
               aircraft_icao24, status, delay_minutes
        FROM flights
        WHERE aircraft_icao24 IS NOT NULL
    """
    return pd.read_sql(query, engine)


def find_cascade_candidates(flights: pd.DataFrame) -> pd.DataFrame:
    flights = flights.copy()
    flights["scheduled_departure"] = pd.to_datetime(flights["scheduled_departure"], utc=True)
    flights["scheduled_arrival"] = pd.to_datetime(flights["scheduled_arrival"], utc=True)

    candidates = []

    # Group by aircraft so we only ever compare flights that share the same
    # airframe -- avoids an O(n^2) scan across the whole table.
    for icao24, group in flights.groupby("aircraft_icao24"):
        group = group.sort_values("scheduled_departure")
        rows = group.to_dict("records")

        for arriving in rows:
            if pd.isna(arriving["scheduled_arrival"]):
                continue
            for departing in rows:
                if arriving["id"] == departing["id"]:
                    continue
                if pd.isna(departing["scheduled_departure"]):
                    continue
                if departing["origin"] != arriving["destination"]:
                    continue

                gap = departing["scheduled_departure"] - arriving["scheduled_arrival"]
                gap_minutes = gap.total_seconds() / 60

                if MIN_TURNAROUND_MINUTES <= gap_minutes <= MAX_TURNAROUND_MINUTES:
                    candidates.append(
                        {
                            "aircraft_icao24": icao24,
                            "upstream_flight_id": arriving["id"],
                            "upstream_flight_number": arriving["flight_number"],
                            "upstream_route": f"{arriving['origin']}->{arriving['destination']}",
                            "upstream_scheduled_arrival": arriving["scheduled_arrival"],
                            "upstream_delay_minutes": arriving["delay_minutes"],
                            "downstream_flight_id": departing["id"],
                            "downstream_flight_number": departing["flight_number"],
                            "downstream_route": f"{departing['origin']}->{departing['destination']}",
                            "downstream_scheduled_departure": departing["scheduled_departure"],
                            "downstream_delay_minutes": departing["delay_minutes"],
                            "turnaround_minutes": round(gap_minutes, 1),
                        }
                    )

    return pd.DataFrame(candidates)


def main():
    load_dotenv(dotenv_path=Path(__file__).parent.parent / "ingestion" / ".env")
    db_url = os.getenv("DATABASE_URL")
    if db_url is None:
        logger.error("DATABASE_URL not found -- check the .env path above matches")
        sys.exit(1)

    engine = create_engine(db_url)
    flights = load_flights(engine)

    logger.info(f"Flights with a non-null aircraft_icao24: {len(flights)}")
    logger.info(f"Distinct aircraft (icao24 values) seen: {flights['aircraft_icao24'].nunique()}")

    if len(flights) == 0:
        logger.warning(
            "No flights have aircraft_icao24 populated yet. This is expected "
            "if this is being run very shortly after the icao24 fix shipped -- "
            "not every flight gets a value, and it takes time to accumulate. "
            "Re-run this script periodically as more data comes in."
        )
        return

    candidates = find_cascade_candidates(flights)

    print(f"\n--- Cascade link candidates found: {len(candidates)} ---")
    print(
        f"(Same aircraft_icao24, arrival->departure at the same airport, "
        f"turnaround between {MIN_TURNAROUND_MINUTES} and {MAX_TURNAROUND_MINUTES} minutes)\n"
    )

    if len(candidates) == 0:
        print(
            "No candidates yet. This is a genuine, informative result -- it "
            "means real cascade-model data isn't available yet, not that the "
            "linking logic is broken. Likely causes: too few flights currently "
            "have icao24 populated, and/or DOH-only tracking means an "
            "aircraft's OTHER leg (outside DOH) isn't visible to us at all, "
            "breaking the arrival->departure chain even when icao24 matches."
        )
    else:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)
        print(candidates.sort_values("turnaround_minutes").to_string(index=False))

        both_have_delay = candidates.dropna(
            subset=["upstream_delay_minutes", "downstream_delay_minutes"]
        )
        print(
            f"\nOf these, {len(both_have_delay)} candidate pair(s) have delay "
            f"data on BOTH flights -- these are the only ones actually usable "
            f"for validating a cascade effect (does upstream delay correlate "
            f"with downstream delay?). {len(candidates) - len(both_have_delay)} "
            f"pair(s) are missing delay data on at least one side."
        )


if __name__ == "__main__":
    main()