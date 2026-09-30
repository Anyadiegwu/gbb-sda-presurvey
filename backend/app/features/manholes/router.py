from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.manholes import repository
from app.features.manholes.model import Manhole
from app.features.manholes.schema import ManholeCreate, ManholeRead, ManholeUpdate

router = APIRouter(prefix="/admin/manholes", tags=["admin: manholes"])


@router.get("/", response_model=List[ManholeRead], dependencies=[Depends(get_current_admin)])
def list_manholes(session: Session = Depends(get_session)):
    return repository.list_manholes(session, active_only=False)


@router.post("/", response_model=ManholeRead, dependencies=[Depends(get_current_admin)])
def create_manhole(payload: ManholeCreate, session: Session = Depends(get_session)):
    manhole = Manhole(**payload.model_dump())
    return repository.create_manhole(session, manhole)


@router.patch("/{manhole_id}", response_model=ManholeRead, dependencies=[Depends(get_current_admin)])
def update_manhole(manhole_id: int, payload: ManholeUpdate, session: Session = Depends(get_session)):
    manhole = repository.get_manhole(session, manhole_id)
    if not manhole:
        raise HTTPException(status_code=404, detail="Manhole not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(manhole, field, value)
    session.add(manhole)
    session.commit()
    session.refresh(manhole)
    return manhole


@router.delete("/{manhole_id}", dependencies=[Depends(get_current_admin)])
def delete_manhole(manhole_id: int, session: Session = Depends(get_session)):
    manhole = repository.get_manhole(session, manhole_id)
    if not manhole:
        raise HTTPException(status_code=404, detail="Manhole not found")
    repository.delete_manhole(session, manhole)
    return {"detail": "Manhole deleted"}
