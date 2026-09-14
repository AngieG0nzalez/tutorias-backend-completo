from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
)


router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"],
)


@router.get(
    "",
    response_model=list[EnrollmentResponse],
)
def get_enrollments(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Enrollment).order_by(
            Enrollment.id,
        )
    ).all()


@router.post(
    "",
    response_model=EnrollmentResponse,
    status_code=201,
)
def create_enrollment(
    data: EnrollmentCreate,
    db: Session = Depends(get_db),
):
    if not db.get(User, data.user_id):
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    if not db.get(TutoringClass, data.class_id):
        raise HTTPException(
            status_code=404,
            detail="Clase no encontrada",
        )

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == data.user_id,
            Enrollment.class_id == data.class_id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="El usuario ya está inscrito",
        )

    enrollment = Enrollment(
        **data.model_dump(),
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


@router.delete("/{enrollment_id}")
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
):
    enrollment = db.get(
        Enrollment,
        enrollment_id,
    )

    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Inscripción no encontrada",
        )

    db.delete(enrollment)
    db.commit()

    return {
        "message": "Inscripción eliminada",
    }
