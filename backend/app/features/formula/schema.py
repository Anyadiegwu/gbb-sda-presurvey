from datetime import datetime

from app.core.schema import CamelModel


class FormulaCreate(CamelModel):
    item_key: str
    name: str
    expression: str


class FormulaRead(CamelModel):
    id: int
    item_key: str
    name: str
    expression: str
    is_active: bool
    created_at: datetime


class FormulaValidateRequest(CamelModel):
    item_key: str
    expression: str
    