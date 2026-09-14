from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentCreate(BaseModel):
    user_id: int
    class_id: int


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    class_id: int
    enrollment_date: datetime
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )
