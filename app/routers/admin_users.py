
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserResponse,
    AdminUserStatusResponse,
    AdminUserStatusUpdate,
)


router = APIRouter(
    prefix="/admin/users",
    tags=["Admin - Users"],
)


def serialize_admin_user(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        grade=(
            user.student_profile.grade
            if user.student_profile is not None
            else None
        ),
        tutor_id=(
            user.tutor.id
            if user.tutor is not None
            else None
        ),
        tutor_is_active=(
            user.tutor.is_active
            if user.tutor is not None
            else None
        ),
    )


@router.get(
    "",
    response_model=list[AdminUserResponse],
)
def list_admin_users(
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    allowed_roles = {"student", "tutor", "admin"}

    if role is not None and role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rol no válido",
        )

    query = (
        select(User)
        .options(
            selectinload(User.student_profile),
            selectinload(User.tutor),
        )
    )

    if role is not None:
        query = query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = (
        query
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    users = db.scalars(query).all()

    return [serialize_admin_user(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=AdminUserResponse,
)
def get_admin_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    user = db.scalar(
        select(User)
        .options(
            selectinload(User.student_profile),
            selectinload(User.tutor),
        )
        .where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return serialize_admin_user(user)


@router.patch(
    "/{user_id}/status",
    response_model=AdminUserStatusResponse,
)
def update_admin_user_status(
    user_id: int,
    data: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar el estado de tu propia cuenta",
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se permite modificar cuentas administrativas",
        )

    if user.is_active == data.is_active:
        return AdminUserStatusResponse(
            id=user.id,
            is_active=user.is_active,
            message="La cuenta ya tiene el estado solicitado",
        )

    try:
        user.is_active = data.is_active
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    return AdminUserStatusResponse(
        id=user.id,
        is_active=user.is_active,
        message=(
            "Cuenta activada correctamente"
            if user.is_active
            else "Cuenta desactivada correctamente"
        ),
    )
