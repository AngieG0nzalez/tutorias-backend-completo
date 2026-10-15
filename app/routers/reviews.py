from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.review import Review
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


# Consulta pública de reseñas
@router.get(
    "",
    response_model=list[ReviewResponse],
)
def get_reviews(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Review).order_by(Review.created_at.desc())
    ).all()


# Crear una reseña: solo estudiantes que participaron
@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los estudiantes pueden calificar clases",
        )

    tutor = db.get(Tutor, data.tutor_id)

    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor no encontrado",
        )

    tutoring_class = db.get(TutoringClass, data.class_id)

    if tutoring_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

    if tutoring_class.tutor_id != tutor.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El tutor no corresponde a esta clase",
        )

    if tutoring_class.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo puedes calificar clases completadas",
        )

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.class_id == tutoring_class.id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes estar inscrito en la clase para calificarla",
        )

    existing_review = db.scalar(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.class_id == tutoring_class.id,
        )
    )

    if existing_review is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya calificaste esta clase",
        )

    review = Review(
        user_id=current_user.id,
        tutor_id=tutor.id,
        class_id=tutoring_class.id,
        rating=data.rating,
        comment=data.comment,
    )

    db.add(review)

    try:
        db.commit()
        db.refresh(review)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear la reseña",
        )

    return review
