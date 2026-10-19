from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class NodeType(str, Enum):
    """What kind of physical network point this is.

    MH  - manhole / handhole
    FDT - fibre distribution terminal
    FAT - fibre access terminal
    POP - point of presence / city site / landing point
    """

    MH = "MH"
    FDT = "FDT"
    FAT = "FAT"
    POP = "POP"


class Manhole(SQLModel, table=True):
    """A network access point a customer can be connected to.

    The table/class keep the name `Manhole` so existing quotes/submissions
    (which store manhole_id) keep working, but rows now carry a node_type, so
    FDTs, FATs and POPs live in the same table and are searched the same way.
    """

    __tablename__ = "manholes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    node_type: str = Field(default=NodeType.MH.value, index=True)
    latitude: float
    longitude: float
    notes: Optional[str] = None
    source_file: Optional[str] = Field(default=None, index=True)  # set when imported from a KMZ/KML
    folder: Optional[str] = None  # where it sat in the KMZ, e.g. "Metro MH > Kano > BUK.kml" (names like MH01 repeat everywhere)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    