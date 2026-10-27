# Nexo — Backend de tutorías de matemáticas

API REST de **Nexo**, plataforma educativa de tutorías y aprendizaje adaptativo para estudiantes de grados **9.º, 10.º y 11.º**.

## Tecnologías

- **Python 3.12** y **FastAPI**
- **SQLAlchemy 2**, **Pydantic** y **Psycopg 3**
- **PostgreSQL en Supabase**
- **JWT** para autenticación y permisos por rol (`student`, `tutor`, `admin`)
- **Bruno** para pruebas de API
- **Render** para el despliegue del backend
- **Brevo** para correos de recuperación y confirmación (según configuración del proyecto)

## 1. Requisitos

- Python **3.12.x**
- Git
- Acceso a la base de datos PostgreSQL de Supabase
- Archivo `.env` con las variables necesarias (consulta `.env.example`)
- Opcional: VS Code y Bruno

> Crea un entorno virtual nuevo en cada sistema operativo. **Nunca copies `.venv` entre Windows, macOS y Linux.**

## 2. Descargar el proyecto

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd tutorias-backend-completo
```

Si ya tienes el repositorio, entra en su carpeta y actualízalo mediante `git pull` cuando corresponda.

## 3. Instalar y ejecutar en Windows (PowerShell)

Comprueba Python 3.12:

```powershell
py -3.12 --version
```

Crea y activa el entorno:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Si PowerShell bloquea la activación, puedes permitirla **solo en la sesión actual**:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Instala dependencias y ejecuta:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edita .env antes de continuar
python -m uvicorn app.main:app --reload
```

Si prefieres no activar el entorno, puedes utilizar directamente `.\.venv\Scripts\python.exe` en los comandos.

## 4. Instalar y ejecutar en macOS (Zsh)

Si todavía no tienes Python 3.12 y usas Homebrew:

```zsh
brew install python@3.12
```

Desde la raíz del proyecto:

```zsh
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
python --version
which python
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Edita .env antes de continuar
python -m uvicorn app.main:app --reload
```

En Mac Apple Silicon, Homebrew suele instalar Python en `/opt/homebrew/bin/python3.12`. En Intel la ruta puede ser diferente; usa `command -v python3.12` para localizarlo.

## 5. Instalar y ejecutar en Ubuntu y Linux Mint (Bash)

Primero comprueba si Python 3.12 está instalado:

```bash
python3.12 --version
```

Si ya está instalado, asegúrate de tener el soporte de entornos virtuales de esa versión. En distribuciones que ofrecen el paquete:

```bash
sudo apt update
sudo apt install python3.12-venv
```

> La disponibilidad de `python3.12` y `python3.12-venv` depende de la versión de Ubuntu o Linux Mint y sus repositorios. **No cambies el Python predeterminado del sistema** para instalar Nexo. Si el paquete no existe, instala Python 3.12 mediante un método compatible con tu distribución (por ejemplo, `pyenv`) antes de continuar.

Desde la raíz del proyecto:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
which python
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Edita .env antes de continuar
python -m uvicorn app.main:app --reload
```

## 6. Variables de entorno

Copia `.env.example` a `.env` y completa las variables que **realmente consume tu código**. La configuración original del proyecto incluye:

```dotenv
user=
password=
host=
port=5432
dbname=postgres

secret_key=
algorithm=HS256
access_token_expire_minutes=60

SMTP_HOST=HOST_DEL_PROVEEDOR
SMTP_PORT=587
SMTP_USER=USUARIO_SMTP
SMTP_PASSWORD=CONTRASENA_SMTP
SMTP_FROM="Nexo <remitente@dominio-autorizado.com>"
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

- `FRONTEND_URL`: base de los enlaces de los correos (recuperación de clave y cambio de correo).
- `CORS_ORIGINS`: orígenes permitidos separados por coma, sin barra final (ej. `https://mi-front.vercel.app,http://localhost:5173`). Si no se define, se usa `http://localhost:5173`.

`.env.example` documenta todos los nombres; deja vacíos o con marcadores todos los secretos.

Para PostgreSQL alojado en Supabase, utiliza el host, puerto, usuario, contraseña y nombre de base de datos de tu proyecto. La conexión debe usar SSL cuando lo requiera Supabase.

**Seguridad:**

- No publiques `.env`, contraseñas, claves JWT ni tokens.
- Incluye `.env` y `.venv/` en `.gitignore`.
- Configura los secretos de producción en **Render → Environment**, nunca dentro del repositorio.
- No compartas las credenciales de Supabase entre proyectos distintos.

## 7. Comprobar el funcionamiento local

