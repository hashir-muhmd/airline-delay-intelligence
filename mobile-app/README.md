# Mobile app

Flutter companion app to the SkyPulse web dashboard, giving a traveler-facing view of live flight and delay status for Doha Hamad International (DOH).

**Status: built and working.** Runs locally against the same backend as the web dashboard.

## What it does

- **Splash screen** with a brief animated radar intro, matching the dashboard's visual identity
- **Overview tab** — animated radar visual (concentric rings, rotating sweep, pinging markers) plus a quick delay-stats summary, echoing the web dashboard's Overview page
- **Flights tab** — live DOH flight list (departures and arrivals), de-duplicated codeshares, status/delay badges
- **Stats tab** — median/mean delay and sample size, pulled from the same `/stats/delays` endpoint the web dashboard uses
- **Auto-refresh** every 60 seconds, plus manual pull-to-refresh on every tab, with a "last updated" timestamp shown in the top bar

## What it deliberately doesn't do

No delay predictions are shown. The backend doesn't currently serve a `/predictions` endpoint, and building one wouldn't be honest yet — the ML regressor's R² is negative at current data volume (see `ml/README.md`), meaning it doesn't outperform simply guessing the average delay. Shipping a "predicted delay" number to a traveler-facing app on top of a model that isn't better than a naive guess would misrepresent what this project has actually achieved. This will be revisited once the regressor is genuinely predictive.

No login or user accounts — there's no per-user data (no saved flights, no personal alerts) that would justify one.

## Structure

```
lib/
├── main.dart              # app entry, theme, routes to SplashScreen
├── api.dart                # backend API base URL + fetch helpers
├── theme.dart               # shared color constants
├── screens/
│   ├── splash_screen.dart
│   └── main_tab_screen.dart   # bottom-tab shell, owns data fetching + auto-refresh
├── tabs/
│   ├── overview_tab.dart
│   ├── flights_tab.dart
│   └── stats_tab.dart
└── widgets/
    ├── radar_hero.dart / radar_painter.dart   # animated radar visual
    ├── top_bar.dart
    ├── delay_stats_card.dart
    ├── flight_tile.dart
    └── error_banner.dart
```

Mirrors the web dashboard's own `pages/` + shared `api.js` structure, adapted to Flutter's conventions.

## Running locally

Requires the backend running locally first (see `../backend/README.md`).

```bash
flutter pub get
flutter run
```

The app points at `http://10.0.2.2:8000` by default — this is the standard alias the **Android emulator** uses to reach the host machine's `localhost`. If testing on a physical device instead, change `apiBase` in `lib/api.dart` to your machine's real LAN IP (and ensure the device is on the same network).

## Testing

```bash
flutter test
```

One smoke test currently exists (`test/widget_test.dart`), confirming the app builds and the splash screen renders its real content. Not comprehensive — a reasonable starting point given this app's current scope, not a claim of full test coverage.