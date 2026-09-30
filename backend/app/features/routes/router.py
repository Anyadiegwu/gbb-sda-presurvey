from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.routes import repository
from app.features.routes.schema import FiberRouteImportResult, FiberRouteRead
from app.integrations.kml_parser import KmlParseError, parse_routes

router = APIRouter(prefix="/admin/fiber-routes", tags=["admin: fiber routes"])


@router.get("/", response_model=List[FiberRouteRead], dependencies=[Depends(get_current_admin)])
def list_fiber_routes(session: Session = Depends(get_session)):
    return repository.list_routes(session, active_only=False)


@router.post(
    "/import",
    response_model=FiberRouteImportResult,
    dependencies=[Depends(get_current_admin)],
)
def import_fiber_routes(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Upload a .kmz or .kml file (e.g. exported from Google Earth) and
    every LineString route inside it is imported as a FiberRoute. Point
    placemarks (cities/sites) in the file are ignored. Re-uploading the
    same file adds duplicate rows -- delete the old ones first if you're
    replacing a route set."""
    if not file.filename.lower().endswith((".kmz", ".kml")):
        raise HTTPException(status_code=400, detail="File must be a .kmz or .kml file")

    file_bytes = file.file.read()
    try:
        parsed_routes = parse_routes(file_bytes, file.filename)
    except KmlParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not parsed_routes:
        raise HTTPException(status_code=400, detail="No route (LineString) placemarks found in file")

    count = repository.bulk_insert_routes(session, parsed_routes, source_file=file.filename)
    return FiberRouteImportResult(imported_count=count, source_file=file.filename)


@router.delete("/{route_id}", dependencies=[Depends(get_current_admin)])
def delete_fiber_route(route_id: int, session: Session = Depends(get_session)):
    route = repository.get_route(session, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Fiber route not found")
    repository.delete_route(session, route)
    return {"detail": "Fiber route deleted"}