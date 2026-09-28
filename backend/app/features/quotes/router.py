from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.features.quotes.schema import (
    CalculateQuoteRequest,
    CalculateQuoteResponse,
    ResolveAddressRequest,
    ResolveAddressResponse,
)
from app.features.quotes.service import QuoteError, calculate_quote, resolve_address_to_nearest_manhole
from app.integrations.geo_provider import GeoProviderError

router = APIRouter(prefix="/quotes", tags=["public: quotes"])


@router.post("/resolve-address", response_model=ResolveAddressResponse)
def resolve_address(payload: ResolveAddressRequest, session: Session = Depends(get_session)):
    """Step 1: customer submits an address -> we geocode it, find the
    nearest manhole, and return the real routing distance + polyline."""
    try:
        return resolve_address_to_nearest_manhole(session, payload.address)
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
    