from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.bandwidth.model import BandwidthTier
from app.features.bandwidth.schema import (
    BandwidthTierCreate,
    BandwidthTierRead,
    BandwidthTierUpdate,
)

router = APIRouter(prefix="/admin/bandwidth-tiers", tags=["admin: bandwidth tiers"])
public_router = APIRouter(prefix="/bandwidth-tiers", tags=["public: bandwidth tiers"])


@public_router.get("/", response_model=List[BandwidthTierRead])
def list_active_tiers(session: Session = Depends(get_session)):
    """Public endpoint so the customer-facing form can populate the bandwidth dropdown."""
    return session.exec(
        select(BandwidthTier).where(BandwidthTier.is_active == True)  # noqa: E712
    ).all()


@router.get("/", response_model=List[BandwidthTierRead], dependencies=[Depends(get_current_admin)])
def list_all_tiers(session: Session = Depends(get_session)):
    return session.exec(select(BandwidthTier)).all()


@router.post("/", response_model=BandwidthTierRead, dependencies=[Depends(get_current_admin)])
def create_tier(payload: BandwidthTierCreate, session: Session = Depends(get_session)):
    tier = BandwidthTier(**payload.model_dump())
    session.add(tier)
    session.commit()
    session.refresh(tier)
    return tier


@router.patch("/{tier_id}", response_model=BandwidthTierRead, dependencies=[Depends(get_current_admin)])
def update_tier(tier_id: int, payload: BandwidthTierUpdate, session: Session = Depends(get_session)):
    tier = session.get(BandwidthTier, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Bandwidth tier not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tier, field, value)
    session.add(tier)
    session.commit()
    session.refresh(tier)
    return tier


@router.delete("/{tier_id}", dependencies=[Depends(get_current_admin)])
def delete_tier(tier_id: int, session: Session = Depends(get_session)):
    tier = session.get(BandwidthTier, tier_id)
    if not tier:
        raise HTTPException(status_code=404, detail="Bandwidth tier not found")
    session.delete(tier)
    session.commit()
    return {"detail": "Bandwidth tier deleted"}
