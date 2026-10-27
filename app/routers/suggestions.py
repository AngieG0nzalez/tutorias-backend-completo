from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.suggestion import Suggestion
from app.models.user import User
from app.schemas.suggestion import (
    AdminSuggestionList,
    AdminSuggestionResponse,
    SuggestionAdminUpdate,
    SuggestionCreate,
    SuggestionList,
    SuggestionResponse,
)
from app.services.account_security import now_utc


router = APIRouter(tags=["Suggestions"])

MAX_PER_WINDOW = 5
WINDOW_MINUTES = 10


def require_author(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("student", "tutor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo estudiantes y tutores pueden enviar sugerencias",
        )
    return current_user


def to_admin(row: Suggestion, user: User) -> AdminSuggestionResponse:
    return AdminSuggestionResponse(
        id=row.id,
        category=row.category,
        subject=row.subject,
        message=row.message,
        status=row.status,
        admin_note=row.admin_note,
        created_at=row.created_at,
        updated_at=row.updated_at,
        author_name=user.name,
        author_role=user.role,
    )


@router.post(
    "/suggestions",
    response_model=SuggestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_suggestion(
    data: SuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_author),
):
    recent = db.scalar(
        select(func.count(Suggestion.id)).where(
            Suggestion.user_id == current_user.id,
            Suggestion.created_at > now_utc() - timedelta(minutes=WINDOW_MINUTES),
        )
    )
    if recent >= MAX_PER_WINDOW:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Has enviado muchas sugerencias seguidas. Intenta más tarde.",
        )
    row = Suggestion(
        user_id=current_user.id,
        category=data.category,
        subject=data.subject,
        message=data.message,
        status="new",
    )
    try:
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(row)
    return row


@router.get("/suggestions/mine", response_model=SuggestionList)
def list_my_suggestions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_author),
):
    where = Suggestion.user_id == current_user.id
    total = db.scalar(select(func.count(Suggestion.id)).where(where))
    items = db.scalars(
        select(Suggestion)
        .where(where)
        .order_by(Suggestion.created_at.desc(), Suggestion.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return SuggestionList(
        items=items, total=total or 0, limit=limit, offset=offset
    )


@router.get("/admin/suggestions", response_model=AdminSuggestionList)
def list_admin_suggestions(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(new|in_review|resolved|rejected)$",
    ),
    category: str | None = Query(
        default=None, pattern="^(content|usability|bug|other)$"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    base = select(Suggestion, User).join(User, User.id == Suggestion.user_id)
    if status_filter:
        base = base.where(Suggestion.status == status_filter)
    if category:
        base = base.where(Suggestion.category == category)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.execute(
        base.order_by(Suggestion.created_at.desc(), Suggestion.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return AdminSuggestionList(
        items=[to_admin(row, user) for row, user in rows],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/admin/suggestions/{suggestion_id}",
    response_model=AdminSuggestionResponse,
)
def update_admin_suggestion(
    suggestion_id: int,
    data: SuggestionAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes indicar el estado o una nota",
        )
    row = db.scalar(
        select(Suggestion)
        .where(Suggestion.id == suggestion_id)
        .with_for_update()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sugerencia no encontrada",
        )
    try:
        if "status" in changes:
            row.status = changes["status"]
        if "admin_note" in changes:
            row.admin_note = changes["admin_note"]
        row.updated_at = func.now()
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(row)
    return to_admin(row, db.get(User, row.user_id))
