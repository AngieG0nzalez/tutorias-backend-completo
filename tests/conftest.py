"""Fixtures HTTP: app real + JWT reales + SQLite en memoria (datos sintéticos).

SQLite NO valida bloqueos FOR UPDATE ni el dialecto PostgreSQL.
"""
import warnings
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.security import create_access_token
from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.student_profile import StudentProfile
from app.models.student_progress import StudentProgress
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.models.user import User

warnings.filterwarnings("ignore", message=".*httpx.*")


@compiles(BigInteger, "sqlite")
def _bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db, name, role, active=True):
    u = User(name=name, email=f"{name}@t.co", password_hash="x", role=role, is_active=active)
    db.add(u)
    db.flush()
    return u


def auth(user):
    token = create_access_token({"sub": str(user.id), "sv": user.session_version})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def world(db):
    """2 tutores, 3 estudiantes, 2 materias, clases y progreso."""
    s1 = make_user(db, "ana", "student")
    s2 = make_user(db, "beto", "student")
    s3 = make_user(db, "cami", "student")
    ta = make_user(db, "tutA", "tutor")
    tb = make_user(db, "tutB", "tutor")
    adm = make_user(db, "adm", "admin")
    for s, g in ((s1, 9), (s2, 9), (s3, 9)):
        db.add(StudentProfile(user_id=s.id, grade=g))
    alg = Subject(name="Algebra", grade=9)
    geo = Subject(name="Geometria", grade=9)
    db.add_all([alg, geo])
    db.flush()
    t1 = Topic(subject_id=alg.id, name="Lineales", order_number=1, is_active=True)
    t2 = Topic(subject_id=alg.id, name="Inecuaciones", order_number=2, is_active=True)
    t3 = Topic(subject_id=alg.id, name="Sistemas", order_number=3, is_active=True)
    t_inactive = Topic(subject_id=alg.id, name="Oculto", order_number=4, is_active=False)
    g1 = Topic(subject_id=geo.id, name="Angulos", order_number=1, is_active=True)
    tutA = Tutor(user_id=ta.id, experience_years=1, is_active=True)
    tutB = Tutor(user_id=tb.id, experience_years=1, is_active=True)
    db.add_all([t1, t2, t3, t_inactive, g1, tutA, tutB])
    db.flush()
    when = datetime.now(timezone.utc) + timedelta(days=1)
    cA = TutoringClass(tutor_id=tutA.id, subject_id=alg.id, title="A", date_time=when,
                       duration_minutes=60, price=0, status="scheduled")
    cB = TutoringClass(tutor_id=tutB.id, subject_id=geo.id, title="B", date_time=when,
                       duration_minutes=60, price=0, status="scheduled")
    db.add_all([cA, cB])
    db.flush()
    db.add_all([
        Enrollment(user_id=s1.id, class_id=cA.id, status="enrolled"),
        Enrollment(user_id=s2.id, class_id=cA.id, status="cancelled"),
        Enrollment(user_id=s3.id, class_id=cB.id, status="enrolled"),
    ])
    now = datetime.now(timezone.utc)
    db.add_all([
        StudentProgress(user_id=s1.id, topic_id=t1.id, exercises_attempted=10, exercises_correct=8,
                        mastery_percentage=65, level="medium", last_practiced_at=now),
        StudentProgress(user_id=s1.id, topic_id=t2.id, exercises_attempted=5, exercises_correct=3,
                        mastery_percentage=50.5, level="low", last_practiced_at=now),
        # práctica en otra materia: no debe aparecer en la clase de álgebra
        StudentProgress(user_id=s1.id, topic_id=g1.id, exercises_attempted=7, exercises_correct=7,
                        mastery_percentage=100, level="high", last_practiced_at=now),
    ])
    db.commit()
    return dict(s1=s1, s2=s2, s3=s3, ta=ta, tb=tb, adm=adm, cA=cA, cB=cB,
                t1=t1, t2=t2, t3=t3, alg=alg)
