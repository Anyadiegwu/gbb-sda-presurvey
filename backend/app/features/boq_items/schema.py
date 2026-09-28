from datetime import datetime
from typing import Optional

from app.core.schema import CamelModel
from app.features.boq_items.model import ChargeType, ComputationMode


class BOQItemCreate(CamelModel):
    """Used for admin-added custom items. key is generated server-side
    from the name (slugified) -- admin doesn't set it directly."""

    name: str
    description: Optional[str] = None
    rate: float
    unit: str = "each"
    charge_type: ChargeType = ChargeType.ONE_OFF
    computation_mode: ComputationMode = ComputationMode.FLAT


class BOQItemUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rate: Optional[float] = None
    unit: Optional[str] = None
    charge_type: Optional[ChargeType] = None
    computation_mode: Optional[ComputationMode] = None
    is_active: Optional[bool] = None


class BOQItemRead(CamelModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    rate: float
    unit: str
    charge_type: ChargeType
    computation_mode: ComputationMode
    is_custom: bool
    is_active: bool
    created_at: datetime
    