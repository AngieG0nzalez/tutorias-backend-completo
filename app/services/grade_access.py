from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User


def ensure_student_can_practice_topic(
    db: Session,
    student: User,
    topic: Topic,
) -> None:
    """El estudiante solo practica materias de su propio grado."""
    student_grade = db.scalar(
        select(StudentProfile.grade).where(
            StudentProfile.user_id == student.id
        )
    )

    if student_grade is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu perfil no tiene un grado asignado. Contacta a un administrador.",
        )

    subject_grade = db.scalar(
        select(Subject.grade).where(Subject.id == topic.subject_id)
    )

    if subject_grade != student_grade:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este tema no corresponde a tu grado",
        )
