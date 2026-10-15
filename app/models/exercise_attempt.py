from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.sql import func

from app.database.base import Base


class ExerciseAttempt(Base):

    __tablename__ = "exercise_attempts"


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


    exercise_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "exercises.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


    selected_option_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "exercise_options.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )


    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )


    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )


    response_time_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="exercise_attempts",
    )

    exercise = relationship(
        "Exercise",
        back_populates="attempts",
    )

    selected_option = relationship(
        "ExerciseOption",
        back_populates="attempts",
    )