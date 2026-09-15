from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

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
)


app = FastAPI(
    title="Tutorías API",
    description="API REST para la plataforma educativa de tutorías",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
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
        return {
            "status": "error",
            "database": "disconnected",
        }
