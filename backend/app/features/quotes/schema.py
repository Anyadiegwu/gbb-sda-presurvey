from typing import List, Optional

from pydantic import ConfigDict, Field

from app.core.schema import CamelModel
from app.features.manholes.model import NodeType


class ResolveAddressRequest(CamelModel):
    model_config = ConfigDict(use_enum_values=True)

    address: str
    # Restrict the search to certain node types, e.g. ["FDT", "FAT"].
    # Omit/null to search every type.
    node_types: Optional[List[NodeType]] = None


class ResolveLocationRequest(CamelModel):
    """Customer's location as GPS coordinates (browser geolocation or a map pin)."""

    model_config = ConfigDict(use_enum_values=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    node_types: Optional[List[NodeType]] = None


class NearestNodesRequest(ResolveLocationRequest):
    pass


class NodeOption(CamelModel):
    """One network node with its distance from the customer."""

    id: int
    name: str
    node_type: str
    folder: Optional[str] = None  # e.g. "Metro MH > Kano > BUK.kml" (node names like MH01 repeat)
    latitude: float
    longitude: float
    road_distance_meters: float
    straight_line_meters: float


class FiberLinePoint(CamelModel):
    route_id: int
    route_name: str
    distance_meters: float  # straight line from the query point to the cable
    point_latitude: float  # the exact spot on the cable that is closest
    point_longitude: float


class NearestNodesResponse(CamelModel):
    customer_latitude: float
    customer_longitude: float
    # Best node of each requested type (nearest by road), nearest first.
    nearest_by_type: List[NodeOption]
    nearest_fiber_line: Optional[FiberLinePoint] = None


class ResolveAddressResponse(CamelModel):
    formatted_address: str
    customer_latitude: float
    customer_longitude: float

    manhole_id: int
    manhole_name: str
    node_type: str = "MH"
    manhole_folder: Optional[str] = None  # where the node sits in the survey data, to tell apart repeated names like "MH01"
    manhole_latitude: float
    manhole_longitude: float
    customer_to_manhole_meters: float  # road-routed distance (OSRM)
    straight_line_meters: float = 0.0  # as-the-crow-flies customer -> node, for comparison
    route_polyline: Optional[str] = None  # customer -> node road path (encoded polyline, precision 5)

    fiberline_route_id: Optional[int] = None
    fiberline_route_name: Optional[str] = None
    manhole_to_fiberline_meters: float = 0.0  # straight-line tap distance
    fiberline_point_latitude: Optional[float] = None  # closest spot on the cable to the node
    fiberline_point_longitude: Optional[float] = None

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
    