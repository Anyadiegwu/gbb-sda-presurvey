from typing import Optional

from sqlmodel import SQLModel, Field


class BandwidthTier(SQLModel, table=True):
    __tablename__ = "bandwidth_tiers"

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str  # e.g. "50 Mbps", "1 Gbps"
    mbps: int
    base_price: float  # flat equipment/tier cost the formula can reference
    is_active: bool = Field(default=True)
