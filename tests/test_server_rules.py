"""Pruebas de reglas de servidor (SQLite en memoria, datos sintéticos)."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  registra los modelos
from app.database.base import Base
from app.models.class_model import TutoringClass
from app.models.enrollment import Enrollment
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.tutor import Tutor
from app.models.user import User
from app.routers.messages import send_message
from app.schemas.message import MessageCreate
from app.services.grade_access import ensure_student_can_practice_topic


@compiles(BigInteger, "sqlite")
def _bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _user(db, name, role, active=True):
    u = User(name=name, email=f"{name}@t.co", password_hash="x", role=role, is_active=active)
    db.add(u)
    db.flush()
    return u


@pytest.fixture()
def world(db):
    s9 = _user(db, "s9", "student")
    s10 = _user(db, "s10", "student")
    s_noprofile = _user(db, "snp", "student")
    t1 = _user(db, "t1", "tutor")
    t2 = _user(db, "t2", "tutor")
    db.add_all([StudentProfile(user_id=s9.id, grade=9), StudentProfile(user_id=s10.id, grade=10)])
    subj9 = Subject(name="Mat9", grade=9)
    db.add(subj9)
    db.flush()
    topic = Topic(subject_id=subj9.id, name="Tema", order_number=1, is_active=True)
    tut1 = Tutor(user_id=t1.id, experience_years=1, is_active=True)
    tut2 = Tutor(user_id=t2.id, experience_years=1, is_active=True)
    db.add_all([topic, tut1, tut2])
    db.flush()
    cls = TutoringClass(
        tutor_id=tut1.id, subject_id=subj9.id, title="C",
        date_time=datetime.now(timezone.utc) + timedelta(days=1),
        duration_minutes=60, price=0, status="scheduled",
    )
    db.add(cls)
    db.flush()
    db.add(Enrollment(user_id=s9.id, class_id=cls.id, status="enrolled"))
    db.commit()
    return dict(s9=s9, s10=s10, snp=s_noprofile, t1=t1, t2=t2, topic=topic)


def test_student_same_grade_can_practice(db, world):
    ensure_student_can_practice_topic(db, world["s9"], world["topic"])


@pytest.mark.parametrize("who", ["s10", "snp"])
def test_student_other_grade_or_no_profile_is_403(db, world, who):
    with pytest.raises(HTTPException) as exc:
        ensure_student_can_practice_topic(db, world[who], world["topic"])
    assert exc.value.status_code == 403


def _send(db, sender, receiver):
    return send_message(MessageCreate(receiver_id=receiver.id, content="hola"), db=db, current_user=sender)


def test_student_can_write_active_tutor(db, world):
    assert _send(db, world["s9"], world["t2"]).id


def test_tutor_can_write_enrolled_student_only(db, world):
    assert _send(db, world["t1"], world["s9"]).id
    with pytest.raises(HTTPException) as exc:
        _send(db, world["t1"], world["s10"])
    assert exc.value.status_code == 403


def test_tutor_can_reply_to_student_who_wrote_first(db, world):
    _send(db, world["s10"], world["t1"])
    assert _send(db, world["t1"], world["s10"]).id


def test_tutor_cannot_message_unrelated_student(db, world):
    with pytest.raises(HTTPException) as exc:
        _send(db, world["t2"], world["s9"])
    assert exc.value.status_code == 403


def test_health_returns_503_when_db_fails(monkeypatch):
    import app.main as main

    class Broken:
        def connect(self):
            raise RuntimeError("db down")

    monkeypatch.setattr(main, "engine", Broken())
    response = main.health()
    assert response.status_code == 503
