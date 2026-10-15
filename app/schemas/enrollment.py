from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentCreate(BaseModel):
    user_id: int = Field(gt=0)
    class_id: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid",
    )


class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    class_id: int
    enrollment_date: datetime
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )
