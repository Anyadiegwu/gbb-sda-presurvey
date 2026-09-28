from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class CalculationFormula(SQLModel, table=True):
    """A pricing formula attached to one BOQItem (by key), used when that
    item's computation_mode is 'formula'. Only one formula per item_key
    should be is_active=True at a time -- that's the one the quote engine
    uses. Keeping history (instead of overwriting) means admin can roll
    back a bad formula edit."""

    __tablename__ = "calculation_formulas"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_key: str = Field(index=True)  # matches BOQItem.key, e.g. "fibre" or "bandwidth"
    name: str
    expression: str  # e.g. "distance_m * rate" or "bandwidth_mbps * rate"
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    