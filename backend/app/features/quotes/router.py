from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.features.quotes.schema import (
    CalculateQuoteRequest,
    CalculateQuoteResponse,
    NearestNodesRequest,
    NearestNodesResponse,
    ResolveAddressRequest,
    ResolveAddressResponse,
    ResolveLocationRequest,
)
from app.features.quotes.service import (
    QuoteError,
    calculate_quote,
    find_nearest_nodes_by_type,
    resolve_address_to_nearest_manhole,
    resolve_location_to_nearest_node,
)
from app.integrations.geo_provider import GeoProviderError

router = APIRouter(prefix="/quotes", tags=["public: quotes"])


@router.post("/resolve-address", response_model=ResolveAddressResponse)
def resolve_address(payload: ResolveAddressRequest, session: Session = Depends(get_session)):
    """Step 1: customer submits an address -> we geocode it, find the
    nearest manhole, and return the real routing distance + polyline."""
    try:
        return resolve_address_to_nearest_manhole(session, payload.address, payload.node_types)
    except GeoProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except QuoteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/resolve-location", response_model=ResolveAddressResponse)
def resolve_location(payload: ResolveLocationRequest, session: Session = Depends(get_session)):
    """Step 1 (GPS version): customer shares their location (browser
    geolocation or a pin dropped on the map) -> nearest node by road, the
    road polyline to it, and the closest spot on the fibre backbone."""
    try:
        return resolve_location_to_nearest_node(
            session, payload.latitude, payload.longitude, node_types=payload.node_types
        )
    except GeoProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except QuoteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/nearest-nodes", response_model=NearestNodesResponse)
def nearest_nodes(payload: NearestNodesRequest, session: Session = Depends(get_session)):
    """The closest MH, FDT, FAT and POP to a point (by road distance), plus
    the closest spot on the fibre cable itself. Use this to show "your
    nearest FDT is 450 m away" before the customer commits to a quote."""
    try:
        return find_nearest_nodes_by_type(
            session, payload.latitude, payload.longitude, payload.node_types
        )
    except GeoProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except QuoteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/calculate", response_model=CalculateQuoteResponse)
def calculate(payload: CalculateQuoteRequest, session: Session = Depends(get_session)):
    """Step 2: customer picks a bandwidth (Mbps) and whether they'll
    provide their own rack -> we price every active BOQ item against the
    combined distance from step 1 and return the NRC/ARC breakdown."""
    try:
        return calculate_quote(
            session,
            total_distance_meters=payload.total_distance_meters,
            manhole_id=payload.manhole_id,
            bandwidth_mbps=payload.bandwidth_mbps,
            provides_own_rack=payload.provides_own_rack,
        )
    except QuoteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    