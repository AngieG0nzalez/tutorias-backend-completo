from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.class_model import TutoringClass
from app.models.review import Review
from app.models.tutor import Tutor
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
)


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.get(
    "",
    response_model=list[ReviewResponse],
)
def get_reviews(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Review).order_by(
            Review.created_at.desc(),
        )
    ).all()


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=201,
)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tutor = db.get(
        Tutor,
        data.tutor_id,
    )

    if not tutor:
        raise HTTPException(
            status_code=404,
            detail="Tutor no encontrado",
        )

    tutoring_class = db.get(
        TutoringClass,
        data.class_id,
    )

    if not tutoring_class:
        raise HTTPException(
            status_code=404,
            detail="Clase no encontrada",
        )

    review = Review(
        user_id=current_user.id,
        tutor_id=data.tutor_id,
        class_id=data.class_id,
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
            status_code=409,
            detail="Ya calificaste esta clase",
        )

    return review
