from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy.sql import func

from app.database.base import Base


class ExerciseOption(Base):

    __tablename__ = "exercise_options"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )


    exercise_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "exercises.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


    option_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


    order_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


    exercise = relationship(
        "Exercise",
        back_populates="options",
    )

    attempts = relationship(
        "ExerciseAttempt",
        back_populates="selected_option",
    )