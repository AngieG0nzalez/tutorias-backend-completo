# Nexo - Tutorías Backend

Backend de **Nexo**, una plataforma educativa de tutorías y aprendizaje de matemáticas para estudiantes de grados 9°, 10° y 11°.

El backend está construido con:

- Python 3.12
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Supabase
- Psycopg 3
- JWT
- Pydantic

---

## 1. Requisitos

Antes de ejecutar el proyecto necesitas:

- Python 3.12
- Git
- Una cuenta/proyecto de Supabase
- Visual Studio Code (opcional)
- Bruno (opcional, para probar la API)

Comprueba tu versión de Python:

```bash
python --version
```

El proyecto utiliza **Python 3.12**.

---

# Instalación en Windows - PowerShell

## 2. Crear el entorno virtual

Desde la raíz del proyecto:

```powershell
python -m venv .venv
```

Si tienes varias versiones de Python instaladas, puedes usar:

```powershell
py -3.12 -m venv .venv
```

## 3. Activar el entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Comprueba la versión:

```powershell
python --version
```

Debe mostrar Python 3.12.x.

---

# Instalación en macOS - Zsh

## 2. Crear el entorno virtual

El proyecto utiliza Python 3.12.

Si Python 3.12 fue instalado mediante Homebrew:

```zsh
python3.12 -m venv .venv
```

En Mac con Apple Silicon, también puedes utilizar explícitamente:

```zsh
/opt/homebrew/bin/python3.12 -m venv .venv
```

## 3. Activar el entorno virtual

```zsh
source .venv/bin/activate
```

Comprueba:

```zsh
python --version
which python
```

Debe aparecer Python 3.12.x y el ejecutable debe pertenecer a:

```text
.../tutorias-backend-completo/.venv/bin/python
```

> No copies el `.venv` entre Windows y macOS. Cada sistema debe crear su propio entorno virtual.

---

# 4. Instalar dependencias

Con el entorno virtual activo:

## Windows PowerShell

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## macOS Zsh

```zsh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

El proyecto utiliza **Psycopg 3** para conectarse a PostgreSQL.

---

# 5. Configurar variables de entorno

Copia:

```text
.env.example
```

como:

```text
.env
```

y configura las variables correspondientes.

Ejemplo:

```env
user=
password=
host=
port=5432
dbname=postgres

secret_key=
algorithm=HS256
access_token_expire_minutes=60
```

Los valores de conexión deben corresponder al proyecto de Supabase.

> Nunca subas `.env` a GitHub.

El archivo `.gitignore` debe contener `.env`.

---

# 6. Ejecutar el backend

Con el entorno virtual activo:

## Windows PowerShell

```powershell
python -m uvicorn app.main:app --reload
```

## macOS Zsh

```zsh
python -m uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

---

# 7. Verificar conexión

Puedes comprobar el estado del backend y PostgreSQL desde:

```text
http://127.0.0.1:8000/health
```

La respuesta esperada es:

```json
{
  "status": "ok",
  "database": "connected"
}
```

---

# 8. Swagger / documentación de la API

FastAPI genera automáticamente la documentación Swagger.

Abre:

```text
http://127.0.0.1:8000/docs
```

---

# Endpoints principales

## Autenticación

```text
POST /auth/register
POST /auth/login
```

> El flujo de registro se encuentra en evolución hacia un sistema de solicitudes y aprobación administrativa.

## Usuarios

```text
GET /users
GET /users/me
```

## Materias

```text
GET  /subjects
POST /subjects
```

## Temas de matemáticas

```text
GET /topics
GET /topics?subject_id={subject_id}
GET /topics/{topic_id}/exercises
```

Ejemplo:

```text
GET /topics?subject_id=1
GET /topics/4/exercises
```

## Tutores

```text
GET  /tutors
POST /tutors
```

## Clases

```text
GET  /classes
POST /classes
```

## Inscripciones

```text
GET  /enrollments
POST /enrollments
```

## Mensajes

```text
GET  /messages
POST /messages
```

## Reseñas

```text
GET  /reviews
POST /reviews
```

---

# Sistema de ejercicios adaptativos

Nexo incorpora una estructura para aprendizaje adaptativo de matemáticas.

Actualmente existen los modelos/tablas:

```text
subjects
    │
    └── topics
          │
          └── exercises
                 │
                 └── exercise_options

users
    │
    ├── exercise_attempts
    │
    └── student_progress
```

También se están incorporando:

```text
student_profiles
registration_requests
```

`student_profiles` permite almacenar información específica del estudiante, como el grado:

```text
9
10
11
```

`registration_requests` permitirá manejar solicitudes de inscripción antes de crear una cuenta activa.

---

# Roles

Nexo utiliza tres roles:

```text
student
tutor
admin
```

Los estudiantes y tutores podrán pasar por un proceso de inscripción y aprobación.

Los administradores no deben crearse mediante el registro público.

La creación controlada de administradores se realizará mediante:

```text
scripts/create_admin.py
```

---

# Seguridad

La API utiliza JWT para autenticación.

El cliente debe enviar el token mediante:

```text
Authorization: Bearer <token>
```

FastAPI obtiene el usuario autenticado a partir del `sub` contenido en el JWT.

Las contraseñas nunca se almacenan directamente. Se almacena únicamente su hash.

---

# Base de datos

La base de datos utiliza PostgreSQL alojado en Supabase.

Este proyecto asume que las tablas ya existen en PostgreSQL y coinciden con los modelos de SQLAlchemy.

Por este motivo actualmente **no se utiliza**:

```python
Base.metadata.create_all()
```

Las modificaciones del esquema se realizan explícitamente en PostgreSQL/Supabase.

Más adelante se recomienda incorporar **Alembic** para administrar las migraciones de base de datos.

---

# Estructura principal

```text
tutorias-backend-completo/
│
├── app/
│   ├── core/
│   ├── database/
│   ├── dependencies/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── main.py
│
├── scripts/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Detener el servidor

Presiona:

```text
Ctrl + C
```

---

# Desactivar el entorno virtual

Tanto en Windows PowerShell como en macOS Zsh:

```bash
deactivate
```

---

# Estado actual del proyecto

El backend se encuentra en desarrollo.

Roadmap actual:

```text
01. Registro y aprobación
02. Script create_admin.py
03. student_profiles
04. registration_requests
05. Revisar/cerrar modelos SQLAlchemy
06. Roles y permisos FastAPI
07. Attempts
08. Progress
09. Algoritmo adaptativo
10. Rutas Admin
11. Rutas Tutor
12. Terminar CRUD/backend existente
13. Pruebas Bruno
14. Backend Render estable

15. Login React mejorado
16. Solicitud de inscripción
17. Sesión y rutas protegidas
18. Panel Student
19. Panel Admin
20. Panel Tutor
21. Conectar frontend con FastAPI
22. Frontend en Vercel

23. IA local
24. Pruebas IA
25. Comparativa de modelos/proveedores
26. Elegir IA de producción
27. Integración IA de producción
28. Despliegue completo
29. Pruebas end-to-end
30. Preparación de presentación
```