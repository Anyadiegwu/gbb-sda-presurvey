from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.manholes import repository as manhole_repo
from app.features.manholes.model import NodeType
from app.features.network.schema import NetworkImportResult
from app.features.routes import repository as route_repo
from app.integrations.kml_parser import KmlParseError, parse_kml

router = APIRouter(prefix="/admin/network", tags=["admin: network"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.post(
    "/import",
    response_model=NetworkImportResult,
    dependencies=[Depends(get_current_admin)],
)
def import_network_file(
    file: UploadFile = File(...),
    default_node_type: NodeType = Form(NodeType.POP),
    replace: bool = Form(True),
    session: Session = Depends(get_session),
):
    """Upload a .kmz/.kml and import BOTH the fibre routes (lines) and the
    network nodes (points) in one go, in a single transaction.

    Each point's type (MH / FDT / FAT) is detected from its name or the
    folder it sits in ("FDT-014", a folder called "Manholes", ...). Points
    that don't say what they are get `default_node_type` (POP by default,
    which suits plain city/site pins). Admins can correct any individual
    node afterwards with PATCH /admin/manholes/{id}.

    With replace=true (default), everything previously imported from a file
    with the same name is replaced, so re-uploading an updated KMZ doesn't
    create duplicates.
    """
    filename = file.filename or ""
    if not filename.lower().endswith((".kmz", ".kml")):
        raise HTTPException(status_code=400, detail="File must be a .kmz or .kml file")

    file_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (25 MB limit)")

    try:
        parsed = parse_kml(file_bytes, filename, default_node_type=default_node_type.value)
    except KmlParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not parsed.routes and not parsed.nodes:
        raise HTTPException(status_code=400, detail="No routes (lines) or points found in file")

    try:
        replaced_routes = replaced_nodes = 0
        if replace:
            replaced_routes = route_repo.delete_by_source_file(session, filename, commit=False)
            replaced_nodes = manhole_repo.delete_by_source_file(session, filename, commit=False)
        route_repo.bulk_insert_routes(session, parsed.routes, source_file=filename, commit=False)
        manhole_repo.bulk_insert_nodes(session, parsed.nodes, source_file=filename, commit=False)
        session.commit()  # all-or-nothing: a failure leaves the old data untouched
    except Exception:
        session.rollback()
        raise

    by_type: dict = {}
    for node in parsed.nodes:
        by_type[node.node_type] = by_type.get(node.node_type, 0) + 1

    return NetworkImportResult(
        source_file=filename,
        routes_imported=len(parsed.routes),
        nodes_imported=len(parsed.nodes),
        nodes_by_type=by_type,
        replaced_routes=replaced_routes,
        replaced_nodes=replaced_nodes,
        skipped=parsed.skipped,
    )


@router.get("/geojson", dependencies=[Depends(get_current_admin)])
def network_geojson(
    simplify: float = 0.0001,
    node_type: Optional[NodeType] = None,
    session: Session = Depends(get_session),
):
    """Everything needed to draw the whole network on a Leaflet/Mapbox/Google
    map as one GeoJSON FeatureCollection: fibre routes as LineStrings and
    nodes as Points (properties.kind = "route" | "node", properties.nodeType).

    `simplify` is the line-simplification tolerance in degrees (0.0001 is
    roughly 11 m; 0 returns full detail). Admin-only: the backbone layout
    isn't something to publish to every visitor."""
    collection = route_repo.routes_as_geojson(session, simplify_degrees=simplify)

    nodes = manhole_repo.list_manholes(
        session, active_only=True, node_types=[node_type.value] if node_type else None
    )
    collection["features"].extend(
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [n.longitude, n.latitude]},
            "properties": {"kind": "node", "id": n.id, "name": n.name, "nodeType": n.node_type},
        }
        for n in nodes
    )
    return collection