Con el servidor iniciado:

- API: http://127.0.0.1:8000
- Salud de la API y base de datos: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json

Respuesta esperada de `/health`, si el endpoint mantiene el contrato original:

```json
{
  "status": "ok",
  "database": "connected"
}
```

La respuesta real puede variar si se ha actualizado el endpoint. Compruébala en Swagger.

## 8. Módulos y endpoints principales

Los métodos y rutas siguientes reflejan las funcionalidades trabajadas durante el desarrollo. **Consulta `/docs` como fuente de verdad del despliegue actual** para conocer todos los métodos, parámetros y esquemas.

| Módulo | Rutas representativas |
| --- | --- |
| Autenticación | `POST /auth/register`, `POST /auth/login`, `POST /auth/forgot-password`, `POST /auth/reset-password` |
| Cuenta | `PATCH /account/password`, `POST /account/email-change`, `POST /account/email-confirm` |
| Usuarios | `/users`, `/users/me` |
| Solicitudes administrativas | `/admin/registration-requests/history` |
| Administración de usuarios | `GET /admin/users`, `GET /admin/users/{user_id}`, `PATCH /admin/users/{user_id}`, `PATCH /admin/users/{user_id}/status` |
| Asignación tutor–materia (admin) | `GET/POST /admin/tutors/{tutor_id}/subjects`, `DELETE /admin/tutors/{tutor_id}/subjects/{subject_id}` (409 si hay clases programadas) |
| Tutores | `/tutors`, `GET /tutors/directory`, `/tutor-panel/me`, `/tutor-panel/classes`, `/tutor-panel/subjects`, `/tutor-panel/summary` |
| Materias y temas | `/subjects`, `/topics`, `POST /topics`, `PATCH /topics/{id}`, `GET /topics/{topic_id}/exercises` |
| Preguntas por tema (tutor) | `GET /topics/{id}/exercises/manage`, `POST /topics/{id}/exercises` (409 si duplicada), `DELETE` (baja lógica) |
| Banco de preguntas | `GET /content/catalog`, `GET/POST /content/exercises`, `PATCH /content/exercises/{id}`, `PATCH .../status`, `POST .../new-version` (admin o tutor con la materia asignada) |
| Sugerencias | `POST /suggestions`, `GET /suggestions/mine`, `GET /admin/suggestions`, `PATCH /admin/suggestions/{id}` (límite 5 por 10 min → 429) |
| Clases e inscripciones | `/classes` (`POST`/`PATCH` propietario o admin), `/enrollments` |
| Mensajes y reseñas | `/messages`, `GET /messages/contacts`, `/reviews` |
| Intentos | `POST /attempts`, `GET /attempts/me` |
| Progreso | `GET /progress/me`, `GET /progress/me/{topic_id}` |
| Adaptación | `GET /adaptive/topics/{topic_id}/next` |

### Modelo de aprendizaje adaptativo

```text
subjects
  └── topics
       └── exercises
            └── exercise_options

users
  ├── exercise_attempts
  └── student_progress
```

El sistema registra intentos, calcula progreso por tema y recomienda ejercicios según el desempeño del estudiante.

### Roles y seguridad

- `student`: consulta y practica con sus propios datos.
- `tutor`: accede a su panel, gestiona clases, temas y preguntas de las materias que tiene asignadas.
- `admin`: administra usuarios, asignaciones tutor–materia, banco de preguntas y sugerencias.

Las preguntas de práctica nunca incluyen `is_correct`; solo se revela en la respuesta a un intento y en los endpoints de gestión (tutor/admin). Las preguntas con historial no se borran: se retiran (`is_active=false`) o se versionan.

Los endpoints protegidos requieren:

```http
Authorization: Bearer <JWT>
```

El backend valida el usuario autenticado, sus permisos y el estado de su cuenta. El cambio de contraseña invalida tokens anteriores mediante el mecanismo de versión de sesión implementado en el proyecto.

## 9. Base de datos y migraciones

La base de datos está en Supabase PostgreSQL y se consulta mediante SQLAlchemy y Psycopg 3.

El proyecto original **no utiliza** `Base.metadata.create_all()` y presupone que las tablas existen y coinciden con los modelos. Las modificaciones del esquema se han realizado explícitamente en PostgreSQL/Supabase.

Las migraciones manuales están en `migrations/`:

- `001_create_suggestions.sql` (tabla `suggestions`) y su `001_create_suggestions_rollback.sql`.

Se aplican a mano en el SQL Editor de Supabase, tras un backup. Nunca ejecutes el rollback sin revisar los datos.

