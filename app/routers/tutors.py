from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.tutor import (
    TutorCreate,
    TutorResponse,
    TutorUpdate,
)


router = APIRouter(
    prefix="/tutors",
    tags=["Tutors"],
)


# Consulta pública de tutores
@router.get(
    "",
    response_model=list[TutorResponse],
)
def get_tutors(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Tutor).order_by(Tutor.id)
    ).all()


# Consulta pública de un tutor
@router.get(
    "/{tutor_id}",
    response_model=TutorResponse,
)
def get_tutor(
    tutor_id: int,
    db: Session = Depends(get_db),
):
    tutor = db.get(Tutor, tutor_id)

    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor no encontrado",
        )

    return tutor


# Creación manual de perfiles: solo administrador
@router.post(
    "",
    response_model=TutorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_tutor(
    data: TutorCreate,
    db: Session = Depends(get_db),
):
    user = db.get(User, data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if user.role != "tutor":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario debe tener el rol tutor",
        )

    existing_tutor = db.scalar(
        select(Tutor).where(
            Tutor.user_id == data.user_id
        )
    )

    if existing_tutor is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya tiene un perfil de tutor",
        )

    tutor = Tutor(**data.model_dump())

    db.add(tutor)

    try:
        db.commit()
        db.refresh(tutor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el perfil de tutor",
        )

    return tutor


# Actualización: administrador o tutor propietario
@router.patch(
    "/{tutor_id}",
    response_model=TutorResponse,
)
def update_tutor(
    tutor_id: int,
    data: TutorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tutor = db.get(Tutor, tutor_id)

    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor no encontrado",
        )

    is_admin = current_user.role == "admin"
    is_owner = (
        current_user.role == "tutor"
        and current_user.id == tutor.user_id
    )

    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar este tutor",
        )

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    # Nunca permitir modificar estos campos desde el perfil
    forbidden_fields = {"id", "user_id", "rating"}

    if forbidden_fields.intersection(update_data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar campos protegidos",
        )

    # Solo un administrador puede activar o desactivar tutores
    if "is_active" in update_data and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede cambiar el estado del tutor",
        )

    for key, value in update_data.items():
        setattr(tutor, key, value)

    try:
        db.commit()
        db.refresh(tutor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible actualizar el perfil",
        )

    return tutor
