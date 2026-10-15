from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_student
from app.models.student_progress import StudentProgress
from app.models.user import User
from app.schemas.progress import ProgressResponse


router = APIRouter(
    prefix="/progress",
    tags=["Student Progress"],
)


@router.get(
    "/me",
    response_model=list[ProgressResponse],
)
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    query = (
        select(StudentProgress)
        .where(
            StudentProgress.user_id == current_user.id,
        )
        .order_by(StudentProgress.topic_id)
    )

    return db.scalars(query).all()


@router.get(
    "/me/{topic_id}",
    response_model=ProgressResponse,
)
def get_my_topic_progress(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    progress = db.scalar(
        select(StudentProgress).where(
            StudentProgress.user_id == current_user.id,
            StudentProgress.topic_id == topic_id,
        )
    )

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe progreso registrado para este tema",
        )

    return progress