Antes de producción, verifica que los cambios recientes de cuentas, tokens y auditoría estén aplicados. **Alembic** queda como mejora futura para versionar migraciones; no lo ejecutes sin configurarlo previamente.

## 10. Pruebas automáticas y con Bruno

Pruebas focalizadas (no requieren base de datos):

```bash
pip install pytest
python -m pytest tests -q
```

Cubren: ausencia de `is_correct` en práctica, validación de 4 opciones / una correcta, rutas duplicadas, dependencias de autenticación y CORS configurable.

### Bruno

1. Importa o abre la colección de Bruno del proyecto.
2. Selecciona el entorno local o Render.
3. Configura `baseUrl` y las variables de autenticación necesarias.
4. Ejecuta el login del rol correspondiente.
5. Verifica autenticación, permisos, intentos, progreso, adaptación y cuentas.
6. No compartas tokens, contraseñas ni correos personales en capturas.

La colección debe apuntar a `http://127.0.0.1:8000` en local o a la URL pública de Render en producción.

## 11. Despliegue en Render

Servicio existente:

**https://tutorias-backend-completo.onrender.com/**

Para actualizarlo:

1. Sube los cambios a la rama vinculada con Render.
2. En el panel de Render, abre el servicio web existente.
3. Comprueba la rama, la versión de Python y las variables de entorno.
4. Verifica los comandos de compilación y arranque:

**Build Command:**

```bash
pip install -r requirements.txt
```

**Start Command:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Despliega y revisa los logs de instalación, inicio y conexión.
6. Comprueba `/health`, `/docs` y las pruebas de Bruno contra Render.

### Python 3.12 en Render

Fija explícitamente la versión compatible con tu proyecto mediante el mecanismo que admita tu configuración de Render (por ejemplo, una variable `PYTHON_VERSION` o el archivo de versión reconocido por Render). **Verifica en los logs que realmente se utiliza Python 3.12.x.**

### Correo transaccional

Si el servicio está en **Render Free**, comprueba la conectividad antes de confiar en SMTP: los puertos salientes SMTP habituales pueden estar restringidos. Para Brevo, puede ser necesario utilizar su API HTTPS en lugar de SMTP. La prueba local de envío de correo no demuestra por sí sola que funcione en Render.

### CORS

Define `CORS_ORIGINS` en Render con el dominio HTTPS real del frontend (y `FRONTEND_URL` con la misma URL). No utilices `*` con credenciales en producción.

## 12. Estructura principal

```text
tutorias-backend-completo/
├── app/
│   ├── core/
│   ├── database/
│   ├── dependencies/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/        # lógica adaptativa, plantillas de correo
│   ├── assets/          # logo de los correos
│   └── main.py
├── migrations/          # SQL manual para Supabase
├── tests/
├── scripts/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

`.env` y `.venv/` se crean localmente y no deben subirse a Git.

## 13. Detener el servidor y salir del entorno

Presiona **Ctrl + C** para detener Uvicorn y luego ejecuta:

```bash
deactivate
```

## 14. Roadmap del proyecto

### Backend

- [x] 01. Registro y aprobación
- [x] 02. Script `create_admin.py`
- [x] 03. `student_profiles`
- [x] 04. `registration_requests`
- [x] 05. Revisar/cerrar modelos SQLAlchemy
- [x] 06. Roles y permisos FastAPI
- [x] 07. Attempts
- [x] 08. Progress
- [x] 09. Algoritmo adaptativo
- [x] 10. Rutas Admin
- [x] 11. Rutas Tutor
- [x] 12. Terminar CRUD/backend existente
- [x] 13. Pruebas Bruno (pruebas principales; mantener regresión)
- [x] 14. Backend Render estable (verificación final pendiente)

### Frontend

- [x] 15. Login React mejorado
- [x] 16. Solicitud de inscripción
- [x] 17. Sesión y rutas protegidas
- [x] 18. Panel Student
- [x] 19. Panel Admin
- [x] 20. Panel Tutor
- [x] 21. Conectar frontend con FastAPI (validación manual en navegador pendiente)
- [ ] 22. Frontend en Vercel

### Inteligencia artificial

- [ ] 23. IA local
- [ ] 24. Pruebas IA
- [ ] 25. Comparativa de modelos/proveedores
- [ ] 26. Elegir IA de producción
- [ ] 27. Integración IA de producción

### Entrega final

- [ ] 28. Despliegue completo
- [ ] 29. Pruebas end-to-end
- [ ] 30. Preparación de presentación

---

**Nota de mantenimiento:** actualiza este README, `.env.example` y `requirements.txt` cuando agregues nuevas rutas, variables de entorno o dependencias.
