import math
from typing import List, Optional, Sequence

from sqlalchemy import bindparam
from sqlmodel import Session, select, text

from app.features.manholes.model import Manhole


def list_manholes(
    session: Session,
    active_only: bool = True,
    node_types: Optional[Sequence[str]] = None,
) -> List[Manhole]:
    query = select(Manhole)
    if active_only:
        query = query.where(Manhole.is_active == True)  # noqa: E712
    if node_types:
        query = query.where(Manhole.node_type.in_(list(node_types)))
    return list(session.exec(query))


def get_manhole(session: Session, manhole_id: int) -> Optional[Manhole]:
    return session.get(Manhole, manhole_id)


def create_manhole(session: Session, manhole: Manhole) -> Manhole:
    session.add(manhole)
    session.commit()
    session.refresh(manhole)
    return manhole


def delete_manhole(session: Session, manhole: Manhole) -> None:
    session.delete(manhole)
    session.commit()


def delete_by_source_file(session: Session, source_file: str, commit: bool = True) -> int:
    """Removes every node previously imported from the given file, so
    re-uploading an updated KMZ replaces the old points instead of
    duplicating them."""
    result = session.exec(
        text("DELETE FROM manholes WHERE source_file = :f"), params={"f": source_file}
    )
    if commit:
        session.commit()
    return result.rowcount


def _node_key(node_type: str, latitude: float, longitude: float) -> tuple:
    # 5 decimal places is ~1 m: two points that close, of the same type, are the same node.
    return (node_type, round(latitude, 5), round(longitude, 5))


def dedupe_nodes(session: Session, nodes, source_file: str):
    """Splits parsed nodes into (new_nodes, duplicate_count).

    The same manholes show up in several KMZs (a city's MH list is repeated in
    the metro file, the city's own file, ...). A node is a duplicate if the
    same type already exists within ~1 m, either earlier in this file or from
    any other file / manual entry. Nodes previously imported from THIS
    source_file are ignored here, since a replace-import is about to remove them.
    """
    rows = session.exec(
        text(
            "SELECT node_type, latitude, longitude FROM manholes "
            "WHERE source_file IS DISTINCT FROM :f"
        ),
        params={"f": source_file},
    ).all()
    seen = {_node_key(r.node_type, r.latitude, r.longitude) for r in rows}
    unique, duplicates = [], 0
    for node in nodes:
        key = _node_key(node.node_type, node.latitude, node.longitude)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(node)
    return unique, duplicates


def bulk_insert_nodes(session: Session, nodes, source_file: str, commit: bool = True) -> int:
    """`nodes` is a list of kml_parser.ParsedNode (already de-duplicated)."""
    for node in nodes:
        session.add(
            Manhole(
                name=node.name,
                node_type=node.node_type,
                latitude=node.latitude,
                longitude=node.longitude,
                folder=node.folder or None,
                source_file=source_file,
            )
        )
    if commit:
        session.commit()
    return len(nodes)


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters (straight line, ignores roads)."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def find_nearest_candidates(
    session: Session,
    latitude: float,
    longitude: float,
    limit: int = 5,
    node_types: Optional[Sequence[str]] = None,
) -> List[Manhole]:
    """Straight-line shortlist of the `limit` closest active nodes, nearest
    first, optionally restricted to certain node types.

    Uses PostGIS's KNN operator (<->) backed by the GiST index created in
    init_db, so it doesn't load every node into Python. The road-routing
    service is then asked for real distances on this short list only.
    """
    type_filter = "AND node_type IN :types" if node_types else ""
    statement = text(
        f"""
        SELECT id FROM manholes
        WHERE is_active = true {type_filter}
        ORDER BY ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                 <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        LIMIT :limit
        """
    )
    params = {"lon": longitude, "lat": latitude, "limit": limit}
    if node_types:
        statement = statement.bindparams(bindparam("types", expanding=True))
        params["types"] = list(node_types)

    ids = [row.id for row in session.exec(statement, params=params)]
    if not ids:
        return []
    by_id = {m.id: m for m in session.exec(select(Manhole).where(Manhole.id.in_(ids)))}
    return [by_id[i] for i in ids if i in by_id]  # keep nearest-first order
