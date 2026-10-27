
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


class TutorStudentSubjectInfo(BaseModel):
    id: int
    name: str
    grade: int


class TutorStudentTopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    order_number: int
    exercises_attempted: int
    exercises_correct: int
    mastery_percentage: float
    level: str
    last_practiced_at: datetime | None
    practiced: bool


class TutorStudentProgressSummary(BaseModel):
    total_topics: int
    practiced_topics: int
    unpracticed_topics: int
    exercises_attempted: int
    exercises_correct: int
    accuracy_percentage: float | None
    average_mastery_percentage: float | None


class TutorStudentProgressResponse(BaseModel):
    class_id: int
    student_user_id: int
    student_name: str
    student_grade: int | None
    subject: TutorStudentSubjectInfo
    summary: TutorStudentProgressSummary
    topics: list[TutorStudentTopicProgress]
