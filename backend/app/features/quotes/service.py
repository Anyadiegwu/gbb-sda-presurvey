from typing import Dict, List, Optional, Sequence, Tuple

from sqlmodel import Session

from app.features.boq_items.calculator import CalculationError, calculate_boq
from app.features.boq_items.model import ChargeType
from app.features.manholes import repository as manhole_repo
from app.features.manholes.model import Manhole, NodeType
from app.features.quotes.schema import (
    CalculateQuoteResponse,
    FiberLinePoint,
    LineItem,
    NearestNodesResponse,
    NodeOption,
    ResolveAddressResponse,
)
from app.features.routes import repository as route_repo
from app.integrations import geo_provider


class QuoteError(Exception):
    pass


# How many straight-line-nearest nodes get a (billable/rate-limited) road
# distance lookup. More = more accurate pick when a river/highway makes the
# closest node by air a poor one by road, but heavier routing calls.
CANDIDATE_LIMIT = 5
PER_TYPE_CANDIDATE_LIMIT = 3


def resolve_address_to_nearest_manhole(
    session: Session, address: str, node_types: Optional[Sequence[str]] = None
) -> ResolveAddressResponse:
    """Customer typed an address: geocode it, then find the nearest node."""
    lat, lng, formatted_address = geo_provider.geocode_address(address)
    return resolve_location_to_nearest_node(session, lat, lng, formatted_address, node_types)


def _rank_by_road(
    origin: Tuple[float, float], candidates: List[Manhole]
) -> List[Tuple[Manhole, float, float]]:
    """Asks the routing service for the real road distance to every
    candidate in ONE call. Returns (node, road_meters, straight_meters)
    sorted shortest road distance first; nodes with no road path are dropped."""
    distances = geo_provider.get_distances_to_candidates(
        origin, [(m.latitude, m.longitude) for m in candidates]
    )
    ranked = [
        (
            node,
            float(road),
            manhole_repo.haversine_meters(origin[0], origin[1], node.latitude, node.longitude),
        )
        for node, road in zip(candidates, distances)
        if road is not None
    ]
    ranked.sort(key=lambda item: item[1])
    return ranked


def resolve_location_to_nearest_node(
    session: Session,
    lat: float,
    lng: float,
    formatted_address: Optional[str] = None,
    node_types: Optional[Sequence[str]] = None,
) -> ResolveAddressResponse:
    """Customer location (GPS or geocoded) -> nearest node by road -> nearest
    point on the fibre backbone to that node."""
    if formatted_address is None:
        try:
            formatted_address = geo_provider.reverse_geocode(lat, lng)
        except geo_provider.GeoProviderError:
            formatted_address = f"{lat:.6f}, {lng:.6f}"  # address is cosmetic; don't fail the quote

    # --- Leg 1: customer -> nearest node (real road distance) ---
    candidates = manhole_repo.find_nearest_candidates(
        session, lat, lng, limit=CANDIDATE_LIMIT, node_types=node_types
    )
    if not candidates:
        kinds = f" of type {', '.join(node_types)}" if node_types else ""
        raise QuoteError(f"No network nodes{kinds} have been configured yet.")

    ranked = _rank_by_road((lat, lng), candidates)
    if not ranked:
        raise QuoteError("Could not find a routable road path to any network node.")

    winning_node, customer_to_node_meters, straight_line_meters = ranked[0]
    polyline = geo_provider.get_route_polyline(
        (lat, lng), (winning_node.latitude, winning_node.longitude)
    )

    # --- Leg 2: node -> nearest point on the fiber backbone line ---
    # Straight-line/geodesic distance, not road routing -- this is a short
    # physical tap/splice from the node down to the buried cable, not a
    # trip along a road.
    fiberline_route_id = None
    fiberline_route_name = None
    node_to_fiberline_meters = 0.0
    fiberline_point_lat = None
    fiberline_point_lng = None

    nearest_route = route_repo.find_nearest_route(
        session, winning_node.latitude, winning_node.longitude
    )
    if nearest_route:
        fiberline_route_id = nearest_route["route_id"]
        fiberline_route_name = nearest_route["route_name"]
        node_to_fiberline_meters = nearest_route["distance_meters"]
        fiberline_point_lat = nearest_route["point_latitude"]
        fiberline_point_lng = nearest_route["point_longitude"]
    # If no fiber route data has been imported yet, we don't hard-fail the
    # quote -- node_to_fiberline_meters just stays 0.

    return ResolveAddressResponse(
        formatted_address=formatted_address,
        customer_latitude=lat,
        customer_longitude=lng,
        manhole_id=winning_node.id,
        manhole_name=winning_node.name,
        node_type=winning_node.node_type,
        manhole_folder=winning_node.folder,
        manhole_latitude=winning_node.latitude,
        manhole_longitude=winning_node.longitude,
        customer_to_manhole_meters=customer_to_node_meters,
        straight_line_meters=straight_line_meters,
        route_polyline=polyline,
        fiberline_route_id=fiberline_route_id,
        fiberline_route_name=fiberline_route_name,
        manhole_to_fiberline_meters=node_to_fiberline_meters,
        fiberline_point_latitude=fiberline_point_lat,
        fiberline_point_longitude=fiberline_point_lng,
        total_distance_meters=customer_to_node_meters + node_to_fiberline_meters,
    )


