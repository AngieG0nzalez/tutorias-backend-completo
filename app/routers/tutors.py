from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
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


@router.get(
    "/{tutor_id}",
    response_model=TutorResponse,
)
def get_tutor(
    tutor_id: int,
    db: Session = Depends(get_db),
):
    tutor = db.get(
        Tutor,
        tutor_id,
    )

    if not tutor:
        raise HTTPException(
            status_code=404,
            detail="Tutor no encontrado",
        )

    return tutor


@router.post(
    "",
    response_model=TutorResponse,
    status_code=201,
)
def create_tutor(
    data: TutorCreate,
    db: Session = Depends(get_db),
):
    user = db.get(
        User,
        data.user_id,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )

    tutor = Tutor(
        **data.model_dump(),
    )

    db.add(tutor)

    try:
        db.commit()
        db.refresh(tutor)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El usuario ya tiene un perfil de tutor",
        )

    return tutor


@router.patch(
    "/{tutor_id}",
    response_model=TutorResponse,
)
def update_tutor(
    tutor_id: int,
    data: TutorUpdate,
    db: Session = Depends(get_db),
):
    tutor = db.get(
        Tutor,
        tutor_id,
    )

    if not tutor:
        raise HTTPException(
            status_code=404,
            detail="Tutor no encontrado",
        )

    for key, value in data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(tutor, key, value)

    db.commit()
    db.refresh(tutor)

    return tutor
