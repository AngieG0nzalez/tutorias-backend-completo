
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_tutor
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.student_profile import StudentProfile
from app.models.student_progress import StudentProgress
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.models.tutor_subject import TutorSubject
from app.models.user import User
from app.schemas.tutor_panel import (
    TutorPanelClass,
    TutorPanelProfile,
    TutorPanelStudent,
    TutorPanelSubject,
    TutorPanelSummary,
    TutorStudentProgressResponse,
    TutorStudentProgressSummary,
    TutorStudentSubjectInfo,
    TutorStudentTopicProgress,
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
    "/classes/{class_id}/students/{student_user_id}/progress",
    response_model=TutorStudentProgressResponse,
)
def get_class_student_progress(
    class_id: int,
    student_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
):
    """
    Progreso global del estudiante en la materia de una clase propia.
    No es progreso atribuible a la clase: student_progress es por tema.
    """
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Estudiante o clase no disponible",
    )

    tutor = db.scalar(
        select(Tutor).where(Tutor.user_id == current_user.id)
    )
    if tutor is None:
        raise not_found

    # Clase propia + inscripción activa en ESA clase + usuario estudiante.
    row = db.execute(
        select(TutoringClass, User)
        .join(Enrollment, Enrollment.class_id == TutoringClass.id)
        .join(User, User.id == Enrollment.user_id)
        .where(
            TutoringClass.id == class_id,
            TutoringClass.tutor_id == tutor.id,
            Enrollment.user_id == student_user_id,
            Enrollment.status == "enrolled",
            User.role == "student",
        )
        .limit(1)
    ).first()
    if row is None:
        raise not_found
    tutoring_class, student = row

    subject = db.get(Subject, tutoring_class.subject_id)
    grade = db.scalar(
        select(StudentProfile.grade).where(
            StudentProfile.user_id == student.id
        )
    )

    # Una sola consulta: temas activos de la materia + progreso del alumno.
    rows = db.execute(
        select(Topic, StudentProgress)
        .outerjoin(
            StudentProgress,
            (StudentProgress.topic_id == Topic.id)
            & (StudentProgress.user_id == student.id),
        )
        .where(
            Topic.subject_id == tutoring_class.subject_id,
            Topic.is_active.is_(True),
        )
        .order_by(Topic.order_number, Topic.id)
    ).all()

    topics = []
    for topic, progress in rows:
        attempted = progress.exercises_attempted if progress else 0
        topics.append(
            TutorStudentTopicProgress(
                topic_id=topic.id,
                topic_name=topic.name,
                order_number=topic.order_number,
                exercises_attempted=attempted,
                exercises_correct=progress.exercises_correct if progress else 0,
                mastery_percentage=float(progress.mastery_percentage) if progress else 0.0,
                level=progress.level if progress else "new",
                last_practiced_at=progress.last_practiced_at if progress else None,
                practiced=attempted > 0,
            )
        )

    practiced = [t for t in topics if t.practiced]
    attempted_total = sum(t.exercises_attempted for t in topics)
    correct_total = sum(t.exercises_correct for t in topics)

    return TutorStudentProgressResponse(
        class_id=tutoring_class.id,
        student_user_id=student.id,
        student_name=student.name,
        student_grade=grade,
        subject=TutorStudentSubjectInfo(
            id=subject.id, name=subject.name, grade=subject.grade
        ),
        summary=TutorStudentProgressSummary(
            total_topics=len(topics),
            practiced_topics=len(practiced),
            unpracticed_topics=len(topics) - len(practiced),
            exercises_attempted=attempted_total,
            exercises_correct=correct_total,
            accuracy_percentage=(
                round(100 * correct_total / attempted_total, 2)
                if attempted_total
                else None
            ),
            average_mastery_percentage=(
                round(
                    sum(t.mastery_percentage for t in practiced)
                    / len(practiced),
                    2,
                )
                if practiced
                else None
            ),
        ),
        topics=topics,
    )


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
