from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_admin,
    get_current_superadmin,
)
from app.features.auth.model import AdminUser
from app.features.auth.schema import AdminCreate, AdminLogin, AdminRead, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login_admin(payload: AdminLogin, session: Session = Depends(get_session)):
    admin = session.exec(
        select(AdminUser).where(AdminUser.email == payload.email)
    ).first()
    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="This admin account is inactive")

    token = create_access_token(subject=admin.email)
    return Token(access_token=token)


@router.get("/me", response_model=AdminRead)
def read_current_admin(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin


# --- Admin account management (superadmin only) ---
# There's no public/open way to create an admin account anymore. The first
# admin is created by seed.py as a superadmin; every admin after that is
# created here by an existing superadmin.

@router.get(
    "/admins",
    response_model=List[AdminRead],
    dependencies=[Depends(get_current_superadmin)],
)
def list_admins(session: Session = Depends(get_session)):
    return session.exec(select(AdminUser)).all()


@router.post(
    "/admins",
    response_model=AdminRead,
    dependencies=[Depends(get_current_superadmin)],
)
def create_admin(payload: AdminCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(AdminUser).where(AdminUser.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = AdminUser(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_superadmin=False,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


@router.patch(
    "/admins/{admin_id}/deactivate",
    response_model=AdminRead,
    dependencies=[Depends(get_current_superadmin)],
)
def deactivate_admin(admin_id: int, session: Session = Depends(get_session)):
    admin = session.get(AdminUser, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if admin.is_superadmin:
        raise HTTPException(status_code=400, detail="Cannot deactivate a superadmin")
    admin.is_active = False
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin