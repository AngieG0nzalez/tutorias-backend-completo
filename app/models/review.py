from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Review(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "class_id",
            name="uq_review_user_class",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    tutor_id: Mapped[int] = mapped_column(
        ForeignKey("tutors.id"),
        nullable=False,
    )

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id"),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="reviews",
    )

    tutor = relationship(
        "Tutor",
        back_populates="reviews",
    )

    tutoring_class = relationship(
        "TutoringClass",
        back_populates="reviews",
    )
