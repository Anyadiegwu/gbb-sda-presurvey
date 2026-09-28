from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class PricingConfig(SQLModel, table=True):
    """Generic key/value store for the numeric inputs the formula uses,
    e.g. price_per_meter, installation_fee, markup_percent.
    Admin can edit these values without touching the formula itself."""

    __tablename__ = "pricing_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: float
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
