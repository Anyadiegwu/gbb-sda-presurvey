from pydantic import EmailStr

from app.core.schema import CamelModel


class AdminCreate(CamelModel):
    email: EmailStr
    full_name: str
    password: str


class AdminLogin(CamelModel):
    email: EmailStr
    password: str


class Token(CamelModel):
    access_token: str
    token_type: str = "bearer"


class AdminRead(CamelModel):
    id: int
    email: EmailStr
    full_name: str
    is_superadmin: bool
    is_active: bool