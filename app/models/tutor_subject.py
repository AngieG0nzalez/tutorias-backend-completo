from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TutorSubject(Base):
    __tablename__ = "tutor_subjects"

    __table_args__ = (
        UniqueConstraint(
            "tutor_id",
            "subject_id",
            name="uq_tutor_subject",
        ),
    )

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tutor = relationship(
        "Tutor",
        back_populates="tutor_subjects",
    )

    subject = relationship(
        "Subject",
        back_populates="tutor_subjects",
    )
