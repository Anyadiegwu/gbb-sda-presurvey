from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class AdminUser(SQLModel, table=True):
    __tablename__ = "admin_users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    hashed_password: str
    is_superadmin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))