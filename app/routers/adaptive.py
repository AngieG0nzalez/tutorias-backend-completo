
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_student
from app.models.topic import Topic
from app.models.user import User
from app.schemas.adaptive import AdaptiveRecommendationResponse
from app.services.adaptive_service import recommend_next_exercise


router = APIRouter(
    prefix="/adaptive",
    tags=["Adaptive Learning"],
)


@router.get(
    "/topics/{topic_id}/next",
    response_model=AdaptiveRecommendationResponse,
)
def get_next_exercise(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    topic = db.get(Topic, topic_id)

    if topic is None or not topic.is_active:
        raise HTTPException(
            status_code=404,
            detail="Tema no encontrado o inactivo",
        )

    recommendation = recommend_next_exercise(
        db=db,
        user_id=current_user.id,
        topic_id=topic_id,
    )

    if recommendation is None:
        raise HTTPException(
            status_code=404,
            detail="No hay ejercicios disponibles para este tema",
        )

    return AdaptiveRecommendationResponse(
        topic_id=topic_id,
        current_level=recommendation["level"],
        recommended_difficulty=recommendation["recommended_difficulty"],
        selected_difficulty=recommendation["selected_difficulty"],
        exercise=recommendation["exercise"],
    )
