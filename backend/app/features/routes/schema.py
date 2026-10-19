from datetime import datetime
from typing import Dict, List, Optional

from app.core.schema import CamelModel


class FiberRouteRead(CamelModel):
    id: int
    name: str
    source_file: Optional[str] = None
    is_active: bool
    created_at: datetime


class FiberRouteImportResult(CamelModel):
    # Original fields (unchanged meaning): number of cable routes imported.
    imported_count: int
    source_file: str
    # Added: points (POP / MH / FDT / FAT) imported from the same file.
    nodes_imported: int = 0
    nodes_by_type: Dict[str, int] = {}
    replaced_routes: int = 0
    replaced_nodes: int = 0
    # What was deliberately NOT imported, so the admin can see why numbers differ
    # from what's in the file:
    duplicates_skipped: int = 0  # same node already imported from another file
    points_skipped: Dict[str, int] = {}  # POLE / SPLICE / UNCLASSIFIED (customer sites) -> count
    survey_routes_skipped: int = 0  # hand-drawn customer pre-survey routes
    skipped: List[str] = []  # placemarks with unusable coordinates
    dry_run: bool = False  # true = nothing was saved, this is a preview
    folders: List[dict] = []  # per-folder breakdown: what each KMZ folder was treated as
    