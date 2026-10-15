from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.class_model import TutoringClass
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.class_schema import (
    ClassCreate,
    ClassResponse,
    ClassUpdate,
)


router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)


# Consultar clases disponibles
@router.get(
    "",
    response_model=list[ClassResponse],
)
def get_classes(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(TutoringClass).order_by(
            TutoringClass.date_time
        )
    ).all()


# Consultar una clase por ID
@router.get(
    "/{class_id}",
    response_model=ClassResponse,
)
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
):
    tutoring_class = db.get(TutoringClass, class_id)

    if tutoring_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    return tutoring_class


# Crear una clase: tutor propietario o administrador
@router.post(
    "",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("tutor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear clases",
        )

    tutor = db.get(Tutor, data.tutor_id)

    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor no encontrado",
        )

    if current_user.role == "tutor":
        if tutor.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes crear clases para tu perfil",
            )

        if not tutor.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu perfil de tutor está inactivo",
            )

    if db.get(Subject, data.subject_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada",
        )

    tutoring_class = TutoringClass(
        **data.model_dump()
    )

    db.add(tutoring_class)

    try:
        db.commit()
        db.refresh(tutoring_class)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear la clase",
        )

    return tutoring_class


# Actualizar una clase: tutor propietario o administrador
@router.patch(
    "/{class_id}",
    response_model=ClassResponse,
)
def update_class(
    class_id: int,
    data: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("tutor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar clases",
        )

    tutoring_class = db.get(TutoringClass, class_id)

    if tutoring_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    tutor = db.get(Tutor, tutoring_class.tutor_id)

    is_admin = current_user.role == "admin"
    is_owner = (
        tutor is not None
        and tutor.user_id == current_user.id
        and current_user.role == "tutor"
    )

    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar clases de otro tutor",
        )

    if is_owner and not tutor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu perfil de tutor está inactivo",
        )

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    # No permitir transferir una clase desde este endpoint
    if "tutor_id" in update_data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede cambiar el tutor de una clase",
        )

    if "subject_id" in update_data:
        if db.get(Subject, update_data["subject_id"]) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada",
            )

    for key, value in update_data.items():
        setattr(tutoring_class, key, value)

    try:
        db.commit()
        db.refresh(tutoring_class)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible actualizar la clase",
        )

    return tutoring_class
