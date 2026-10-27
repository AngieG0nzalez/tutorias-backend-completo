from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_admin
from app.models.class_model import TutoringClass
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.models.tutor_subject import TutorSubject
from app.models.user import User
from app.schemas.tutor import (
    AdminTutorSubjectCreate,
    AdminTutorSubjectResponse,
)
from app.services.account_security import audit


router = APIRouter(
    prefix="/admin/tutors",
    tags=["Admin Tutor Subjects"],
)


def get_tutor_or_404(db: Session, tutor_id: int) -> Tutor:
    tutor = db.get(Tutor, tutor_id)
    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor no encontrado",
        )
    return tutor


def list_assignments(db: Session, tutor_id: int):
    rows = db.execute(
        select(TutorSubject, Subject)
        .join(Subject, Subject.id == TutorSubject.subject_id)
        .where(TutorSubject.tutor_id == tutor_id)
        .order_by(Subject.grade, Subject.name)
    ).all()
    return [
        AdminTutorSubjectResponse(
            subject_id=subject.id,
            name=subject.name,
            grade=subject.grade,
            assigned_at=link.created_at,
        )
        for link, subject in rows
    ]


@router.get(
    "/{tutor_id}/subjects",
    response_model=list[AdminTutorSubjectResponse],
)
def get_tutor_subjects(
    tutor_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    get_tutor_or_404(db, tutor_id)
    return list_assignments(db, tutor_id)


@router.post(
    "/{tutor_id}/subjects",
    response_model=AdminTutorSubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_subject_to_tutor(
    tutor_id: int,
    data: AdminTutorSubjectCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    tutor = get_tutor_or_404(db, tutor_id)
    if not tutor.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El tutor está inactivo",
        )
    subject = db.get(Subject, data.subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Materia no encontrada",
        )
    exists = db.scalar(
        select(TutorSubject.id).where(
            TutorSubject.tutor_id == tutor_id,
            TutorSubject.subject_id == subject.id,
        )
    )
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La materia ya está asignada a este tutor",
        )
    link = TutorSubject(tutor_id=tutor_id, subject_id=subject.id)
    db.add(link)
    try:
        audit(
            db,
            tutor.user_id,
            "admin_subject_assign",
            actor_user_id=current_admin.id,
            reason=f"Materia {subject.id}",
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La materia ya está asignada a este tutor",
        )
    except Exception:
        db.rollback()
        raise
    db.refresh(link)
    return AdminTutorSubjectResponse(
        subject_id=subject.id,
        name=subject.name,
        grade=subject.grade,
        assigned_at=link.created_at,
    )


@router.delete(
    "/{tutor_id}/subjects/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_subject_from_tutor(
    tutor_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    tutor = get_tutor_or_404(db, tutor_id)
    link = db.scalar(
        select(TutorSubject).where(
            TutorSubject.tutor_id == tutor_id,
            TutorSubject.subject_id == subject_id,
        )
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La materia no está asignada a este tutor",
        )
    # Regla: no se retira la materia mientras existan clases programadas.
    scheduled = db.scalar(
        select(func.count(TutoringClass.id)).where(
            TutoringClass.tutor_id == tutor_id,
            TutoringClass.subject_id == subject_id,
            TutoringClass.status == "scheduled",
        )
    )
    if scheduled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El tutor tiene {scheduled} clase(s) programada(s) de esta "
                "materia. Cancélalas o finalízalas antes de retirarla."
            ),
        )
    try:
        db.delete(link)
        audit(
            db,
            tutor.user_id,
            "admin_subject_remove",
            actor_user_id=current_admin.id,
            reason=f"Materia {subject_id}",
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
