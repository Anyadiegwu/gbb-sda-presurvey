"""
Shared Pydantic base for every public-facing request/response schema.

The frontend (agreed design) uses camelCase field names throughout
(e.g. totalDistanceMeters, providesOwnRack). Python/FastAPI convention is
snake_case. CamelModel bridges the two: internal code stays snake_case,
JSON in/out is camelCase automatically.

populate_by_name=True means incoming request bodies accept EITHER
camelCase (the alias) or snake_case (the python field name) -- handy for
testing with curl/Swagger, and harmless for the real frontend which will
only ever send camelCase.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )