from datetime import datetime, timezone
from typing import Any, Optional

from geoalchemy2 import Geometry
from sqlalchemy import Column
from sqlmodel import SQLModel, Field


class FiberRoute(SQLModel, table=True):
    """A single backbone fiber cable path, imported from a KMZ/KML file.
    geom is a WGS84 LineString (the actual cable route, following its
    real-world path — often hundreds of vertices, not a straight line)."""

    __tablename__ = "fiber_routes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # e.g. "S1 Abuja - Madalla -44.186KM", taken from the KML placemark name
    source_file: Optional[str] = None  # e.g. "Backbone_Phase_2.kmz", for traceability
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    geom: Any = Field(
        sa_column=Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    )