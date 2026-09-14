from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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


class Tutor(Base):
    __tablename__ = "tutors"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    specialty: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="tutor",
    )

    classes = relationship(
        "TutoringClass",
        back_populates="tutor",
    )

    tutor_subjects = relationship(
        "TutorSubject",
        back_populates="tutor",
    )

    reviews = relationship(
        "Review",
        back_populates="tutor",
    )
