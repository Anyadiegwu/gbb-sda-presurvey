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


def bulk_insert_routes(
    session: Session, parsed_routes: List[ParsedRoute], source_file: str
) -> int:
    """Inserts every parsed route as a new FiberRoute row. Does not
    dedupe/replace by name — call this once per KMZ file; if you need to
    re-import the same file, delete the old rows for that source_file first."""
    count = 0
    for route in parsed_routes:
        line = LineString(route.coordinates)  # shapely expects (lon, lat) pairs
        geom = from_shape(line, srid=4326)
        session.add(FiberRoute(name=route.name, source_file=source_file, geom=geom))
        count += 1
    session.commit()
    return count


def find_nearest_route(
    session: Session, latitude: float, longitude: float
) -> Optional[dict]:
    """
    Finds the fiber route line closest to the given point, and the
    straight-line (geodesic) distance in meters to the nearest point on
    that line.

    Uses PostGIS's <-> KNN operator (backed by the geometry column's GiST
    index) to cheaply find candidate routes, then computes the exact
    geography distance for the winner. This scales fine even with dense,
    many-thousand-vertex route lines.
    """
    sql = text(
        """
        SELECT
            id,
            name,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) AS distance_meters
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
    }