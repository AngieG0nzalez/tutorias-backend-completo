from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    grade: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    classes = relationship(
        "TutoringClass",
        back_populates="subject",
    )

    tutor_subjects = relationship(
        "TutorSubject",
        back_populates="subject",
    )
