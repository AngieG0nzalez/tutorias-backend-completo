# Tutorías Backend

Backend para una plataforma de tutorías construido con:

- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Supabase
- Psycopg 3
- JWT

## 1. Crear y activar entorno virtual

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

## 3. Configurar variables

Copia `.env.example` como `.env` y reemplaza los valores por los de Supabase.

Nunca subas `.env` a Git.

## 4. Ejecutar

```powershell
python -m uvicorn app.main:app --reload
```

## 5. Swagger

Abre:

http://127.0.0.1:8000/docs

## Endpoints principales

- `POST /auth/register`
- `POST /auth/login`
- `GET /users`
- `GET /users/me`
- `GET /subjects`
- `POST /subjects`
- `GET /tutors`
- `POST /tutors`
- `GET /classes`
- `POST /classes`
- `GET /enrollments`
- `POST /enrollments`
- `GET /messages`
- `POST /messages`
- `GET /reviews`
- `POST /reviews`

## Nota sobre tablas

Este proyecto asume que las tablas ya existen en Supabase/PostgreSQL y coinciden
con los modelos SQLAlchemy. No usa `Base.metadata.create_all()`.

Más adelante se recomienda agregar Alembic para migraciones.
