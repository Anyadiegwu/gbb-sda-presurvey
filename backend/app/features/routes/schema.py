from datetime import datetime
from typing import Optional

from app.core.schema import CamelModel


class FiberRouteRead(CamelModel):
    id: int
    name: str
    source_file: Optional[str] = None
    is_active: bool
    created_at: datetime


class FiberRouteImportResult(CamelModel):
    imported_count: int
    source_file: str