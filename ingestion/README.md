# Ingestion

Scheduled service that polls flight and weather APIs and writes to PostgreSQL.

Planned contents:
- `aviationstack_client.py` — live flight status/delay data
- `weather_client.py` — OpenWeatherMap airport weather
- `scheduler.py` — polling job (every 15-30 min, respects API quotas)
- `config.py` — tracked airports/routes (includes DOH as primary hub)

Status: not yet implemented.
