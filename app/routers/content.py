from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.exercise_option import ExerciseOption
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.models.tutor_subject import TutorSubject
from app.models.user import User
from app.routers.topics import get_active_tutor_for_subject
from app.services.exercise_service import (
    build_options,
    duplicate_conflict,
    find_duplicate,
    normalized_statement,
)
from app.schemas.content import (
    ContentExerciseCreate,
    ContentExerciseList,
    ContentExerciseResponse,
    ContentExerciseStatus,
    ContentExerciseUpdate,
    ContentOptionResponse,
    ContentSubjectCatalog,
    ContentTopicCatalog,
)
from app.schemas.exercise import ExerciseCreate


router = APIRouter(
    prefix="/content",
    tags=["Content Management"],
)


def require_content_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("admin", "tutor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador o tutor",
        )
    return current_user


def assigned_subject_ids(db: Session, user: User) -> set[int] | None:
    """None = sin restricción (administrador)."""
    if user.role == "admin":
        return None
    tutor = db.scalar(select(Tutor).where(Tutor.user_id == user.id))
    if tutor is None or not tutor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere un perfil de tutor activo",
        )
    return set(
        db.scalars(
            select(TutorSubject.subject_id).where(
                TutorSubject.tutor_id == tutor.id
            )
        ).all()
    )


def authorize_subject(db: Session, user: User, subject_id: int) -> None:
    if user.role == "admin":
        return
    get_active_tutor_for_subject(db, user, subject_id)


def load_topic_for_update(db: Session, topic_id: int) -> Topic:
    topic = db.scalar(
        select(Topic).where(Topic.id == topic_id).with_for_update()
    )
    if topic is None or not topic.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tema no encontrado",
        )
    return topic


def load_exercise(db: Session, exercise_id: int) -> Exercise:
    exercise = db.scalar(
        select(Exercise)
        .options(selectinload(Exercise.options))
        .where(Exercise.id == exercise_id)
        .with_for_update(of=Exercise)
    )
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada",
        )
    return exercise


def count_attempts(db: Session, exercise_ids: list[int]) -> dict[int, int]:
    if not exercise_ids:
        return {}
    rows = db.execute(
        select(ExerciseAttempt.exercise_id, func.count(ExerciseAttempt.id))
        .where(ExerciseAttempt.exercise_id.in_(exercise_ids))
        .group_by(ExerciseAttempt.exercise_id)
    ).all()
    return {exercise_id: total for exercise_id, total in rows}


def serialize(
    exercise: Exercise,
    topic: Topic,
    subject: Subject,
    attempts: int,
    warning: str | None = None,
) -> ContentExerciseResponse:
    return ContentExerciseResponse(
        id=exercise.id,
        topic_id=topic.id,
        topic_name=topic.name,
        subject_id=subject.id,
        subject_name=subject.name,
        grade=subject.grade,
        statement=exercise.statement,
        difficulty=exercise.difficulty,
        explanation=exercise.explanation,
        is_ai_generated=exercise.is_ai_generated,
        is_active=exercise.is_active,
        attempts_count=attempts,
        created_at=exercise.created_at,
        options=[
            ContentOptionResponse(
                id=o.id,
                option_text=o.option_text,
                order_number=o.order_number,
                is_correct=o.is_correct,
            )
            for o in sorted(exercise.options, key=lambda o: o.order_number)
        ],
        warning=warning,
    )


def same_subject_warning(
    db: Session, topic: Topic, statement: str
) -> str | None:
    key = normalized_statement(statement)
    rows = db.execute(
        select(Exercise.statement, Topic.name)
        .join(Topic, Topic.id == Exercise.topic_id)
        .where(
            Topic.subject_id == topic.subject_id,
            Topic.id != topic.id,
            Exercise.is_active.is_(True),
        )
    ).all()
    for text, topic_name in rows:
        if normalized_statement(text) == key:
            return (
                "Existe una pregunta con el mismo enunciado en otro tema "
                f"de la materia: «{topic_name}»."
            )
    return None


