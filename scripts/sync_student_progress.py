
from sqlalchemy import select

import app.models

from app.database.connection import SessionLocal
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.topic import Topic
from app.services.progress_service import (
    recalculate_student_progress,
)


def sync_student_progress():
    db = SessionLocal()

    try:
        # Identificamos cada combinación de estudiante y tema
        # que tenga al menos un intento registrado.
        pairs = db.execute(
            select(
                ExerciseAttempt.user_id,
                Exercise.topic_id,
            )
            .join(
                Exercise,
                Exercise.id == ExerciseAttempt.exercise_id,
            )
            .distinct()
            .order_by(
                Exercise.topic_id,
                ExerciseAttempt.user_id,
            )
        ).all()

        print(f"Progresos por sincronizar: {len(pairs)}")

        updated = 0

        for user_id, topic_id in pairs:
            # Bloqueamos el tema mientras recalculamos
            # para mantener la consistencia con POST /attempts.
            db.scalar(
                select(Topic)
                .where(Topic.id == topic_id)
                .with_for_update()
            )

            progress = recalculate_student_progress(
                db=db,
                user_id=user_id,
                topic_id=topic_id,
            )

            print(
                f"Estudiante {user_id} | "
                f"Tema {topic_id} | "
                f"Intentos {progress.exercises_attempted} | "
                f"Aciertos {progress.exercises_correct} | "
                f"Dominio {progress.mastery_percentage}%"
            )

            updated += 1

        db.commit()

        print(
            f"Sincronización completada: "
            f"{updated} registros de progreso procesados."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sync_student_progress()
