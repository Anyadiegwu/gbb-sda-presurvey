"""
Tests run against a REAL PostgreSQL + PostGIS database (the nearest-node and
nearest-cable queries are PostGIS SQL, so mocking the DB would test nothing).
Only the external geocoder/OSRM calls are stubbed.

    createdb fiber_boq_test            # once
    TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/fiber_boq_test pytest
"""
import io
import os
import zipfile

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://fiber:fiber@localhost:5432/fiber_boq_test"
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("DEFAULT_ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "admin12345")
os.environ["LOCATIONIQ_API_KEY"] = ""

import psycopg  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402


def _ensure_test_database():
    url = make_url(os.environ["DATABASE_URL"])
    with psycopg.connect(
        host=url.host, port=url.port or 5432, user=url.username,
        password=url.password, dbname="postgres", autocommit=True,
    ) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,)).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{url.database}"')


_ensure_test_database()

from app.core.database import engine  # noqa: E402
from app.integrations import geo_provider  # noqa: E402
from app.main import app  # noqa: E402
import seed  # noqa: E402


# --- polyline helper (Google/OSRM precision-5 encoding) so the stubbed route
# --- looks like what OSRM really returns -----------------------------------
def encode_polyline(points):
    out, prev_lat, prev_lon = [], 0, 0
    for lat, lon in points:
        ilat, ilon = round(lat * 1e5), round(lon * 1e5)
        for v in (ilat - prev_lat, ilon - prev_lon):
            v = ~(v << 1) if v < 0 else v << 1
            while v >= 0x20:
                out.append(chr((0x20 | (v & 0x1F)) + 63))
                v >>= 5
            out.append(chr(v + 63))
        prev_lat, prev_lon = ilat, ilon
    return "".join(out)


KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>t</name>
<Folder><name>Backbone Test</name>
  <Folder><name>Sites</name>
    <Placemark><name>Kaduna</name><Point><coordinates>7.4433,10.5693,0</coordinates></Point></Placemark>
  </Folder>
  <Placemark><name>FDT-01</name><Point><coordinates>7.4000,9.0000,0</coordinates></Point></Placemark>
  <Placemark><name>FAT-01</name><Point><coordinates>7.4100,9.0100,0</coordinates></Point></Placemark>
  <Folder><name>Metro MH</name><Folder><name>Kano.kml</name><Folder><name>Site</name>
    <Placemark><name>MH 07
       Wuse</name><Point><coordinates>7.4500,9.0500,0</coordinates></Point></Placemark>
    <Placemark><name>Server Room</name><Point><coordinates>7.4510,9.0510,0</coordinates></Point></Placemark>
    <Placemark><name>SP3</name><Point><coordinates>7.4520,9.0520,0</coordinates></Point></Placemark>
  </Folder></Folder></Folder>
  <Folder><name>Pole</name>
    <Placemark><name>Pole 4</name><Point><coordinates>7.4600,9.0600,0</coordinates></Point></Placemark>
  </Folder>
  <Folder><name>Customer School</name>
    <Placemark><name>Customer School</name><Point><coordinates>7.3000,9.3000,0</coordinates></Point></Placemark>
    <Placemark><name>Route - 6998m</name><LineString><coordinates>7.3000,9.3000,0 7.4000,9.0500,0</coordinates></LineString></Placemark>
  </Folder>
  <Placemark><name>S1 Abuja - Madalla</name><LineString><coordinates>
     7.3000,9.0000,0 7.5000,9.0000,0 7.7000,9.0000,0</coordinates></LineString></Placemark>
</Folder></Document></kml>"""


def make_kmz(kml: str = KML) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("doc.kml", kml)
    return buf.getvalue()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # runs startup -> init_db (PostGIS + tables + indexes)
        yield c


@pytest.fixture(autouse=True)
def clean_db(client):
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE manholes, fiber_routes, boq_submissions, boq_items, "
            "calculation_formulas RESTART IDENTITY CASCADE"
        ))
    seed.run()
    yield


@pytest.fixture
def admin_headers(client):
    r = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin12345"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


@pytest.fixture(autouse=True)
def stub_external_services(monkeypatch):
    """No network in tests: road distance = straight line x 1.3, polyline is
    the straight segment, geocoders return fixed values."""
    from app.features.manholes.repository import haversine_meters

    def fake_distances(origin, destinations):
        return [haversine_meters(origin[0], origin[1], la, lo) * 1.3 for la, lo in destinations]

    monkeypatch.setattr(geo_provider, "get_distances_to_candidates", fake_distances)
    monkeypatch.setattr(
        geo_provider, "get_route_polyline", lambda o, d: encode_polyline([o, d])
    )
    monkeypatch.setattr(geo_provider, "reverse_geocode", lambda lat, lon: "Stubbed Street, Abuja")
    monkeypatch.setattr(
        geo_provider, "geocode_address", lambda a: (9.0010, 7.4010, "Stubbed address, Abuja")
    )


@pytest.fixture
def imported(client, admin_headers):
    r = client.post(
        "/admin/fiber-routes/import",
        headers=admin_headers,
        files={"file": ("test.kmz", make_kmz(), "application/vnd.google-earth.kmz")},
    )
    assert r.status_code == 200, r.text
    return r.json()
