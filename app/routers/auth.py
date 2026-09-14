from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado",
        )

    if data.role not in [
        "student",
        "tutor",
        "admin",
    ]:
        raise HTTPException(
            status_code=400,
            detail="Rol inválido",
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(
            data.password,
        ),
        role=data.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Usuario inactivo",
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }
