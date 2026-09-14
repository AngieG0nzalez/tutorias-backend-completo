from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.subject import Subject
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)


router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)


@router.get(
    "",
    response_model=list[SubjectResponse],
)
def get_subjects(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Subject).order_by(
            Subject.grade,
            Subject.name,
        )
    ).all()


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
):
    subject = db.get(
        Subject,
        subject_id,
    )

    if not subject:
        raise HTTPException(
            status_code=404,
            detail="Materia no encontrada",
        )

    return subject


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=201,
)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
):
    subject = Subject(
        **data.model_dump(),
    )

    db.add(subject)

    try:
        db.commit()
        db.refresh(subject)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="La materia ya existe para ese grado",
        )

    return subject


@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: Session = Depends(get_db),
):
    subject = db.get(
        Subject,
        subject_id,
    )

    if not subject:
        raise HTTPException(
            status_code=404,
            detail="Materia no encontrada",
        )

    for key, value in data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(subject, key, value)

    try:
        db.commit()
        db.refresh(subject)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="La materia ya existe para ese grado",
        )

    return subject


@router.delete("/{subject_id}")
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
):
    subject = db.get(
        Subject,
        subject_id,
    )

    if not subject:
        raise HTTPException(
            status_code=404,
            detail="Materia no encontrada",
        )

    db.delete(subject)
    db.commit()

    return {
        "message": "Materia eliminada",
    }
