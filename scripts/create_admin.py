from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.user import User


def create_admin():
    db = SessionLocal()

    try:
        name = input("Nombre del administrador: ").strip()
        email = input("Correo del administrador: ").strip().lower()
        password = getpass("Contraseña: ")
        confirm_password = getpass("Confirmar contraseña: ")

        if not name:
            print("El nombre es obligatorio.")
            return

        if not email:
            print("El correo es obligatorio.")
            return

        if len(password) < 8:
            print("La contraseña debe tener mínimo 8 caracteres.")
            return

        if password != confirm_password:
            print("Las contraseñas no coinciden.")
            return

        existing_user = db.scalar(
            select(User).where(
                User.email == email
            )
        )

        if existing_user:
            print("Ya existe un usuario con ese correo.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print()
        print("Administrador creado correctamente.")
        print(f"ID: {admin.id}")
        print(f"Nombre: {admin.name}")
        print(f"Correo: {admin.email}")
        print(f"Rol: {admin.role}")

    except Exception as error:
        db.rollback()
        print(f"Error al crear administrador: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()