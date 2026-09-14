from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.class_model import TutoringClass
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.schemas.class_schema import (
    ClassCreate,
    ClassResponse,
    ClassUpdate,
)


router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)


@router.get(
    "",
    response_model=list[ClassResponse],
)
def get_classes(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(TutoringClass).order_by(
            TutoringClass.date_time,
        )
    ).all()


@router.get(
    "/{class_id}",
    response_model=ClassResponse,
)
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
):
    tutoring_class = db.get(
        TutoringClass,
        class_id,
    )

    if not tutoring_class:
        raise HTTPException(
            status_code=404,
            detail="Clase no encontrada",
        )

    return tutoring_class


@router.post(
    "",
    response_model=ClassResponse,
    status_code=201,
)
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db),
):
    if not db.get(Tutor, data.tutor_id):
        raise HTTPException(
            status_code=404,
            detail="Tutor no encontrado",
        )

    if not db.get(Subject, data.subject_id):
        raise HTTPException(
            status_code=404,
            detail="Materia no encontrada",
        )

    tutoring_class = TutoringClass(
        **data.model_dump(),
    )

    db.add(tutoring_class)
    db.commit()
    db.refresh(tutoring_class)

    return tutoring_class


@router.patch(
    "/{class_id}",
    response_model=ClassResponse,
)
def update_class(
    class_id: int,
    data: ClassUpdate,
    db: Session = Depends(get_db),
):
    tutoring_class = db.get(
        TutoringClass,
        class_id,
    )

    if not tutoring_class:
        raise HTTPException(
            status_code=404,
            detail="Clase no encontrada",
        )

    for key, value in data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(
            tutoring_class,
            key,
            value,
        )

    db.commit()
    db.refresh(tutoring_class)

    return tutoring_class
