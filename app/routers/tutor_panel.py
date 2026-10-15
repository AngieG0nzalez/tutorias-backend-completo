
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_tutor
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.models.tutor_subject import TutorSubject
from app.models.user import User
from app.schemas.tutor_panel import (
    TutorPanelClass,
    TutorPanelProfile,
    TutorPanelStudent,
    TutorPanelSubject,
    TutorPanelSummary,
)


router = APIRouter(
    prefix="/tutor-panel",
    tags=["Tutor Panel"],
)


def get_my_tutor(
    db: Session,
    current_user: User,
) -> Tutor:
    """
    Obtiene el perfil asociado al JWT.
    No acepta IDs de otros tutores.
    """
    tutor = db.scalar(
        select(Tutor).where(
            Tutor.user_id == current_user.id
        )
    )

    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes un perfil de tutor registrado",
        )

    return tutor


@router.get(
    "/me",
    response_model=TutorPanelProfile,
)
def get_my_tutor_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    tutor = get_my_tutor(db, current_user)

    return TutorPanelProfile(
        id=tutor.id,
        user_id=tutor.user_id,
        name=current_user.name,
        email=current_user.email,
        bio=tutor.bio,
        specialty=tutor.specialty,
        experience_years=tutor.experience_years,
        rating=tutor.rating,
        is_active=tutor.is_active,
    )


@router.get(
    "/classes",
    response_model=list[TutorPanelClass],
)
def get_my_tutor_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    tutor = get_my_tutor(db, current_user)

    query = (
        select(TutoringClass)
        .where(TutoringClass.tutor_id == tutor.id)
        .order_by(
            TutoringClass.date_time.desc(),
            TutoringClass.id.desc(),
        )
    )

    return db.scalars(query).all()


@router.get(
    "/classes/{class_id}/students",
    response_model=list[TutorPanelStudent],
)
def get_my_class_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    tutor = get_my_tutor(db, current_user)

    tutoring_class = db.get(TutoringClass, class_id)

    if (
        tutoring_class is None
        or tutoring_class.tutor_id != tutor.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    rows = db.execute(
        select(Enrollment, User)
        .join(User, User.id == Enrollment.user_id)
        .where(
            Enrollment.class_id == class_id,
            User.role == "student",
        )
        .order_by(Enrollment.id)
    ).all()

    return [
        TutorPanelStudent(
            enrollment_id=enrollment.id,
            user_id=student.id,
            name=student.name,
            email=student.email,
            enrollment_status=enrollment.status,
            enrollment_date=enrollment.enrollment_date,
        )
        for enrollment, student in rows
    ]


@router.get(
    "/subjects",
    response_model=list[TutorPanelSubject],
)
def get_my_tutor_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    tutor = get_my_tutor(db, current_user)

    subjects = db.scalars(
        select(Subject)
        .join(
            TutorSubject,
            TutorSubject.subject_id == Subject.id,
        )
        .where(TutorSubject.tutor_id == tutor.id)
        .order_by(Subject.grade, Subject.name)
    ).all()

    return [
        TutorPanelSubject(
            id=subject.id,
            name=subject.name,
            grade=subject.grade,
        )
        for subject in subjects
    ]


@router.get(
    "/summary",
    response_model=TutorPanelSummary,
)
def get_my_tutor_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    tutor = get_my_tutor(db, current_user)

    total_classes = db.scalar(
        select(func.count(TutoringClass.id))
        .where(TutoringClass.tutor_id == tutor.id)
    ) or 0

    scheduled_classes = db.scalar(
        select(func.count(TutoringClass.id))
        .where(
            TutoringClass.tutor_id == tutor.id,
            TutoringClass.status == "scheduled",
        )
    ) or 0

    completed_classes = db.scalar(
        select(func.count(TutoringClass.id))
        .where(
            TutoringClass.tutor_id == tutor.id,
            TutoringClass.status == "completed",
        )
    ) or 0

    cancelled_classes = db.scalar(
        select(func.count(TutoringClass.id))
        .where(
            TutoringClass.tutor_id == tutor.id,
            TutoringClass.status == "cancelled",
        )
    ) or 0

    total_enrollments = db.scalar(
        select(func.count(Enrollment.id))
        .join(
            TutoringClass,
            Enrollment.class_id == TutoringClass.id,
        )
        .where(TutoringClass.tutor_id == tutor.id)
    ) or 0

    total_subjects = db.scalar(
        select(func.count(TutorSubject.id))
        .where(TutorSubject.tutor_id == tutor.id)
    ) or 0

    return TutorPanelSummary(
        total_classes=total_classes,
        scheduled_classes=scheduled_classes,
        completed_classes=completed_classes,
        cancelled_classes=cancelled_classes,
        total_enrollments=total_enrollments,
        total_subjects=total_subjects,
    )