@router.get("/catalog", response_model=list[ContentSubjectCatalog])
def get_content_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_manager),
):
    allowed = assigned_subject_ids(db, current_user)
    subjects_query = select(Subject).order_by(Subject.grade, Subject.name)
    if allowed is not None:
        subjects_query = subjects_query.where(Subject.id.in_(allowed or {0}))
    subjects = db.scalars(subjects_query).all()
    if not subjects:
        return []
    topics = db.scalars(
        select(Topic)
        .where(
            Topic.subject_id.in_([s.id for s in subjects]),
            Topic.is_active.is_(True),
        )
        .order_by(Topic.order_number, Topic.id)
    ).all()
    counts = {
        (topic_id, is_active): total
        for topic_id, is_active, total in db.execute(
            select(
                Exercise.topic_id,
                Exercise.is_active,
                func.count(Exercise.id),
            )
            .where(Exercise.topic_id.in_([t.id for t in topics] or [0]))
            .group_by(Exercise.topic_id, Exercise.is_active)
        ).all()
    }
    return [
        ContentSubjectCatalog(
            id=subject.id,
            name=subject.name,
            grade=subject.grade,
            topics=[
                ContentTopicCatalog(
                    id=topic.id,
                    name=topic.name,
                    order_number=topic.order_number,
                    active_exercises=counts.get((topic.id, True), 0),
                    inactive_exercises=counts.get((topic.id, False), 0),
                )
                for topic in topics
                if topic.subject_id == subject.id
            ],
        )
        for subject in subjects
    ]


@router.get("/exercises", response_model=ContentExerciseList)
def list_content_exercises(
    topic_id: int | None = Query(default=None, gt=0),
    subject_id: int | None = Query(default=None, gt=0),
    grade: int | None = Query(default=None, ge=9, le=11),
    difficulty: str | None = Query(default=None, pattern="^(easy|medium|hard)$"),
    is_active: bool | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_manager),
):
    allowed = assigned_subject_ids(db, current_user)
    if topic_id is not None:
        topic = db.get(Topic, topic_id)
        if topic is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tema no encontrado",
            )
        authorize_subject(db, current_user, topic.subject_id)
    if (
        subject_id is not None
        and allowed is not None
        and subject_id not in allowed
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes consultar materias asignadas",
        )

    base = (
        select(Exercise, Topic, Subject)
        .join(Topic, Topic.id == Exercise.topic_id)
        .join(Subject, Subject.id == Topic.subject_id)
    )
    if allowed is not None:
        base = base.where(Subject.id.in_(allowed or {0}))
    if topic_id is not None:
        base = base.where(Topic.id == topic_id)
    if subject_id is not None:
        base = base.where(Subject.id == subject_id)
    if grade is not None:
        base = base.where(Subject.grade == grade)
    if difficulty is not None:
        base = base.where(Exercise.difficulty == difficulty)
    if is_active is not None:
        base = base.where(Exercise.is_active.is_(is_active))
    if q and q.strip():
        escaped = (
            q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        base = base.where(Exercise.statement.ilike(f"%{escaped}%", escape="\\"))

    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.execute(
        base.options(selectinload(Exercise.options))
        .order_by(Subject.grade, Subject.name, Topic.order_number, Exercise.id)
        .limit(limit)
        .offset(offset)
    ).all()
    attempts = count_attempts(db, [row[0].id for row in rows])
    return ContentExerciseList(
        items=[
            serialize(exercise, topic, subject, attempts.get(exercise.id, 0))
            for exercise, topic, subject in rows
        ],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/exercises",
    response_model=ContentExerciseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_content_exercise(
    data: ContentExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_manager),
):
    topic = load_topic_for_update(db, data.topic_id)
    authorize_subject(db, current_user, topic.subject_id)
    if find_duplicate(db, topic.id, data.statement) is not None:
        raise duplicate_conflict()
    try:
        exercise = Exercise(
            topic_id=topic.id,
            statement=data.statement,
            difficulty=data.difficulty,
            explanation=(data.explanation or "").strip() or None,
            is_ai_generated=False,
            is_active=True,
        )
        exercise.options = build_options(data.options)
        db.add(exercise)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(exercise)
    subject = db.get(Subject, topic.subject_id)
    return serialize(
        exercise,
        topic,
        subject,
        0,
        same_subject_warning(db, topic, exercise.statement),
    )


@router.patch(
    "/exercises/{exercise_id}",
    response_model=ContentExerciseResponse,
)
def update_content_exercise(
    exercise_id: int,
    data: ContentExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_manager),
):
    exercise = load_exercise(db, exercise_id)
    topic = db.get(Topic, exercise.topic_id)
    authorize_subject(db, current_user, topic.subject_id)
    changes = data.model_dump(exclude_unset=True)
    attempts = count_attempts(db, [exercise.id]).get(exercise.id, 0)

    semantic = False
    if "statement" in changes and changes["statement"] != exercise.statement:
        semantic = True
    if "options" in changes:
        current = [
            (o.option_text, o.is_correct)
            for o in sorted(exercise.options, key=lambda o: o.order_number)
        ]
        proposed = [
            (o["option_text"], o["is_correct"]) for o in changes["options"]
        ]
        if current != proposed:
            semantic = True
    if semantic and attempts > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La pregunta ya tiene intentos registrados: no se puede "
                "modificar su enunciado ni sus opciones. Crea una nueva "
                "versión para conservar el historial."
            ),
        )
    if (
        "statement" in changes
        and semantic
        and find_duplicate(db, topic.id, changes["statement"], exercise.id)
    ):
        raise duplicate_conflict()
    if "options" in changes and len(exercise.options) != 4:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La pregunta no tiene cuatro opciones; crea una nueva versión.",
        )

    try:
        if "statement" in changes:
            exercise.statement = changes["statement"]
        if "difficulty" in changes:
            exercise.difficulty = changes["difficulty"]
        if "explanation" in changes:
            exercise.explanation = (changes["explanation"] or "").strip() or None
        if "options" in changes and semantic:
            for stored, new in zip(
                sorted(exercise.options, key=lambda o: o.order_number),
                changes["options"],
            ):
                stored.option_text = new["option_text"]
                stored.is_correct = new["is_correct"]
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(exercise)
    subject = db.get(Subject, topic.subject_id)
    return serialize(exercise, topic, subject, attempts)


