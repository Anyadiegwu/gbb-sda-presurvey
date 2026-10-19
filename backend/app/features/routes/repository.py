import json
from typing import List, Optional

from geoalchemy2.shape import from_shape
from shapely.geometry import LineString
from sqlmodel import Session, select, text

from app.features.routes.model import FiberRoute
from app.integrations.kml_parser import ParsedRoute


def list_routes(session: Session, active_only: bool = True) -> List[FiberRoute]:
    query = select(FiberRoute)
    if active_only:
        query = query.where(FiberRoute.is_active == True)  # noqa: E712
    return list(session.exec(query))


def get_route(session: Session, route_id: int) -> Optional[FiberRoute]:
    return session.get(FiberRoute, route_id)


def delete_route(session: Session, route: FiberRoute) -> None:
    session.delete(route)
    session.commit()


def delete_by_source_file(session: Session, source_file: str, commit: bool = True) -> int:
    """Removes every route previously imported from the given file, so
    re-uploading an updated KMZ replaces the old routes instead of
    duplicating them."""
    result = session.exec(
        text("DELETE FROM fiber_routes WHERE source_file = :f"), params={"f": source_file}
    )
    if commit:
        session.commit()
    return result.rowcount


def bulk_insert_routes(
    session: Session,
    parsed_routes: List[ParsedRoute],
    source_file: str,
    replace: bool = False,
    commit: bool = True,
) -> int:
    """Inserts every parsed route as a new FiberRoute row. With
    replace=True, routes previously imported from the same source_file are
    deleted first (in the same transaction) so a re-upload doesn't duplicate."""
    if replace:
        delete_by_source_file(session, source_file, commit=False)
    count = 0
    for route in parsed_routes:
        line = LineString(route.coordinates)  # shapely expects (lon, lat) pairs
        geom = from_shape(line, srid=4326)
        session.add(FiberRoute(name=route.name, source_file=source_file, geom=geom))
        count += 1
    if commit:
        session.commit()
    return count


def find_nearest_route(
    session: Session, latitude: float, longitude: float
) -> Optional[dict]:
    """
    Finds the fiber route line closest to the given point, the straight-line
    (geodesic) distance in meters to it, and the exact spot on the line that
    is closest (so the map can draw the connecting segment).

    Uses PostGIS's <-> KNN operator (backed by the geometry column's GiST
    index) to find the candidate, then computes the exact geography distance
    for the winner. Scales fine even with dense, many-thousand-vertex lines.
    """
    sql = text(
        """
        SELECT
            id,
            name,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) AS distance_meters,
            ST_Y(ST_ClosestPoint(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))) AS point_lat,
            ST_X(ST_ClosestPoint(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))) AS point_lon
        FROM fiber_routes
        WHERE is_active = true
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        LIMIT 1
        """
    )
    result = session.exec(sql, params={"lon": longitude, "lat": latitude}).first()
    if result is None:
        return None

    return {
        "route_id": result.id,
        "route_name": result.name,
        "distance_meters": float(result.distance_meters),
        "point_latitude": float(result.point_lat),
        "point_longitude": float(result.point_lon),
    }


def routes_as_geojson(session: Session, simplify_degrees: float = 0.0001) -> dict:
    """Active routes as a GeoJSON FeatureCollection for drawing on a map.

    Lines are simplified (0.0001 degrees is roughly 11 m) because the raw
    KMZ lines have thousands of vertices -- that's far more detail than a
    map needs and makes the payload huge. Pass 0 for the full geometry.
    """
    geometry = (
        "ST_SimplifyPreserveTopology(geom, :tol)" if simplify_degrees > 0 else "geom"
    )
    rows = session.exec(
        text(
            f"""
            SELECT id, name, source_file, ST_AsGeoJSON({geometry}) AS geojson
            FROM fiber_routes WHERE is_active = true ORDER BY id
            """
        ),
        params={"tol": simplify_degrees} if simplify_degrees > 0 else {},
    ).all()
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": json.loads(r.geojson),
                "properties": {"kind": "route", "id": r.id, "name": r.name, "sourceFile": r.source_file},
            }
            for r in rows
        ],
    }
