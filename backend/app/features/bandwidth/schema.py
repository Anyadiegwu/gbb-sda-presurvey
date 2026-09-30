from typing import Optional
from pydantic import BaseModel


class BandwidthTierCreate(BaseModel):
    label: str
    mbps: int
    base_price: float


class BandwidthTierUpdate(BaseModel):
    label: Optional[str] = None
    mbps: Optional[int] = None
    base_price: Optional[float] = None
    is_active: Optional[bool] = None


class BandwidthTierRead(BaseModel):
    id: int
    label: str
    mbps: int
    base_price: float
    is_active: bool

    class Config:
        from_attributes = True
