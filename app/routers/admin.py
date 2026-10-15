from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_admin
from app.models.registration_request import RegistrationRequest
from app.models.user import User
from app.schemas.registration_request import (RegistrationRequestResponse, RegistrationReviewResponse)

from datetime import datetime, timezone


from app.models.student_profile import StudentProfile
from app.models.tutor import Tutor


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/registration-requests",
    response_model=list[RegistrationRequestResponse],
)
def get_registration_requests(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    requests = db.scalars(
        select(RegistrationRequest)
        .where(
            RegistrationRequest.status == "pending"
        )
        .order_by(
            RegistrationRequest.created_at.asc()
        )
    ).all()

    return requests

@router.patch(
    "/registration-requests/{request_id}/approve",
    response_model=RegistrationReviewResponse,
)
def approve_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    registration_request = db.get(
        RegistrationRequest,
        request_id,
    )

    if registration_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada",
        )

    if registration_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue procesada",
        )

    existing_user = db.scalar(
        select(User).where(
            User.email == registration_request.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con este correo",
        )

    try:
        user = User(
            name=registration_request.name,
            email=registration_request.email,
            password_hash=registration_request.password_hash,
            role=registration_request.requested_role,
            is_active=True,
        )

        db.add(user)

        # Necesitamos el ID generado por PostgreSQL
        # antes de crear el perfil relacionado.
        db.flush()

        if registration_request.requested_role == "student":
            student_profile = StudentProfile(
                user_id=user.id,
                grade=registration_request.grade,
            )

            db.add(student_profile)

        elif registration_request.requested_role == "tutor":
            tutor = Tutor(
                user_id=user.id,
            )

            db.add(tutor)

        registration_request.status = "approved"
        registration_request.reviewed_at = datetime.now(
            timezone.utc
        )
        registration_request.reviewed_by = current_admin.id

        db.commit()

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible aprobar la solicitud",
        )

    return {
        "id": registration_request.id,
        "status": registration_request.status,
        "message": "Solicitud aprobada correctamente",
    }

@router.patch(
    "/registration-requests/{request_id}/reject",
    response_model=RegistrationReviewResponse,
)
def reject_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    registration_request = db.get(
        RegistrationRequest,
        request_id,
    )

    if registration_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada",
        )

    if registration_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue procesada",
        )

    registration_request.status = "rejected"
    registration_request.reviewed_at = datetime.now(
        timezone.utc
    )
    registration_request.reviewed_by = current_admin.id

    db.commit()

    return {
        "id": registration_request.id,
        "status": registration_request.status,
        "message": "Solicitud rechazada correctamente",
    }


@router.get(
    "/registration-requests/history",
    response_model=list[RegistrationRequestResponse],
)
def get_registration_requests_history(
    request_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Consulta el historial de solicitudes.

    Filtros:
    - pending
    - approved
    - rejected

    Sin filtro devuelve todas las solicitudes.
    """

    allowed_statuses = {
        "pending",
        "approved",
        "rejected",
    }

    if (
        request_status is not None
        and request_status not in allowed_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Estado de solicitud no válido",
        )

    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Paginación inválida",
        )

    query = select(RegistrationRequest)

    if request_status is not None:
        query = query.where(
            RegistrationRequest.status == request_status
        )

    query = (
        query
        .order_by(
            RegistrationRequest.created_at.desc(),
            RegistrationRequest.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(query).all()
