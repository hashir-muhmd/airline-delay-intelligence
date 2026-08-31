# Web Dashboard

React + Vite ops dashboard for SkyPulse — a radar-scope-themed view into live
flight, delay, and airport data for Doha Hamad International (DOH).

**Live (frontend only)**: https://airline-delay-intelligence.vercel.app
**Status**: deployed on Vercel, all pages/routes working. The backend it
originally pointed to (Railway) is no longer running — see the root
`README.md`'s "Deployment history" section. Live data only loads when
pointed at a locally-run backend; see Running locally below.

## Pages

- **Overview** — high-level status/radar view
- **Live Flights** — real-time flight list from the backend, de-duplicated
  to physical flights
- **Delay Stats** — aggregate delay statistics
- **Cascade Risk** — live-updating page (calls `GET /cascade/stats`),
  reporting the current count of matched same-aircraft arrival→departure
  pairs found in the data. Currently reports 0 candidates, with the
  structural reason (DOH-only tracking) explained in-page and in
  `ml/README.md`. Not a static placeholder — the numbers shown update
  automatically as more data is ingested.
- **Airports** — tracked airports, with a collapsible world route map

## Design system

Dark navy, radar-scope motif:
- Signal green `#00D9A3` — on-time / live status
- Amber `#FFB020` — delays
- IBM Plex Mono — data/numeric display
- Space Grotesk — headings

Design tokens live in `src/index.css`.

## Tech stack

- React 19 + Vite
- `react-router-dom` for routing
- `react-simple-maps` + `d3-geo` + `prop-types` for the airport route map
  (React 19 requires `legacy-peer-deps=true` in `.npmrc`, since
  `react-simple-maps`'s peer dependency only officially supports React 16–18)

## API configuration

`src/api.js` resolves `API_BASE` from `VITE_API_BASE` at **build time** (Vite
bakes env vars into the compiled bundle — this matters when debugging "why
isn't my env var working" issues, since changing the value after a build
requires a fresh build/redeploy to take effect).

- `.env.development` → `http://localhost:8000`
- `.env.production` → previously the live Railway backend URL; now stale,
  since that backend is no longer running (see Deployment notes below)

Both files are safe to commit — they contain only public URLs, no secrets.

## Deployment notes

- Deployed on Vercel (Hobby/free plan) as a separate project from the
  backend, which previously ran on Railway.
- `vercel.json` adds a SPA rewrite rule so client-side routes (e.g.
  `/flights`) don't 404 when loaded directly rather than navigated to via
  in-app links.
- **`.env.production` currently points at a dead URL.** The Railway backend
  it references was retired after the trial expired (see root `README.md`).
  The Vercel deployment above still serves the frontend correctly, but any
  page that fetches live data will show a "couldn't reach the API" state,
  since there's nothing running at that URL anymore. This is expected and
  documented, not a bug — the project's full functionality is demonstrated
  by running the stack locally (see below), not via the stale Vercel URL.
- If this project is redeployed to a live backend in the future, always
  reference that backend's stable production domain in `.env.production`,
  never a per-deployment preview URL.

## Running locally

```bash
npm install
npm run dev
```

Uses `.env.development` automatically, pointing at `http://localhost:8000`.
Run the backend locally too (see `backend/README.md`) for full functionality
— this is the correct way to see the full working system, since the
Vercel-hosted version's backend is offline.

## Building for production

```bash
npm run build
```

Uses `.env.production`. As noted above, this currently points at a retired
Railway URL — update it to a real backend URL before deploying a fresh
build anywhere.