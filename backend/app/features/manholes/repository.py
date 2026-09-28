import math
from typing import List, Optional

from sqlmodel import Session, select

from app.features.manholes.model import Manhole


def list_manholes(session: Session, active_only: bool = True) -> List[Manhole]:
    query = select(Manhole)
    if active_only:
        query = query.where(Manhole.is_active == True)  # noqa: E712
    return list(session.exec(query))


def get_manhole(session: Session, manhole_id: int) -> Optional[Manhole]:
    return session.get(Manhole, manhole_id)


def create_manhole(session: Session, manhole: Manhole) -> Manhole:
    session.add(manhole)
    session.commit()
    session.refresh(manhole)
    return manhole


def delete_manhole(session: Session, manhole: Manhole) -> None:
    session.delete(manhole)
    session.commit()


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters. Used only to shortlist candidates
    cheaply before spending a Google Maps API call on real routing distance."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def find_nearest_candidates(
    session: Session, latitude: float, longitude: float, limit: int = 5
) -> List[Manhole]:
    """Cheap straight-line shortlist. We then ask Google Maps for real
    routing distance only on this shortlist, to keep API costs down."""
    manholes = list_manholes(session, active_only=True)
    manholes.sort(
        key=lambda m: _haversine_meters(latitude, longitude, m.latitude, m.longitude)
    )
    return manholes[:limit]
