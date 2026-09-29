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
    existing_user = db.scalar(
        select(User).where(
            User.email == data.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya pertenece a un usuario registrado",
        )

    pending_request = db.scalar(
        select(RegistrationRequest).where(
            RegistrationRequest.email == data.email,
            RegistrationRequest.status == "pending",
        )
    )

    if pending_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una solicitud pendiente para este correo",
        )

    registration_request = RegistrationRequest(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        requested_role=data.requested_role,
        grade=data.grade,
        status="pending",
    )

    db.add(registration_request)

    try:
        db.commit()
        db.refresh(registration_request)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear la solicitud de registro",
        )

    return registration_request

    # El registro público nunca puede crear administradores.
    if data.role not in ALLOWED_PUBLIC_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no permitido para registro público",
        )


    existing_user = db.scalar(
        select(User).where(
            User.email == data.email,
        )
    )


    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado",
        )


    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(
            data.password,
        ),
        role=data.role,
    )


    db.add(user)
    db.commit()
    db.refresh(user)


    return user


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
    })


    return {
        "access_token": token,
        "token_type": "bearer",
    }