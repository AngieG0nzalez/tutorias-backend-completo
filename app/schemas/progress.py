from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    exercises_attempted: int
    exercises_correct: int
    mastery_percentage: Decimal
    level: str
    last_practiced_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
