from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.database.connection import get_db

from app.models.registration_request import RegistrationRequest
from app.models.user import User

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
)

from app.schemas.registration_request import (
    RegistrationRequestCreate,
    RegistrationRequestResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


ALLOWED_PUBLIC_ROLES = {
    "student",
    "tutor",
}



@router.post(
    "/register-request",
    response_model=RegistrationRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_registration_request(
    data: RegistrationRequestCreate,
    db: Session = Depends(get_db),
):
    # 1. Normalizar el correo electrónico
    email = str(data.email).strip().lower()

    # 2. Verificar si ya existe un usuario registrado
    existing_user = db.scalar(
        select(User).where(
            User.email.ilike(email)
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya pertenece a un usuario registrado",
        )

    # 3. Verificar si existe una solicitud pendiente
    pending_request = db.scalar(
        select(RegistrationRequest).where(
            RegistrationRequest.email.ilike(email),
            RegistrationRequest.status == "pending",
        )
    )

    if pending_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una solicitud pendiente para este correo",
        )

    # 4. Crear solicitud de registro
    registration_request = RegistrationRequest(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        requested_role=data.requested_role,
        grade=data.grade,
        status="pending",
    )

    db.add(registration_request)

    # 5. Guardar solicitud en PostgreSQL
    try:
        db.commit()
        db.refresh(registration_request)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear la solicitud. Verifica si ya existe.",
        )

    # 6. Devolver solicitud sin exponer la contraseña
    return registration_request

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )


    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )


    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )


    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )


    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "sv": user.session_version,
    })


    return {
        "access_token": token,
        "token_type": "bearer",
    }