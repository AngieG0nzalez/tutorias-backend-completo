from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "class_id",
            name="uq_user_class",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id"),
        nullable=False,
    )

    enrollment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="enrolled",
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="enrollments",
    )

    tutoring_class = relationship(
        "TutoringClass",
        back_populates="enrollments",
    )