def find_nearest_nodes_by_type(
    session: Session,
    lat: float,
    lng: float,
    node_types: Optional[Sequence[str]] = None,
) -> NearestNodesResponse:
    """The closest MH, closest FDT, closest FAT (and so on) to a point, each
    by real road distance, plus the closest spot on the fibre cable itself.
    Uses a single routing call for all candidates of all types."""
    types = list(node_types) if node_types else [t.value for t in NodeType]

    candidates: Dict[int, Manhole] = {}
    for node_type in types:
        for node in manhole_repo.find_nearest_candidates(
            session, lat, lng, limit=PER_TYPE_CANDIDATE_LIMIT, node_types=[node_type]
        ):
            candidates[node.id] = node

    best_per_type: List[NodeOption] = []
    if candidates:
        ranked = _rank_by_road((lat, lng), list(candidates.values()))
        seen = set()
        for node, road, straight in ranked:  # already shortest-first
            if node.node_type in seen:
                continue
            seen.add(node.node_type)
            best_per_type.append(
                NodeOption(
                    id=node.id,
                    name=node.name,
                    node_type=node.node_type,
                    folder=node.folder,
                    latitude=node.latitude,
                    longitude=node.longitude,
                    road_distance_meters=road,
                    straight_line_meters=straight,
                )
            )

    nearest_line = route_repo.find_nearest_route(session, lat, lng)
    return NearestNodesResponse(
        customer_latitude=lat,
        customer_longitude=lng,
        nearest_by_type=best_per_type,
        nearest_fiber_line=FiberLinePoint(**nearest_line) if nearest_line else None,
    )


def _charge_type_label(charge_type: ChargeType) -> str:
    return "One-Off" if charge_type == ChargeType.ONE_OFF else "Recurring"


def calculate_quote(
    session: Session,
    total_distance_meters: float,
    manhole_id: int,
    bandwidth_mbps: float,
    provides_own_rack: bool = False,
) -> CalculateQuoteResponse:
    manhole = session.get(Manhole, manhole_id)
    if not manhole:
        raise QuoteError("Manhole not found.")

    if bandwidth_mbps <= 0:
        raise QuoteError("bandwidthMbps must be greater than 0.")

    try:
        result = calculate_boq(
            session,
            distance_m=total_distance_meters,
            bandwidth_mbps=bandwidth_mbps,
            provides_own_rack=provides_own_rack,
        )
    except CalculationError as exc:
        raise QuoteError(str(exc)) from exc

    nrc_items = []
    arc_items = []
    for line in result.line_items:
        item = LineItem(
            description=line.description,
            qty=line.qty,
            rate=line.rate,
            amount=line.amount,
            unit=line.unit,
            type=_charge_type_label(line.charge_type),
        )
        if line.charge_type == ChargeType.ONE_OFF:
            nrc_items.append(item)
        else:
            arc_items.append(item)

    return CalculateQuoteResponse(
        manhole_id=manhole_id,
        bandwidth_mbps=bandwidth_mbps,
        total_distance_meters=total_distance_meters,
        nrc_items=nrc_items,
        arc_items=arc_items,
        total_nrc=result.total_nrc,
        total_arc=result.total_arc,
        grand_total=result.grand_total,
    )
    