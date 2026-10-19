from typing import Dict, List

from app.core.schema import CamelModel


class NetworkImportResult(CamelModel):
    source_file: str
    routes_imported: int
    nodes_imported: int
    nodes_by_type: Dict[str, int]
    replaced_routes: int
    replaced_nodes: int
    skipped: List[str]
