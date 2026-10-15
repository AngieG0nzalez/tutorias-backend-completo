from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
)


router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"],
)


# Consultar inscripciones según el rol autenticado
@router.get(
    "",
    response_model=list[EnrollmentResponse],
)
def get_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Enrollment).order_by(Enrollment.id)

    if current_user.role == "student":
        query = query.where(
            Enrollment.user_id == current_user.id
        )

    elif current_user.role == "tutor":
        query = (
            query
            .join(
                TutoringClass,
                Enrollment.class_id == TutoringClass.id,
            )
            .join(
                Tutor,
                TutoringClass.tutor_id == Tutor.id,
            )
            .where(Tutor.user_id == current_user.id)
        )

    elif current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar inscripciones",
        )

    return db.scalars(query).all()


# Crear una inscripción
@router.post(
    "",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("student", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear inscripciones",
        )

    # Un estudiante solo puede inscribirse a sí mismo
    if (
        current_user.role == "student"
        and data.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes inscribirte a ti mismo",
        )

    student = db.get(User, data.user_id)

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if student.role != "student" or not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El usuario debe ser un estudiante activo",
        )

    tutoring_class = db.get(TutoringClass, data.class_id)

    if tutoring_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    if tutoring_class.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La clase no está disponible para inscripciones",
        )

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == data.user_id,
            Enrollment.class_id == data.class_id,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El estudiante ya está inscrito en esta clase",
        )

    enrollment = Enrollment(
        user_id=data.user_id,
        class_id=data.class_id,
    )

    db.add(enrollment)

    try:
        db.commit()
        db.refresh(enrollment)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear la inscripción",
        )

    return enrollment


# Eliminar una inscripción
@router.delete("/{enrollment_id}")
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment = db.get(Enrollment, enrollment_id)

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inscripción no encontrada",
        )

    is_admin = current_user.role == "admin"

    is_owner = (
        current_user.role == "student"
        and enrollment.user_id == current_user.id
    )

    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta inscripción",
        )

    db.delete(enrollment)
    db.commit()

    return {
        "message": "Inscripción eliminada",
    }
