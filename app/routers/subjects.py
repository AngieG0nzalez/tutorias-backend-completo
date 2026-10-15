from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_admin
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


# Consulta pública de materias
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


# Consulta pública de una materia
@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
):
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada",
        )

    return subject


# Solo el administrador puede crear materias
@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
):
    subject = Subject(**data.model_dump())

    db.add(subject)

    try:
        db.commit()
        db.refresh(subject)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La materia ya existe para ese grado",
        )

    return subject


# Solo el administrador puede actualizar materias
@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
    dependencies=[Depends(require_admin)],
)
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: Session = Depends(get_db),
):
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada",
        )

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    for key, value in update_data.items():
        setattr(subject, key, value)

    try:
        db.commit()
        db.refresh(subject)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La materia ya existe para ese grado",
        )

    return subject


# Solo el administrador puede eliminar materias
@router.delete(
    "/{subject_id}",
    dependencies=[Depends(require_admin)],
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
):
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada",
        )

    try:
        db.delete(subject)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una materia con registros asociados",
        )

    return {
        "message": "Materia eliminada",
    }
