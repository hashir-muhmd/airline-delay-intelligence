"""
scripts/enrich_airports.py

One-off script to enrich stub airport rows (code only) with real metadata
(name, city, country, latitude, longitude) pulled from the OurAirports
public dataset: https://ourairports.com/data/airports.csv

Usage:
    python scripts/enrich_airports.py
"""

import os
import csv
import io
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env lives in ingestion/, not scripts/
load_dotenv(dotenv_path=Path(__file__).parent.parent / "ingestion" / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found — check .env path")

OURAIRPORTS_CSV_URL = "https://ourairports.com/data/airports.csv"


def fetch_ourairports_data() -> dict:
    """
    Downloads the OurAirports CSV and returns a dict keyed by IATA code,
    since our `airports.code` column stores IATA codes (e.g. 'DOH', 'LHR').
    """
    print("Downloading OurAirports reference data...")
    response = requests.get(OURAIRPORTS_CSV_URL, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))
    by_iata = {}

    for row in reader:
        iata = (row.get("iata_code") or "").strip().upper()
        if not iata:
            continue  # skip airports with no IATA code, we can't match them
        by_iata[iata] = {
            "name": row.get("name", "").strip(),
            "city": row.get("municipality", "").strip(),
            "country": row.get("iso_country", "").strip(),
            "latitude": row.get("latitude_deg"),
            "longitude": row.get("longitude_deg"),
        }

    print(f"Loaded {len(by_iata)} airports with IATA codes from OurAirports")
    return by_iata


def get_stub_airport_codes(engine) -> list[str]:
    """Returns airport codes currently missing name/latitude (stub rows)."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT code FROM airports WHERE name IS NULL OR latitude IS NULL")
        )
        return [row[0] for row in result]


def enrich_airports(engine, reference_data: dict):
    stub_codes = get_stub_airport_codes(engine)
    print(f"Found {len(stub_codes)} stub airport rows to enrich")

    matched, unmatched = [], []

    with engine.begin() as conn:  # begin() auto-commits on success, rolls back on error
        for code in stub_codes:
            info = reference_data.get(code)
            if info is None:
                unmatched.append(code)
                continue

            conn.execute(
                text("""
                    UPDATE airports
                    SET name = :name,
                        city = :city,
                        country = :country,
                        latitude = :latitude,
                        longitude = :longitude
                    WHERE code = :code
                """),
                {
                    "name": info["name"] or None,
                    "city": info["city"] or None,
                    "country": info["country"] or None,
                    "latitude": float(info["latitude"]) if info["latitude"] else None,
                    "longitude": float(info["longitude"]) if info["longitude"] else None,
                    "code": code,
                },
            )
            matched.append(code)

    print(f"\nEnriched: {len(matched)} airports")
    if matched:
        print(f"  {', '.join(matched)}")

    print(f"\nUnmatched (no IATA match in OurAirports): {len(unmatched)} airports")
    if unmatched:
        print(f"  {', '.join(unmatched)}")
        print("  -> These may need manual lookup or are non-standard/regional codes.")


def main():
    engine = create_engine(DATABASE_URL)
    reference_data = fetch_ourairports_data()
    enrich_airports(engine, reference_data)


if __name__ == "__main__":
    main()