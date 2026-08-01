# Web Dashboard

React + Vite ops dashboard for SkyPulse — a radar-scope-themed view into live
flight, delay, and airport data for Doha Hamad International (DOH).

**Live**: https://airline-delay-intelligence.vercel.app
**Status**: deployed live on Vercel, all pages working, including direct
deep-links to sub-routes.

## Pages

- **Overview** — high-level status/radar view
- **Live Flights** — real-time flight list from the backend, de-duplicated
  to physical flights
- **Delay Stats** — aggregate delay statistics
- **Cascade Risk** — honest "in development" placeholder; gated on data
  volume (delay cascade modeling needs more historical flight data than is
  currently available)
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
- `.env.production` → the live Railway backend URL

Both files are safe to commit — they contain only public URLs, no secrets.

## Deployment notes

- Deployed on Vercel (Hobby/free plan) as a separate project from the
  Railway-hosted backend.
- `vercel.json` adds a SPA rewrite rule so client-side routes (e.g.
  `/flights`) don't 404 when loaded directly rather than navigated to via
  in-app links.
- Always reference the stable production domain
  (`airline-delay-intelligence.vercel.app`), never a per-deployment preview
  URL — those change on every redeploy and will silently break any hardcoded
  reference (CORS origins, docs, CV links).

## Running locally

```bash
npm install
npm run dev
```

Uses `.env.development` automatically, pointing at `http://localhost:8000`.
Run the backend locally too (see `backend/README.md`) for full functionality.

## Building for production

```bash
npm run build
```

Uses `.env.production`, pointing at the live Railway backend.