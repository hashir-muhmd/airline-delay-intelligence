# Database

PostgreSQL schema and migrations.

Planned tables:
- `flights` — core historical flight + delay data
- `weather_snapshots` — airport weather tied to flight timestamps
- `airports` — airport metadata, hub flags
- `predictions` — model outputs over time
- `cascade_links` — aircraft/crew rotation links for cascade modeling

Status: not yet implemented.
