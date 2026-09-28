from typing import Optional

from app.core.schema import CamelModel


class ManholeCreate(CamelModel):
    name: str
    latitude: float
    longitude: float
    notes: Optional[str] = None


class ManholeUpdate(CamelModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ManholeRead(CamelModel):
    id: int
    name: str
    latitude: float
    longitude: float
    notes: Optional[str] = None
    is_active: bool
    