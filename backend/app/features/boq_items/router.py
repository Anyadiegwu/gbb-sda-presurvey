from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.boq_items import repository
from app.features.boq_items.model import BOQItem
from app.features.boq_items.repository import BUILT_IN_KEYS
from app.features.boq_items.schema import BOQItemCreate, BOQItemRead, BOQItemUpdate

router = APIRouter(prefix="/admin/boq-items", tags=["admin: BOQ items"])


@router.get("/", response_model=List[BOQItemRead], dependencies=[Depends(get_current_admin)])
def list_boq_items(session: Session = Depends(get_session)):
    return repository.list_items(session, active_only=False)


@router.post("/", response_model=BOQItemRead, dependencies=[Depends(get_current_admin)])
def create_boq_item(payload: BOQItemCreate, session: Session = Depends(get_session)):
    """Adds a new custom line item. It is automatically included (per its
    charge_type/computation_mode) in every quote from here on."""
    item = BOQItem(**payload.model_dump())
    return repository.create_custom_item(session, item)


@router.patch("/{item_id}", response_model=BOQItemRead, dependencies=[Depends(get_current_admin)])
def update_boq_item(item_id: int, payload: BOQItemUpdate, session: Session = Depends(get_session)):
    """Works for both built-in items (fibre/rack/router/bandwidth -- edit
    rate, description, charge_type, computation_mode freely) and custom
    ones. The item's `key` never changes."""
    item = repository.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}", dependencies=[Depends(get_current_admin)])
def delete_boq_item(item_id: int, session: Session = Depends(get_session)):
    item = repository.get_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")
    if item.key in BUILT_IN_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete the built-in '{item.key}' item -- deactivate it instead (set isActive to false).",
        )
    repository.delete_item(session, item)
    return {"detail": "BOQ item deleted"}