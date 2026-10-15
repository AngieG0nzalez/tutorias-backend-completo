from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.sql import func

from app.database.base import Base


class StudentProgress(Base):

    __tablename__ = "student_progress"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )


    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


    topic_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "topics.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


    exercises_attempted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )


    exercises_correct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )


    mastery_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )


    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="new",
    )


    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="student_progress",
    )

    topic = relationship(
        "Topic",
        back_populates="student_progress",
    )