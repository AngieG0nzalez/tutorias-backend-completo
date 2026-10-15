
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.student_progress import StudentProgress



def calculate_level(percentage: Decimal) -> str:
    """
    Clasifica el dominio del estudiante
    utilizando los niveles definidos en Supabase.

    new: sin intentos
    low: dominio inferior al 40 %
    medium: dominio entre 40 % y 69.99 %
    high: dominio desde el 70 %
    """
    if percentage >= 70:
        return "high"

    if percentage >= 40:
        return "medium"

    return "low"



def recalculate_student_progress(
    db: Session,
    user_id: int,
    topic_id: int,
) -> StudentProgress:
    """
    Recalcula el progreso de un estudiante
    utilizando todos sus intentos en un tema.

    No hace commit: la transacción pertenece
    al endpoint que llama esta función.
    """

    stats = db.execute(
        select(
            func.count(ExerciseAttempt.id),
            func.coalesce(
                func.sum(
                    case(
                        (
                            ExerciseAttempt.is_correct.is_(True),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.max(ExerciseAttempt.created_at),
        )
        .join(
            Exercise,
            Exercise.id == ExerciseAttempt.exercise_id,
        )
        .where(
            ExerciseAttempt.user_id == user_id,
            Exercise.topic_id == topic_id,
        )
    ).one()

    total_attempts = int(stats[0])
    correct_attempts = int(stats[1])
    last_attempt = stats[2]

    percentage = (
        Decimal(correct_attempts)
        / Decimal(total_attempts)
        * Decimal("100")
        if total_attempts > 0
        else Decimal("0")
    ).quantize(Decimal("0.01"))

    progress = db.scalar(
        select(StudentProgress).where(
            StudentProgress.user_id == user_id,
            StudentProgress.topic_id == topic_id,
        )
    )

    if progress is None:
        progress = StudentProgress(
            user_id=user_id,
            topic_id=topic_id,
        )
        db.add(progress)

    progress.exercises_attempted = total_attempts
    progress.exercises_correct = correct_attempts
    progress.mastery_percentage = percentage
    progress.level = (
        "new"
        if total_attempts == 0
        else calculate_level(percentage)
    )
    progress.last_practiced_at = last_attempt
    progress.updated_at = datetime.now(timezone.utc)

    db.flush()

    return progress
