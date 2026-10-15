from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import (
    Session,
    selectinload,
)

from app.database.connection import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicResponse
from app.models.exercise import Exercise
from app.schemas.exercise import ExerciseResponse


router = APIRouter(
    prefix="/topics",
    tags=["Topics"],
)


@router.get(
    "",
    response_model=list[TopicResponse],
)
def get_topics(
    subject_id: int | None = None,
    db: Session = Depends(get_db),
):

    query = (
        select(Topic)
        .where(
            Topic.is_active.is_(True),
        )
        .order_by(
            Topic.order_number,
        )
    )


    if subject_id is not None:

        query = query.where(
            Topic.subject_id == subject_id,
        )


    topics = db.scalars(
        query,
    ).all()


    return topics

@router.get(
    "/{topic_id}/exercises",
    response_model=list[ExerciseResponse],
)
def get_topic_exercises(
    topic_id: int,
    db: Session = Depends(get_db),
):
    topic = db.get(Topic, topic_id)

    if topic is None or not topic.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado",
    )

    query = (
        select(Exercise)
        .options(
            selectinload(
                Exercise.options,
            ),
        )
        .where(
            Exercise.topic_id == topic_id,
            Exercise.is_active.is_(True),
        )
        .order_by(
            Exercise.id,
        )
    )


    exercises = db.scalars(
        query,
    ).all()


    return exercises