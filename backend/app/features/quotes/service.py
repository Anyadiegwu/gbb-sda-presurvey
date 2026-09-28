from sqlmodel import Session

from app.features.boq_items.calculator import CalculationError, calculate_boq
from app.features.boq_items.model import ChargeType
from app.features.manholes import repository as manhole_repo
from app.features.manholes.model import Manhole
from app.features.quotes.schema import (
    CalculateQuoteResponse,
    LineItem,
    ResolveAddressResponse,
)
from app.features.routes import repository as route_repo
from app.integrations import geo_provider


class QuoteError(Exception):
    pass


def resolve_address_to_nearest_manhole(
    session: Session, address: str
) -> ResolveAddressResponse:
    lat, lng, formatted_address = geo_provider.geocode_address(address)

    # --- Leg 1: customer -> nearest manhole (real road distance) ---
    candidates = manhole_repo.find_nearest_candidates(session, lat, lng, limit=5)
    if not candidates:
        raise QuoteError("No manhole locations have been configured yet.")

    destinations = [(m.latitude, m.longitude) for m in candidates]
    distances = geo_provider.get_distances_to_candidates((lat, lng), destinations)

    best_index = None
    best_distance = None
    for index, distance in enumerate(distances):
        if distance is None:
            continue
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_index = index

    if best_index is None:
        raise QuoteError("Could not find a routable path to any manhole location.")

    winning_manhole = candidates[best_index]
    customer_to_manhole_meters = best_distance
    polyline = geo_provider.get_route_polyline(
        (lat, lng), (winning_manhole.latitude, winning_manhole.longitude)
    )

    # --- Leg 2: manhole -> nearest point on the fiber backbone line ---
    # Straight-line/geodesic distance, not road routing -- this is a short
    # physical tap/splice from the manhole down to the buried cable, not a
    # trip along a road.
    fiberline_route_id = None
    fiberline_route_name = None
    manhole_to_fiberline_meters = 0.0

    nearest_route = route_repo.find_nearest_route(
        session, winning_manhole.latitude, winning_manhole.longitude
    )
    if nearest_route:
        fiberline_route_id = nearest_route["route_id"]
        fiberline_route_name = nearest_route["route_name"]
        manhole_to_fiberline_meters = nearest_route["distance_meters"]
    # If no fiber route data has been imported yet, we don't hard-fail the
    # quote -- manhole_to_fiberline_meters just stays 0.

    total_distance_meters = customer_to_manhole_meters + manhole_to_fiberline_meters

    return ResolveAddressResponse(
        formatted_address=formatted_address,
        customer_latitude=lat,
        customer_longitude=lng,
        manhole_id=winning_manhole.id,
        manhole_name=winning_manhole.name,
        manhole_latitude=winning_manhole.latitude,
        manhole_longitude=winning_manhole.longitude,
        customer_to_manhole_meters=customer_to_manhole_meters,
        route_polyline=polyline,
        fiberline_route_id=fiberline_route_id,
        fiberline_route_name=fiberline_route_name,
        manhole_to_fiberline_meters=manhole_to_fiberline_meters,
        total_distance_meters=total_distance_meters,
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
