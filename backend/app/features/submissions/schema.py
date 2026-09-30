from datetime import datetime
from typing import List, Optional

from pydantic import EmailStr, Field

from app.core.schema import CamelModel
from app.features.quotes.schema import LineItem


class SubmissionCreate(CamelModel):
    # Contact fields
    full_name: str
    company: Optional[str] = None
    email: EmailStr
    phone: str
    site_address: str
    notes: Optional[str] = None

    # Echoed back from the /quotes flow (resolve-address + calculate)
    manhole_id: int
    customer_to_manhole_meters: float
    fiberline_route_id: Optional[int] = None
    manhole_to_fiberline_meters: float = 0.0
    total_distance_meters: float
    route_polyline: Optional[str] = None

    bandwidth_mbps: float
    provides_own_rack: bool = False

    nrc_items: List[LineItem]
    arc_items: List[LineItem]
    total_nrc: float = Field(alias="totalNRC")
    total_arc: float = Field(alias="totalARC")
    grand_total: float


class SubmissionRead(CamelModel):
    id: int
    reference: Optional[str] = None
    full_name: str
    company: Optional[str] = None
    email: str
    phone: str
    site_address: str
    notes: Optional[str] = None

    manhole_id: int
    customer_to_manhole_meters: float
    fiberline_route_id: Optional[int] = None
    manhole_to_fiberline_meters: float
    total_distance_meters: float
    route_polyline: Optional[str] = None

    bandwidth_mbps: float
    provides_own_rack: bool

    nrc_items: List[LineItem]
    arc_items: List[LineItem]
    total_nrc: float = Field(alias="totalNRC")
    total_arc: float = Field(alias="totalARC")
    grand_total: float

    status: str
    created_at: datetime


class SubmissionStatusUpdate(CamelModel):
    status: str
    