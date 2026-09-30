from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, Column, JSON


class BOQSubmission(SQLModel, table=True):
    __tablename__ = "boq_submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    reference: Optional[str] = Field(default=None, index=True, unique=True)  # e.g. "GBB-2026-000123", set after insert

    # Contact form fields
    full_name: str
    company: Optional[str] = None
    email: str
    phone: str
    site_address: str
    notes: Optional[str] = None

    # Quote snapshot (from the /quotes flow) so historical BOQs stay
    # accurate even if pricing/formula changes later
    manhole_id: int
    customer_to_manhole_meters: float
    fiberline_route_id: Optional[int] = None
    manhole_to_fiberline_meters: float = 0.0
    total_distance_meters: float
    route_polyline: Optional[str] = None

    bandwidth_mbps: float
    provides_own_rack: bool = Field(default=False)

    nrc_items: list = Field(default_factory=list, sa_column=Column(JSON))
    arc_items: list = Field(default_factory=list, sa_column=Column(JSON))
    total_nrc: float
    total_arc: float
    grand_total: float

    status: str = Field(default="new")  # new | reviewed | quoted | closed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    