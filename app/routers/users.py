
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# Solo el administrador puede listar todos los usuarios
@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_admin)],
)
def get_users(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(User).order_by(User.id)
    ).all()


# Cualquier usuario autenticado puede consultar su perfil
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# Consultar un usuario:
# - Administrador: cualquier usuario
# - Estudiante o tutor: únicamente su propio usuario
@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar este usuario",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return user


# Actualizar usuario:
# - Administrador: puede actualizar perfiles permitidos
# - Estudiante o tutor: solo puede actualizar su propio perfil
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar este usuario",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Campos que se pueden actualizar desde este endpoint.
    # No permitir cambios de rol, contraseña o estado de la cuenta.
    allowed_fields = {"name"}

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    forbidden_fields = set(update_data) - allowed_fields

    if forbidden_fields:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No está permitido modificar estos campos: "
                + ", ".join(sorted(forbidden_fields))
            ),
        )

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user
