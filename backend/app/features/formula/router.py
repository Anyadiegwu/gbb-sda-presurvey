from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.boq_items import repository as item_repo
from app.features.formula.engine import FormulaError, validate_expression
from app.features.formula.model import CalculationFormula
from app.features.formula.schema import (
    FormulaCreate,
    FormulaRead,
    FormulaValidateRequest,
)

router = APIRouter(prefix="/admin/formulas", tags=["admin: calculation formulas"])


def _ensure_item_exists(session: Session, item_key: str) -> None:
    if item_repo.get_item_by_key(session, item_key) is None:
        raise HTTPException(status_code=404, detail=f"No BOQ item with key '{item_key}' exists")


@router.get("/", response_model=List[FormulaRead], dependencies=[Depends(get_current_admin)])
def list_formulas(item_key: str = None, session: Session = Depends(get_session)):
    """Optionally filter with ?itemKey=fibre (or bandwidth, etc.)."""
    query = select(CalculationFormula)
    if item_key:
        query = query.where(CalculationFormula.item_key == item_key)
    return session.exec(query).all()


@router.post("/validate", dependencies=[Depends(get_current_admin)])
def validate_formula(payload: FormulaValidateRequest, session: Session = Depends(get_session)):
    _ensure_item_exists(session, payload.item_key)
    try:
        validate_expression(payload.item_key, payload.expression)
    except FormulaError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"valid": True}


@router.post("/", response_model=FormulaRead, dependencies=[Depends(get_current_admin)])
def create_formula(payload: FormulaCreate, session: Session = Depends(get_session)):
    _ensure_item_exists(session, payload.item_key)
    try:
        validate_expression(payload.item_key, payload.expression)
    except FormulaError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    formula = CalculationFormula(
        item_key=payload.item_key, name=payload.name, expression=payload.expression
    )
    session.add(formula)
    session.commit()
    session.refresh(formula)
    return formula


@router.post("/{formula_id}/activate", response_model=FormulaRead, dependencies=[Depends(get_current_admin)])
def activate_formula(formula_id: int, session: Session = Depends(get_session)):
    """Deactivates every other formula for the SAME item_key and activates
    this one. Only one active formula per item at a time. Note: this does
    not change that item's computation_mode -- set it to 'formula' via
    PATCH /admin/boq-items/{id} for this to actually take effect."""
    formula = session.get(CalculationFormula, formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")

    siblings = session.exec(
        select(CalculationFormula).where(CalculationFormula.item_key == formula.item_key)
    ).all()
    for f in siblings:
        f.is_active = f.id == formula_id
        session.add(f)
    session.commit()
    session.refresh(formula)
    return formula
