
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TutorPanelProfile(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    bio: str | None
    specialty: str | None
    experience_years: int
    rating: Decimal | None
    is_active: bool


class TutorPanelSubject(BaseModel):
    id: int
    name: str
    grade: int


class TutorPanelClass(BaseModel):
    id: int
    subject_id: int
    title: str
    description: str | None
    date_time: datetime
    duration_minutes: int
    price: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorPanelStudent(BaseModel):
    enrollment_id: int
    user_id: int
    name: str
    email: str
    enrollment_status: str
    enrollment_date: datetime


class TutorPanelSummary(BaseModel):
    total_classes: int
    scheduled_classes: int
    completed_classes: int
    cancelled_classes: int
    total_enrollments: int
    total_subjects: int
