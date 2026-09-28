# Fiber BOQ Backend

Admin-managed BOQ generator for a fiber ISP: a customer enters an address,
we find the nearest POP manhole and the real routing distance via Google
Maps, the customer picks a bandwidth tier, and a priced BOQ is generated
from admin-configurable pricing (and, optionally, an admin-rewritten
pricing formula).

## Stack
- FastAPI + SQLModel
- PostgreSQL
- Google Maps (Geocoding, Distance Matrix, Directions APIs) — server-side only
- `simpleeval` for safe, sandboxed formula evaluation (no `eval()`)
- JWT auth for the admin side; customer-facing endpoints are public

## Setup (using [uv](https://docs.astral.sh/uv/))

```bash
# 1. Install dependencies (creates .venv automatically)
uv sync

# 2. Copy env file and fill in real values
cp .env.example .env
# - set DATABASE_URL to your Postgres instance
# - set GOOGLE_MAPS_SERVER_KEY (a server-restricted key with Geocoding,
#   Distance Matrix, and Directions APIs enabled — see note below)
# - set JWT_SECRET_KEY to a long random string

# 3. Seed an initial admin account + default pricing/formula
uv run python seed.py

# 4. Run the dev server
uv run uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

## Google Maps key setup
Create **two separate** API keys in the same Google Cloud project:
- **Server key** (`GOOGLE_MAPS_SERVER_KEY` in `.env`): enable Geocoding API,
  Distance Matrix API, Directions API. Restrict it by server IP address.
  This is the only key this backend uses.
- **Browser key** (only needed if/when the frontend shows a live map):
  enable Maps JavaScript API only, restrict by HTTP referrer to your
  domain. Never give this key Geocoding/Directions scopes.

## Project layout
```
app/
  core/            # config, db session, JWT/password auth
  integrations/
    google_maps.py # geocoding + distance/directions wrapper
  features/
    auth/          # admin login/register
    manholes/      # admin CRUD on POP manhole locations
    bandwidth/     # admin CRUD on bandwidth tiers (public read for the form)
    pricing/       # admin-editable key/value pricing inputs
    formula/       # admin-editable calculation formula (sandboxed eval)
    quotes/        # public: resolve-address -> nearest manhole -> calculate BOQ
    submissions/   # public: submit contact form + quote; admin: view/manage
```

## Customer flow
1. `POST /quotes/resolve-address {"address": "..."}` → geocodes, shortlists
   nearby manholes cheaply (Haversine), then makes **one** Distance Matrix
   API call to get real routing distance to all candidates, then **one**
   Directions API call for the winning candidate's polyline.
2. `GET /bandwidth-tiers/` → populate the bandwidth dropdown.
3. `POST /quotes/calculate {...}` → runs the active pricing formula against
   distance + tier + admin pricing config, returns line items + total.
4. `POST /submissions/` → customer submits contact details alongside the
   quote just generated; this is what shows up in the admin dashboard.

## Admin capabilities
- `POST /auth/login` → get a JWT, send as `Authorization: Bearer <token>`
  on every `/admin/*` route.
- `/admin/manholes` — add/edit/remove manhole locations (lat/lng).
- `/admin/bandwidth-tiers` — add/edit/remove tiers and their base price.
- `/admin/pricing-config` — edit `price_per_meter`, `installation_fee`,
  `markup_percent`, or add new keys (just remember to reference any new
  key in the active formula for it to actually be used).
- `/admin/formulas` — write a new pricing expression, validate it
  (`POST /admin/formulas/validate`), then activate it. Only one formula
  is active at a time. Allowed variable names: `distance_m`,
  `distance_km`, `price_per_meter`, `tier_base_price`,
  `installation_fee`, `markup_percent`.
- `/admin/submissions` — view every BOQ request with the customer's
  contact info, quoted distance, line items, and total.

## Before production
- Replace `init_db()` in `app/main.py` with Alembic migrations.
- Lock down `POST /auth/register` (it currently lets anyone create an
  admin account — fine for initial setup, not fine to leave open).
- Add rate limiting to the public `/quotes/*` endpoints — every call can
  trigger billed Google Maps API requests.
- Decide on and wire up an admin notification channel (email/Slack) in
  `submissions/router.py` where the `TODO` is.
- Decide on the frontend and CORS origin(s) in `.env` (`FRONTEND_URL`).
