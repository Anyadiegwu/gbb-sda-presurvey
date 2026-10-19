from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.manholes import repository as manhole_repo
from app.features.manholes.model import NodeType
from app.features.routes import repository
from app.features.routes.schema import FiberRouteImportResult, FiberRouteRead
from app.integrations.kml_parser import KmlParseError, parse_kml

router = APIRouter(prefix="/admin/fiber-routes", tags=["admin: fiber routes"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.get("/", response_model=List[FiberRouteRead], dependencies=[Depends(get_current_admin)])
def list_fiber_routes(session: Session = Depends(get_session)):
    return repository.list_routes(session, active_only=False)


@router.get("/geojson", dependencies=[Depends(get_current_admin)])
def network_geojson(
    simplify: float = 0.0001,
    node_type: Optional[NodeType] = None,
    session: Session = Depends(get_session),
):
    """Everything needed to draw the whole network on a map, as one GeoJSON
    FeatureCollection: fibre routes as LineStrings and nodes as Points
    (properties.kind = "route" | "node", properties.nodeType).

    `simplify` is the line-simplification tolerance in degrees (0.0001 is
    roughly 11 m; 0 returns full detail)."""
    collection = repository.routes_as_geojson(session, simplify_degrees=simplify)
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


@router.post(
    "/import",
    response_model=FiberRouteImportResult,
    dependencies=[Depends(get_current_admin)],
)
def import_fiber_routes(
    file: UploadFile = File(...),
    replace: bool = True,
    dry_run: bool = False,
    default_node_type: Optional[NodeType] = None,
    session: Session = Depends(get_session),
):
    """Upload a .kmz or .kml file (e.g. exported from Google Earth).

    Real KMZs mix network points, poles, splice points, customer sites and
    hand-drawn pre-survey routes in one file, so each placemark is classified:

    - Points named/filed as manholes or handholes (MH, HH), FDT, FAT, or POP /
      site pins are imported as network nodes (`nodeType`).
    - Poles, splice points and unrecognised points (customer sites from earlier
      pre-surveys) are NOT imported, and counted in `pointsSkipped`.
    - Lines are imported as fibre routes, except hand-drawn customer pre-survey
      routes (`surveyRoutesSkipped`).
    - Nodes already imported from another file (same type, within ~1 m) are
      skipped as duplicates (`duplicatesSkipped`).

    `folders` shows what every KMZ folder was treated as. Pass `dry_run=true`
    to see all of this without saving anything. `default_node_type` imports
    unrecognised points as that type instead of skipping them.

    With replace=true (default), anything previously imported from a file with
    the same name is replaced instead of duplicated. The import is one
    transaction: a failure leaves the existing data untouched.
    """
    filename = file.filename or ""
    if not filename.lower().endswith((".kmz", ".kml")):
        raise HTTPException(status_code=400, detail="File must be a .kmz or .kml file")

    file_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (25 MB limit)")

    try:
        parsed = parse_kml(
            file_bytes, filename,
            default_node_type=default_node_type.value if default_node_type else None,
        )
    except KmlParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    unique_nodes, duplicates = manhole_repo.dedupe_nodes(session, parsed.nodes, filename)

    if not parsed.routes and not unique_nodes and not duplicates:
        detail = "Nothing importable found in this file."
        extras = []
        if parsed.skipped_survey_routes:
            extras.append(f"{parsed.skipped_survey_routes} pre-survey routes")
        if parsed.skipped_points:
            extras.append(", ".join(f"{n} {k.lower()} points" for k, n in parsed.skipped_points.items()))
        if extras:
            detail += " Skipped: " + "; ".join(extras) + "."
        else:
            detail += " (Only lines and points are imported; shapes/polygons are ignored.)"
        raise HTTPException(status_code=400, detail=detail)

    replaced_routes = replaced_nodes = 0
    if not dry_run:
        try:
            if replace:
                replaced_routes = repository.delete_by_source_file(session, filename, commit=False)
                replaced_nodes = manhole_repo.delete_by_source_file(session, filename, commit=False)
            repository.bulk_insert_routes(session, parsed.routes, source_file=filename, commit=False)
            manhole_repo.bulk_insert_nodes(session, unique_nodes, source_file=filename, commit=False)
            session.commit()
        except Exception:
            session.rollback()
            raise

    by_type: dict = {}
    for node in unique_nodes:
        by_type[node.node_type] = by_type.get(node.node_type, 0) + 1

    return FiberRouteImportResult(
        imported_count=len(parsed.routes),
        source_file=filename,
        nodes_imported=len(unique_nodes),
        nodes_by_type=by_type,
        replaced_routes=replaced_routes,
        replaced_nodes=replaced_nodes,
        duplicates_skipped=duplicates,
        points_skipped=parsed.skipped_points,
        survey_routes_skipped=parsed.skipped_survey_routes,
        skipped=parsed.skipped,
        dry_run=dry_run,
        folders=parsed.folders,
    )


@router.delete("/{route_id}", dependencies=[Depends(get_current_admin)])
def delete_fiber_route(route_id: int, session: Session = Depends(get_session)):
    route = repository.get_route(session, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Fiber route not found")
    repository.delete_route(session, route)
    return {"detail": "Fiber route deleted"}
    