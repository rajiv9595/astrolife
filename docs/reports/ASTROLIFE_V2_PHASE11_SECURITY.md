# ASTROLIFE V2 — PHASE 11 — SECURITY

## Static audit (131-test Python suite gates this)
Zero `eval(`/`Function(`/`dangerouslySetInnerHTML` in app source; no
hardcoded secrets/tokens/keys (AWS/GCP patterns scanned); Bearer token in
sessionStorage (tab-scoped, not persistent localStorage); env-first API URL
(`VITE_API_URL`, localhost dev fallback only); query encoding in geocode
builders; no `http://` literals in the new client; research endpoints
read-only (no POST/PUT/DELETE in `routes/research.py`).

## Pre-existing findings (documented, not altered)
- Backend CORS `allow_origins=["*"]` (backend/app.py). Recommendation:
  restrict to deployed frontend origins when domains are final. Not changed
  to avoid breaking existing deployments.
- `localStorage 'chartData'` caches last chart client-side (staleness risk
  across users mitigated by fresh-fetch-on-mount in YogasPage and nav-param
  flow in GuestKundli; documented).
- `npm run lint` has no eslint config (pre-existing broken script; build
  via Vite validates syntax of all touched files).
- `bg-cosmic-black` is a dead class (absent from tailwind config/CSS);
  cosmetic no-op, left untouched.

## Calculation firewall
Static scan distinguishes DISPLAY/TYPE/API from calculation (comment,
component-name, import, and backend-field-read whitelisting): zero
unauthorized implementations of ephemeris/ayanamsha/houses/Vargas/
Nakshatra/Dasha/Shadbala/Yoga/Dosha/Jaimini/transit/prediction in the
browser; production bundle contains no Swiss Ephemeris (verified).

## Observability
Errors surfaced as kind+message without stack traces; no birth-data,
token, or secret logging added.