@router.patch(
    "/exercises/{exercise_id}/status",
    response_model=ContentExerciseResponse,
)
def update_content_exercise_status(
    exercise_id: int,
    data: ContentExerciseStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_manager),
):
    exercise = load_exercise(db, exercise_id)
    topic = db.get(Topic, exercise.topic_id)
    authorize_subject(db, current_user, topic.subject_id)
    if data.is_active and not exercise.is_active:
        if not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El tema está inactivo",
            )
        if find_duplicate(db, topic.id, exercise.statement, exercise.id):
            raise duplicate_conflict()
    try:
        exercise.is_active = data.is_active
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(exercise)
    subject = db.get(Subject, topic.subject_id)
    attempts = count_attempts(db, [exercise.id]).get(exercise.id, 0)
    return serialize(exercise, topic, subject, attempts)


@router.post(
    "/exercises/{exercise_id}/new-version",
    response_model=ContentExerciseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_content_exercise_version(
    exercise_id: int,
    data: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_manager),
):
    old = load_exercise(db, exercise_id)
    topic = load_topic_for_update(db, old.topic_id)
    authorize_subject(db, current_user, topic.subject_id)
    if find_duplicate(db, topic.id, data.statement, old.id):
        raise duplicate_conflict()
    try:
        new = Exercise(
            topic_id=topic.id,
            statement=data.statement,
            difficulty=data.difficulty,
            explanation=(data.explanation or "").strip() or None,
            is_ai_generated=False,
            is_active=True,
        )
        new.options = build_options(data.options)
        db.add(new)
        old.is_active = False
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new)
    subject = db.get(Subject, topic.subject_id)
    return serialize(new, topic, subject, 0)
