from typing import List, Optional

from pydantic import Field

from app.core.schema import CamelModel


class ResolveAddressRequest(CamelModel):
    address: str


class ResolveAddressResponse(CamelModel):
    formatted_address: str
    customer_latitude: float
    customer_longitude: float

    manhole_id: int
    manhole_name: str
    manhole_latitude: float
    manhole_longitude: float
    customer_to_manhole_meters: float  # road-routed distance (Google Directions)
    route_polyline: Optional[str] = None  # customer -> manhole road path

    fiberline_route_id: Optional[int] = None
    fiberline_route_name: Optional[str] = None
    manhole_to_fiberline_meters: float = 0.0  # straight-line tap distance

    total_distance_meters: float  # customer_to_manhole + manhole_to_fiberline -- feed this into /quotes/calculate


class CalculateQuoteRequest(CamelModel):
    total_distance_meters: float
    manhole_id: int
    bandwidth_mbps: float
    provides_own_rack: bool = False


class LineItem(CamelModel):
    description: str
    qty: float
    rate: float
    amount: float
    unit: str
    type: str  # "One-Off" or "Recurring" -- matches the frontend's row.type exactly


class CalculateQuoteResponse(CamelModel):
    manhole_id: int
    bandwidth_mbps: float
    total_distance_meters: float
    nrc_items: List[LineItem]
    arc_items: List[LineItem]
    # to_camel() would turn total_nrc/total_arc into totalNrc/totalArc --
    # explicit aliases here keep the acronym capitalization the frontend expects.
    total_nrc: float = Field(alias="totalNRC")
    total_arc: float = Field(alias="totalARC")
    grand_total: float
    