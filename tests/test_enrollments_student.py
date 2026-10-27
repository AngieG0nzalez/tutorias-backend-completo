"""Fase 2: catálogo e inscripción del estudiante (HTTP, SQLite sintético)."""
from datetime import datetime, timedelta, timezone

from app.models.class_model import TutoringClass
from app.models.student_profile import StudentProfile
from app.models.subject import Subject
from tests.conftest import auth, make_user


def test_catalogo_solo_grado_y_programadas(client, db, world):
    s10 = make_user(db, "diego", "student")
    db.add(StudentProfile(user_id=s10.id, grade=10))
    s10_subj = Subject(name="Calculo", grade=10)
    db.add(s10_subj)
    db.flush()
    tut = db.query(__import__("app.models.tutor", fromlist=["Tutor"]).Tutor).first()
    db.add(TutoringClass(tutor_id=tut.id, subject_id=s10_subj.id, title="C10",
                         date_time=datetime.now(timezone.utc) + timedelta(days=2),
                         duration_minutes=45, price=0, status="scheduled"))
    db.add(TutoringClass(tutor_id=tut.id, subject_id=world["alg"].id, title="Vieja",
                         date_time=datetime.now(timezone.utc), duration_minutes=45,
                         price=0, status="completed"))
    db.commit()
    r9 = client.get("/enrollments/catalog", headers=auth(world["s1"]))
    assert r9.status_code == 200
    titles9 = {c["title"] for c in r9.json()}
    assert titles9 == {"A", "B"}
    assert all(c["subject_grade"] == 9 for c in r9.json())
    mine = next(c for c in r9.json() if c["title"] == "A")
    assert mine["enrollment_id"] is not None and mine["tutor_name"] == "tutA"
    r10 = client.get("/enrollments/catalog", headers=auth(s10))
    assert {c["title"] for c in r10.json()} == {"C10"}


def test_catalogo_solo_estudiantes(client, world):
    assert client.get("/enrollments/catalog", headers=auth(world["ta"])).status_code == 403
    assert client.get("/enrollments/catalog").status_code in (401, 403)


def test_inscripcion_ok_duplicado_y_ajena(client, world):
    body = {"user_id": world["s3"].id, "class_id": world["cA"].id}
    ok = client.post("/enrollments", json=body, headers=auth(world["s3"]))
    assert ok.status_code == 201
    assert client.post("/enrollments", json=body, headers=auth(world["s3"])).status_code == 409
    ajena = {"user_id": world["s2"].id, "class_id": world["cB"].id}
    assert client.post("/enrollments", json=ajena, headers=auth(world["s3"])).status_code == 403


def test_inscripcion_otro_grado_403(client, db, world):
    s10 = make_user(db, "eva", "student")
    db.add(StudentProfile(user_id=s10.id, grade=10))
    db.commit()
    r = client.post("/enrollments", json={"user_id": s10.id, "class_id": world["cA"].id},
                    headers=auth(s10))
    assert r.status_code == 403


def test_inscripcion_sin_perfil_403(client, db, world):
    s = make_user(db, "sinperfil", "student")
    db.commit()
    r = client.post("/enrollments", json={"user_id": s.id, "class_id": world["cA"].id},
                    headers=auth(s))
    assert r.status_code == 403


def test_inscripcion_clase_no_programada_409(client, db, world):
    world["cA"].status = "completed"
    db.commit()
    r = client.post("/enrollments", json={"user_id": world["s3"].id, "class_id": world["cA"].id},
                    headers=auth(world["s3"]))
    assert r.status_code == 409


def test_cancelar_propia_y_no_ajena(client, db, world):
    from app.models.enrollment import Enrollment
    e_s1 = db.query(Enrollment).filter_by(user_id=world["s1"].id).one()
    assert client.delete(f"/enrollments/{e_s1.id}", headers=auth(world["s3"])).status_code == 403
    assert client.delete(f"/enrollments/{e_s1.id}", headers=auth(world["s1"])).status_code == 200
