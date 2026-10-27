from decimal import Decimal
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


class StudentClassCatalogItem(BaseModel):
    class_id: int
    title: str
    description: str | None
    date_time: datetime
    duration_minutes: int
    price: Decimal
    status: str
    subject_id: int
    subject_name: str
    subject_grade: int
    tutor_name: str
    tutor_specialty: str | None
    enrollment_id: int | None
