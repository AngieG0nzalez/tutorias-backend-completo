
from pydantic import BaseModel

from app.schemas.exercise import ExerciseResponse


class AdaptiveRecommendationResponse(BaseModel):
    topic_id: int
    current_level: str
    recommended_difficulty: str
    selected_difficulty: str
    exercise: ExerciseResponse
