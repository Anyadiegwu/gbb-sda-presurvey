"""
Turns the set of active BOQItems into a priced NRC/ARC breakdown, given
the customer's distance, requested bandwidth, and rack preference.

This is the one place item pricing actually happens -- used by
/quotes/calculate. Every active item (built-in or admin-added custom) is
included automatically, except "rack" when the customer says they'll
provide their own.
"""

from dataclasses import dataclass
from typing import List, Optional

from sqlmodel import Session, select

from app.features.boq_items.model import BOQItem, ChargeType, ComputationMode
from app.features.formula.engine import DEFAULT_EXPRESSION, FormulaError, evaluate
from app.features.formula.model import CalculationFormula


class CalculationError(Exception):
    pass


@dataclass
class ComputedLineItem:
    description: str
    qty: float
    rate: float
    amount: float
    unit: str
    charge_type: ChargeType  # caller formats this to "One-Off"/"Recurring" for the API response


@dataclass
class BOQCalculationResult:
    line_items: List[ComputedLineItem]
    total_nrc: float
    total_arc: float
    grand_total: float


def _resolve_quantity(item: BOQItem, distance_m: float, bandwidth_mbps: float) -> float:
    if item.key == "fibre":
        return distance_m
    if item.key == "bandwidth":
        return bandwidth_mbps
    return 1.0


def _get_active_formula(session: Session, item_key: str) -> str:
    formula = session.exec(
        select(CalculationFormula).where(
            CalculationFormula.item_key == item_key,
            CalculationFormula.is_active == True,  # noqa: E712
        )
    ).first()
    return formula.expression if formula else DEFAULT_EXPRESSION


def _compute_item_amount(session: Session, item: BOQItem, quantity: float) -> float:
    if item.computation_mode == ComputationMode.FLAT:
        return item.rate
    if item.computation_mode == ComputationMode.QUANTITY:
        return item.rate * quantity
    if item.computation_mode == ComputationMode.FORMULA:
        expression = _get_active_formula(session, item.key)
        try:
            return evaluate(item.key, expression, rate=item.rate, quantity=quantity)
        except FormulaError as exc:
            raise CalculationError(f"Pricing formula error for '{item.key}': {exc}") from exc
    raise CalculationError(f"Unknown computation_mode on item '{item.key}'")


def calculate_boq(
    session: Session,
    distance_m: float,
    bandwidth_mbps: float,
    provides_own_rack: bool = False,
) -> BOQCalculationResult:
    items = session.exec(
        select(BOQItem).where(BOQItem.is_active == True)  # noqa: E712
    ).all()

    line_items: List[ComputedLineItem] = []
    total_nrc = 0.0
    total_arc = 0.0

    for item in items:
        if item.key == "rack" and provides_own_rack:
            continue  # customer is providing their own rack -- skip this item entirely

        quantity = _resolve_quantity(item, distance_m, bandwidth_mbps)
        amount = _compute_item_amount(session, item, quantity)

        line_items.append(
            ComputedLineItem(
                description=item.name,
                qty=quantity,
                rate=item.rate,
                amount=round(amount, 2),
                unit=item.unit,
                charge_type=item.charge_type,
            )
        )

        if item.charge_type == ChargeType.ONE_OFF:
            total_nrc += amount
        else:
            total_arc += amount

    return BOQCalculationResult(
        line_items=line_items,
        total_nrc=round(total_nrc, 2),
        total_arc=round(total_arc, 2),
        grand_total=round(total_nrc + total_arc, 2),
    )