from typing import Optional
from pydantic import BaseModel


class PricingConfigCreate(BaseModel):
    key: str
    value: float
    description: Optional[str] = None


class PricingConfigUpdate(BaseModel):
    value: Optional[float] = None
    description: Optional[str] = None


class PricingConfigRead(BaseModel):
    id: int
    key: str
    value: float
    description: Optional[str] = None

    class Config:
        from_attributes = True
