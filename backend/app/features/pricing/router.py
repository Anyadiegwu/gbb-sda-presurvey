from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.pricing.model import PricingConfig
from app.features.pricing.schema import (
    PricingConfigCreate,
    PricingConfigRead,
    PricingConfigUpdate,
)

router = APIRouter(prefix="/admin/pricing-config", tags=["admin: pricing config"])


@router.get("/", response_model=List[PricingConfigRead], dependencies=[Depends(get_current_admin)])
def list_pricing_config(session: Session = Depends(get_session)):
    return session.exec(select(PricingConfig)).all()


@router.post("/", response_model=PricingConfigRead, dependencies=[Depends(get_current_admin)])
def create_pricing_key(payload: PricingConfigCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(PricingConfig).where(PricingConfig.key == payload.key)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Key already exists, use PATCH to update it")
    entry = PricingConfig(**payload.model_dump())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.patch("/{key}", response_model=PricingConfigRead, dependencies=[Depends(get_current_admin)])
def update_pricing_key(key: str, payload: PricingConfigUpdate, session: Session = Depends(get_session)):
    entry = session.exec(select(PricingConfig).where(PricingConfig.key == key)).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Pricing key not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    entry.updated_at = datetime.now(timezone.utc)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{key}", dependencies=[Depends(get_current_admin)])
def delete_pricing_key(key: str, session: Session = Depends(get_session)):
    entry = session.exec(select(PricingConfig).where(PricingConfig.key == key)).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Pricing key not found")
    session.delete(entry)
    session.commit()
    return {"detail": "Pricing key deleted"}
