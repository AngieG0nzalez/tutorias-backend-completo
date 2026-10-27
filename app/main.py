import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

import app.models

from app.database.connection import engine
from app.routers import (
    auth,
    users,
    tutors,
    subjects,
    classes,
    enrollments,
    messages,
    reviews,
    topics,
    admin,
    attempts,
    progress,
    adaptive,
    admin_users,
    tutor_panel,
    account,
    admin_tutor_subjects,
    content,
    suggestions,
)


app = FastAPI(
    title="Tutorías API",
    description="API REST para la plataforma educativa de tutorías",
    version="1.0.0",
    docs_url=None,
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    swagger_html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Documentación",
    )

    html = swagger_html.body.decode("utf-8")

    dark_css = """
    <style>
        body {
            background-color: #121212 !important;
        }

        .swagger-ui {
            filter: invert(88%) hue-rotate(180deg);
        }

        .swagger-ui .microlight {
            filter: invert(100%) hue-rotate(180deg);
        }
    </style>
    """

    html = html.replace(
        "</head>",
        f"{dark_css}</head>"
    )

    return HTMLResponse(content=html)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip().rstrip("/")
        for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173"
        ).split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tutors.router)
app.include_router(subjects.router)
app.include_router(classes.router)
app.include_router(enrollments.router)
app.include_router(messages.router)
app.include_router(reviews.router)
app.include_router(topics.router)
app.include_router(admin.router)
app.include_router(attempts.router)
app.include_router(progress.router)
app.include_router(adaptive.router)
app.include_router(admin_users.router)
app.include_router(tutor_panel.router)
app.include_router(account.router)
app.include_router(admin_tutor_subjects.router)
app.include_router(content.router)
app.include_router(suggestions.router)

@app.get("/")
def root():
    return {
        "name": "Tutorías API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "disconnected",
            },
        )
