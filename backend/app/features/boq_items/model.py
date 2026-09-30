from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class ChargeType(str, Enum):
    ONE_OFF = "one_off"  # NRC -- Non-Recurring Cost
    RECURRING = "recurring"  # ARC -- Annual/Recurring Cost


class ComputationMode(str, Enum):
    FLAT = "flat"  # amount = rate (quantity is always 1) -- rack, router, custom items
    QUANTITY = "quantity"  # amount = rate * customer-supplied quantity -- fibre (distance_m), bandwidth (bandwidth_mbps)
    FORMULA = "formula"  # amount computed via an attached CalculationFormula -- for anything needing custom math


class BOQItem(SQLModel, table=True):
    """
    Generic billable line item. The four built-ins (fibre, rack, router,
    bandwidth) are seeded once and should never be deleted (the quote
    engine looks them up by key) but CAN be freely edited by admin --
    rate, description, charge_type, computation_mode, all of it.

    Admin can also add arbitrary extra items (is_custom=True) via
    POST /admin/boq-items/ -- these are automatically included in every
    quote total alongside the built-ins.
    """

    __tablename__ = "boq_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)  # "fibre" | "rack" | "router" | "bandwidth" | "custom_<slug>"
    name: str
    description: Optional[str] = None
    rate: float
    unit: str 
    charge_type: ChargeType = Field(default=ChargeType.ONE_OFF)
    computation_mode: ComputationMode = Field(default=ComputationMode.FLAT)
    is_custom: bool = Field(default=False)  # False for the 4 built-ins, True for admin-added extras
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
