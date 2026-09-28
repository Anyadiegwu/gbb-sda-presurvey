from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class Manhole(SQLModel, table=True):
    __tablename__ = "manholes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    latitude: float
    longitude: float
    notes: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
