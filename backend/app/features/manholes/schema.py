from typing import Optional

from pydantic import ConfigDict, Field

from app.core.schema import CamelModel
from app.features.manholes.model import NodeType


class ManholeCreate(CamelModel):
    model_config = ConfigDict(use_enum_values=True)

    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    node_type: NodeType = NodeType.MH
    notes: Optional[str] = None


class ManholeUpdate(CamelModel):
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    node_type: Optional[NodeType] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ManholeRead(CamelModel):
    id: int
    name: str
    node_type: str
    latitude: float
    longitude: float
    notes: Optional[str] = None
    source_file: Optional[str] = None
    folder: Optional[str] = None
    is_active: bool
    