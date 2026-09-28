"""
Free-tier geocoding + routing for development/testing:
- Geocoding: LocationIQ (https://locationiq.com) -- free tier, 5,000
  requests/day, requires a free API key (no credit card). This is a real
  API product (not a public demo instance), so it doesn't block
  programmatic backend requests the way Nominatim/Photon's public demo
  servers do.
- Distance matrix + route polyline: OSRM (Open Source Routing Machine)

Both are fine for local development and low-volume testing, NOT fine for
real production traffic:
- LocationIQ's free tier is rate/volume limited -- see their pricing page
  before relying on this for real customer traffic.
- OSRM's public demo server (router.project-osrm.org) is explicitly for
  light testing only, with no uptime guarantee. It's this server, not
  LocationIQ, that's usually behind occasional intermittent 502s here --
  see the retry wrapper below.

Swap this module out for a paid provider (Google, Mapbox, HERE) or
self-hosted instances before any real production traffic. The public
function signatures here match the original Google-based module exactly,
so nothing else in the app needs to change if you swap providers again --
just replace the body of these three functions.
"""

import time
from typing import Callable, List, Optional, Tuple, TypeVar

import requests

from app.core.config import LOCATIONIQ_API_KEY

LOCATIONIQ_URL = "https://us1.locationiq.com/v1/search"
OSRM_BASE_URL = "https://router.project-osrm.org"

# --- Retry tuning ---------------------------------------------------------
# The OSRM public demo server has no uptime guarantee and occasionally
# times out or drops a request under load, especially on a route/location
# it hasn't served before. Retrying a couple of times with a short backoff
# clears up the vast majority of these without the customer ever seeing a
# 502. LocationIQ is a real paid-tier product and much less likely to need
# this, but there's no harm in covering it too.
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1  
REQUEST_TIMEOUT_SECONDS = 10

T = TypeVar("T")


class GeoProviderError(Exception):
    pass


def _with_retry(operation_name: str, fn: Callable[[], T]) -> T:
    """
    Runs fn() up to MAX_ATTEMPTS times, retrying only on network-level
    failures (timeouts, connection errors, 5xx responses from
    raise_for_status()) -- i.e. failures that are plausibly transient.
    Logical failures (bad address, no route found) are raised by fn()
    itself as GeoProviderError and are NOT retried here, since retrying
    those wastes time without any chance of a different outcome.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < MAX_ATTEMPTS:
                delay = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                time.sleep(delay)
                continue
    raise GeoProviderError(
        f"{operation_name} failed after {MAX_ATTEMPTS} attempts: {last_exc}"
    ) from last_exc


def geocode_address(address: str) -> Tuple[float, float, str]:
    """Returns (latitude, longitude, formatted_address)."""
    if not LOCATIONIQ_API_KEY:
        raise GeoProviderError(
            "LOCATIONIQ_API_KEY is not set. Sign up free at "
            "https://locationiq.com/register and add it to your .env file."
        )

    def _do_request():
        response = requests.get(
            LOCATIONIQ_URL,
            params={"key": LOCATIONIQ_API_KEY, "q": address, "format": "json", "limit": 1},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    results = _with_retry("Geocoding request", _do_request)

    if not results:
        raise GeoProviderError(f"Could not geocode address: {address!r}")

    result = results[0]
    return float(result["lat"]), float(result["lon"]), result.get("display_name", address)


def get_distances_to_candidates(
    origin: Tuple[float, float], destinations: List[Tuple[float, float]]
) -> List[Optional[float]]:
    """
    One OSRM Table API call covering every candidate manhole. Returns
    distance in meters per destination, in the same order as the input
    list. A destination OSRM couldn't route to is returned as None.
    """
    # OSRM coordinates are lon,lat (opposite of the lat,lng tuples used
    # everywhere else in this codebase), passed as one semicolon-separated
    # path: origin first, then every destination.
    points = [origin] + destinations
    coords_str = ";".join(f"{lon},{lat}" for lat, lon in points)

    def _do_request():
        response = requests.get(
            f"{OSRM_BASE_URL}/table/v1/driving/{coords_str}",
            params={"sources": "0", "annotations": "distance"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    data = _with_retry("Distance request", _do_request)

    if data.get("code") != "Ok":
        raise GeoProviderError(f"OSRM table error: {data.get('message', data.get('code'))}")

    distances_row = data["distances"][0]
    result: List[Optional[float]] = []
    for distance in distances_row[1:]:  # index 0 is origin-to-origin (skip it)
        result.append(float(distance) if distance is not None else None)
    return result


def get_route_polyline(
    origin: Tuple[float, float], destination: Tuple[float, float]
) -> Optional[str]:
    """
    One OSRM Route API call for just the winning candidate, to get the
    encoded polyline for drawing the route on a map. OSRM's default
    polyline encoding is the same algorithm Google uses, so the frontend's
    polyline decoder works unchanged. Returns None if no route is found.
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    coords_str = f"{lon1},{lat1};{lon2},{lat2}"

    def _do_request():
        response = requests.get(
            f"{OSRM_BASE_URL}/route/v1/driving/{coords_str}",
            params={"overview": "full", "geometries": "polyline"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    data = _with_retry("Route request", _do_request)

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    return data["routes"][0]["geometry"]
