from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.ai_config import get_ai_settings
from app.database.connection import get_db
from app.dependencies.auth import require_student, require_tutor
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.student_progress import StudentProgress
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User
from app.routers.topics import get_active_tutor_for_subject
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    DraftOption,
    DraftRequest,
    DraftResponse,
    ExplanationRequest,
    ExplanationResponse,
)
from app.services import ai_tutor_service as svc
from app.services.ai_provider import AIProvider, AIProviderError, get_ai_provider
from app.services.exercise_service import find_duplicate

router = APIRouter(prefix="/ai", tags=["IA local"])

UNAVAILABLE = "La explicación de IA no está disponible en este momento"


def _rate_limit(user: User):
    if not svc.limiter.allow(user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes de IA. Espera un momento.",
        )


def _call(provider: AIProvider, system: str, user: str, *, json_format: bool, max_chars: int) -> str:
    # Sin ranuras libres se trata como proveedor no disponible, sin encolar.
    if not svc.inference_slots.acquire(blocking=False):
        raise AIProviderError("unavailable")
    try:
        return provider.chat(system, user, json_format=json_format, max_chars=max_chars)
    finally:
        svc.inference_slots.release()


@router.post("/explanations", response_model=ExplanationResponse)
def explain_attempt(
    data: ExplanationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
    provider: AIProvider = Depends(get_ai_provider),
):
    attempt = db.scalar(
        select(ExerciseAttempt).where(
            ExerciseAttempt.id == data.attempt_id,
            ExerciseAttempt.user_id == current_user.id,
        )
    )
    if attempt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intento no encontrado")
    _rate_limit(current_user)

    exercise = db.scalar(
        select(Exercise)
        .options(selectinload(Exercise.options))
        .where(Exercise.id == attempt.exercise_id)
    )
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intento no encontrado")
    topic = db.get(Topic, exercise.topic_id)
    subject = db.get(Subject, topic.subject_id) if topic else None
    level = db.scalar(
        select(StudentProgress.level).where(
            StudentProgress.user_id == current_user.id,
            StudentProgress.topic_id == exercise.topic_id,
        )
    )
    selected = next((o for o in exercise.options if o.id == attempt.selected_option_id), None)
    correct = [o for o in exercise.options if o.is_correct]

    # Solo datos académicos: sin nombre, correo ni identificadores de usuario.
    context = {
        "grado": subject.grade if subject else None,
        "materia": subject.name if subject else None,
        "tema": topic.name if topic else None,
        "enunciado": exercise.statement,
        "opciones": [o.option_text for o in exercise.options],
        "opcion_elegida": selected.option_text if selected else None,
        "opcion_correcta": [o.option_text for o in correct],
        "resultado": "correcto" if attempt.is_correct else "incorrecto",
        "nivel_de_dominio_del_tema": level,
        "explicacion_revisada": exercise.explanation,
    }
    settings = get_ai_settings()
    curated = (exercise.explanation or "").strip()

    def fallback():
        if curated:
            return ExplanationResponse(
                attempt_id=attempt.id,
                exercise_id=exercise.id,
                explanation=curated,
                source="curated",
                model=None,
                is_fallback=True,
            )
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, UNAVAILABLE)

    try:
        raw = _call(
            provider,
            svc.EXPLANATION_SYSTEM,
            svc.build_explanation_prompt(context),
            json_format=False,
            max_chars=settings.max_explanation_chars,
        )
    except AIProviderError:
        return fallback()
    text = svc.clean_explanation(raw, settings.max_explanation_chars)
    if text is None:
        return fallback()
    return ExplanationResponse(
        attempt_id=attempt.id,
        exercise_id=exercise.id,
        explanation=text,
        source="ollama",
        model=provider.model or None,
        is_fallback=False,
    )


@router.post("/exercise-drafts", response_model=DraftResponse)
def generate_draft(
    data: DraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tutor),
    provider: AIProvider = Depends(get_ai_provider),
):
    topic = db.get(Topic, data.topic_id)
    if topic is None or not topic.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tema no encontrado")
    get_active_tutor_for_subject(db, current_user, topic.subject_id)
    subject = db.get(Subject, topic.subject_id)
    _rate_limit(current_user)

    settings = get_ai_settings()
    context = {
        "grado": subject.grade,
        "materia": subject.name,
        "tema": topic.name,
        "dificultad": data.difficulty,
        "objetivo": data.objective,
    }
    draft = None
    # Un reintento acotado solo si el borrador resulta duplicado.
    for attempt_number in range(2):
        try:
            raw = _call(
                provider,
                svc.DRAFT_SYSTEM,
                svc.build_draft_prompt(context),
                json_format=True,
                max_chars=settings.max_draft_chars,
            )
        except AIProviderError as exc:
            if exc.kind == "invalid":
                raise HTTPException(status.HTTP_502_BAD_GATEWAY, "El modelo devolvió un borrador inválido. Inténtalo de nuevo.")
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "La IA no está disponible en este momento")
        parsed = svc.parse_draft(raw)
        if parsed is None:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "El modelo devolvió un borrador inválido. Inténtalo de nuevo.")
        if find_duplicate(db, topic.id, parsed.statement) is None:
            draft = parsed
            break
    if draft is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El borrador generado ya existe en este tema. Inténtalo de nuevo.")

    return DraftResponse(
        topic_id=topic.id,
        grade=subject.grade,
        difficulty=data.difficulty,
        statement=draft.statement,
        explanation=draft.explanation,
        options=[DraftOption(option_text=o.option_text, is_correct=o.is_correct) for o in draft.options],
        warning=svc.DRAFT_WARNING,
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    current_user: User = Depends(require_student),
    provider: AIProvider = Depends(get_ai_provider),
):
    if data.messages[-1].role != "user":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El último mensaje debe ser del estudiante")
    _rate_limit(current_user)
    settings = get_ai_settings()
    history = [{"rol": m.role, "texto": m.content} for m in data.messages]
    unavailable = HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El chat de IA no está disponible en este momento")
    try:
        raw = _call(
            provider,
            svc.CHAT_SYSTEM,
            svc.build_chat_prompt(history),
            json_format=False,
            max_chars=settings.max_explanation_chars,
        )
    except AIProviderError:
        raise unavailable
    text = svc.clean_explanation(raw, settings.max_explanation_chars)
    if text is None:
        raise unavailable
    return ChatResponse(reply=text, model=provider.model or None)
