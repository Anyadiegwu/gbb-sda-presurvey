# Fiber BOQ Backend

Admin-managed BOQ generator for a fiber ISP: a customer enters an address,
we find the nearest network node (manhole / FDT / FAT / POP) and the real
road distance to it, the customer picks a bandwidth tier, and a priced BOQ is generated
from admin-configurable pricing (and, optionally, an admin-rewritten
pricing formula).

## Stack
- FastAPI + SQLModel
- PostgreSQL **with PostGIS** (nearest-node and nearest-cable queries)
- Geocoding: LocationIQ (free key). Road routing: OSRM (public demo for dev, your own server for production)
- `simpleeval` for safe, sandboxed formula evaluation (no `eval()`)
- JWT auth for the admin side; customer-facing endpoints are public

## Setup (using [uv](https://docs.astral.sh/uv/))

```bash
uv sync                      # install dependencies
cp .env.example .env         # then fill in DATABASE_URL, JWT_SECRET_KEY, LOCATIONIQ_API_KEY
uv run python seed.py        # initial admin + default BOQ items
uv run uvicorn app.main:app --reload
```
API docs: `http://localhost:8000/docs`. The database needs the PostGIS extension
(use the `postgis/postgis` Docker image, or Stack Builder on Windows).
Tables, indexes and the new `node_type`/`source_file` columns are created/added
automatically on startup (safe to run repeatedly on an existing database).

## How the map side works

**Admin uploads a KMZ/KML** -> `POST /admin/fiber-routes/import` (multipart `file`;
optional query params `replace`, `dry_run`, `default_node_type`). Real KMZs mix network
points, poles, splice points, customer sites and hand-drawn pre-survey routes, so every
placemark is classified instead of imported blindly:

| In the file | What happens |
|---|---|
| Manholes / handholes (`MH01`, `EXMH65`, `HH01`, or anything inside a "...MH" folder) | imported as `MH` |
| `FDT8 (Finance)`, `FAT1 (NOC)` (recognised from the point's own name only) | imported as `FDT` / `FAT` |
| `Site BB Madalla`, `Kano DC`, `GBB-NOC`, `...ODF`, and pins in a backbone file's `cities` / `Site` folders | imported as `POP` |
| Poles, splice points (`SP11`) | skipped (`pointsSkipped`) |
| Customer sites from earlier pre-surveys (schools, hospitals...) | skipped (`pointsSkipped.UNCLASSIFIED`) |
| A customer point + its hand-drawn route, routes named by length (`Route - 6998m`), files/folders called SURVEY | routes skipped (`surveyRoutesSkipped`) |
| The same node already imported from another file (same type, within ~1 m) | skipped (`duplicatesSkipped`) |
| Everything else that is a line | imported as a fibre route |

The response lists what every KMZ folder was treated as (`folders`). Use `dry_run=true` to
preview without saving. Each node remembers its folder (`folder`), because hundreds of nodes
share names like `MH01`. Re-uploading a file with the same name replaces its old data.
Fix any single node with `PATCH /admin/manholes/{id}` (`{"nodeType": "FDT"}`).

**Customer gives a location**, either way:
- `POST /quotes/resolve-location {"latitude", "longitude", "nodeTypes"?}` (GPS or map pin)
- `POST /quotes/resolve-address {"address", "nodeTypes"?}` (typed address)

Both return: the nearest node **by road** (the 5 straight-line-closest nodes are
shortlisted with PostGIS, then ranked by real road distance in one OSRM call), the
road route as an encoded polyline, and the node's closest point on the backbone cable
(`fiberlinePointLatitude/Longitude`, `manholeToFiberlineMeters`). `totalDistanceMeters`
feeds `/quotes/calculate` as before.

`POST /quotes/nearest-nodes {"latitude", "longitude"}` returns the closest MH, FDT,
FAT and POP separately (each by road), plus the closest point on the cable itself.

**Drawing the map:** `GET /admin/fiber-routes/geojson` (admin) returns every route and node
as one GeoJSON FeatureCollection (lines simplified to ~11 m so it stays small).
`examples/map_demo.html` is a working Leaflet page showing the whole flow:

```bash
python -m http.server 3000 -d examples   # then open http://localhost:3000/map_demo.html
```

## Tests
```bash
createdb fiber_boq_test   # a database with PostGIS available; the tests create the extension
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/fiber_boq_test uv run pytest
```
Runs against real PostGIS; only LocationIQ/OSRM calls are stubbed.

## Project layout
```
app/
  core/            # config, db session + startup migrations, JWT/password auth
  integrations/
    geo_provider.py  # LocationIQ geocoding + OSRM distance/route
    kml_parser.py    # KMZ/KML -> routes + typed nodes
  features/
    auth/ manholes/ (all node types) routes/ (KMZ import + geojson)
    bandwidth/ pricing/ boq_items/ formula/ quotes/ submissions/
examples/map_demo.html
tests/
```

## Admin capabilities
- `POST /auth/login` -> JWT, sent as `Authorization: Bearer <token>` on every `/admin/*` route.
- `/admin/manholes`: add/edit/remove nodes of any type (lat/lng, `nodeType`).
- `/admin/fiber-routes/import`: KMZ upload (routes + points). `/geojson`: map data. Also list/delete routes.
- `/admin/bandwidth-tiers`, `/admin/pricing-config`, `/admin/formulas`: pricing setup.
- `/admin/submissions`: every BOQ request with contact info, distances, line items, total.

## Before production
- Replace `init_db()` and its inline migrations with Alembic.
- Run your own OSRM (with Nigeria's OSM extract) instead of the public demo server, and
  check LocationIQ's free-tier limits against real traffic.
- Rate-limit the public `/quotes/*` endpoints: each call triggers geocoding/routing requests.
- OSRM snaps points to the nearest road, so road distance excludes any off-road stretch
  between the customer's exact spot and the road. Add an allowance if that matters to pricing.
- Wire up an admin notification (email/Slack) where the `TODO` is in `submissions/router.py`.
