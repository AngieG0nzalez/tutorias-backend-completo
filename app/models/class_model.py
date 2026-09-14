from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TutoringClass(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    tutor_id: Mapped[int] = mapped_column(
        ForeignKey("tutors.id"),
        nullable=False,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tutor = relationship(
        "Tutor",
        back_populates="classes",
    )

    subject = relationship(
        "Subject",
        back_populates="classes",
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="tutoring_class",
    )

    reviews = relationship(
        "Review",
        back_populates="tutoring_class",
    )
