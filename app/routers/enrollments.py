from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_student
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    StudentClassCatalogItem,
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


# Catálogo del estudiante: clases programadas de su grado (sin IDs de tutor ajenos).
@router.get(
    "/catalog",
    response_model=list[StudentClassCatalogItem],
)
def get_student_class_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    grade = db.scalar(
        select(StudentProfile.grade).where(
            StudentProfile.user_id == current_user.id
        )
    )

    if grade is None:
        return []

    rows = db.execute(
        select(TutoringClass, Subject, Tutor, User, Enrollment.id)
        .join(Subject, Subject.id == TutoringClass.subject_id)
        .join(Tutor, Tutor.id == TutoringClass.tutor_id)
        .join(User, User.id == Tutor.user_id)
        .outerjoin(
            Enrollment,
            (Enrollment.class_id == TutoringClass.id)
            & (Enrollment.user_id == current_user.id),
        )
        .where(
            Subject.grade == grade,
            TutoringClass.status == "scheduled",
            Tutor.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(TutoringClass.date_time, TutoringClass.id)
    ).all()

    return [
        StudentClassCatalogItem(
            class_id=c.id,
            title=c.title,
            description=c.description,
            date_time=c.date_time,
            duration_minutes=c.duration_minutes,
            price=c.price,
            status=c.status,
            subject_id=s.id,
            subject_name=s.name,
            subject_grade=s.grade,
            tutor_name=u.name,
            tutor_specialty=t.specialty,
            enrollment_id=enrollment_id,
        )
        for c, s, t, u, enrollment_id in rows
    ]


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

    student_grade = db.scalar(
        select(StudentProfile.grade).where(
            StudentProfile.user_id == student.id
        )
    )
    subject_grade = db.scalar(
        select(Subject.grade).where(
            Subject.id == tutoring_class.subject_id
        )
    )

    if student_grade is None or student_grade != subject_grade:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta clase no corresponde al grado del estudiante",
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
