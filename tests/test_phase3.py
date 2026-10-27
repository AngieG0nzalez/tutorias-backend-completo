"""Fase 3: transiciones de clase, límite de login y paridad de preguntas (HTTP, SQLite)."""
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.tutor import Tutor
from app.models.tutor_subject import TutorSubject
from tests.conftest import auth, make_user


def patch(client, user, cls, **body):
    return client.patch(f"/classes/{cls.id}", json=body, headers=auth(user))


def test_transiciones_validas_e_invalidas(client, world):
    ta, c = world["ta"], world["cA"]
    assert patch(client, ta, c, status="in_progress").status_code == 200
    assert patch(client, ta, c, status="scheduled").status_code == 409
    assert patch(client, ta, c, status="completed").status_code == 200
    # estado final: no se reabre ni se edita
    assert patch(client, ta, c, status="cancelled").status_code == 409
    assert patch(client, ta, c, title="Otro").status_code == 409


def test_cancelar_desde_programada_y_editar_datos(client, world):
    ta, c = world["ta"], world["cA"]
    assert patch(client, ta, c, title="Nuevo titulo").json()["title"] == "Nuevo titulo"
    assert patch(client, ta, c, status="cancelled").json()["status"] == "cancelled"


def test_tutor_ajeno_no_cambia_estado(client, world):
    assert patch(client, world["tb"], world["cA"], status="cancelled").status_code == 403


def test_crear_clase_solo_programada(client, db, world):
    tutor = db.query(Tutor).filter_by(user_id=world["ta"].id).one()
    db.add(TutorSubject(tutor_id=tutor.id, subject_id=world["alg"].id))
    db.commit()
    body = {
        "tutor_id": tutor.id, "subject_id": world["alg"].id, "title": "Nueva",
        "date_time": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        "duration_minutes": 60,
    }
    assert client.post("/classes", json={**body, "status": "completed"}, headers=auth(world["ta"])).status_code == 422
    assert client.post("/classes", json=body, headers=auth(world["ta"])).status_code == 201


def test_login_bloquea_tras_5_fallos(client, db):
    u = make_user(db, "pepe", "student")
    u.password_hash = hash_password("ClaveCorrecta1")
    db.commit()
    for _ in range(5):
        r = client.post("/auth/login", json={"email": u.email, "password": "mala"})
        assert r.status_code == 401
    blocked = client.post("/auth/login", json={"email": u.email, "password": "ClaveCorrecta1"})
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers


def test_login_correcto_y_correo_inexistente(client, db):
    u = make_user(db, "lola", "student")
    u.password_hash = hash_password("ClaveCorrecta1")
    db.commit()
    ok = client.post("/auth/login", json={"email": u.email, "password": "ClaveCorrecta1"})
    assert ok.status_code == 200 and "access_token" in ok.json()
    nx = client.post("/auth/login", json={"email": "nadie@t.co", "password": "x"})
    assert nx.status_code == 401 and nx.json()["detail"] == "Credenciales incorrectas"


def _question(statement):
    return {
        "statement": statement,
        "difficulty": "easy",
        "options": [{"option_text": f"o{i}", "is_correct": i == 0} for i in range(4)],
    }


def test_duplicado_consistente_en_ambas_apis(client, db, world):
    tutor = db.query(Tutor).filter_by(user_id=world["ta"].id).one()
    db.add(TutorSubject(tutor_id=tutor.id, subject_id=world["alg"].id))
    db.commit()
    h = auth(world["ta"])
    topic = world["t1"].id
    first = client.post(f"/topics/{topic}/exercises", json=_question("¿Cuánto es 2x=4?"), headers=h)
    assert first.status_code == 201
    dup_legacy = client.post(f"/topics/{topic}/exercises", json=_question("  ¿CUÁNTO es   2x=4? "), headers=h)
    assert dup_legacy.status_code == 409
    dup_new = client.post("/content/exercises", json={**_question("¿cuánto es 2x=4?"), "topic_id": topic}, headers=h)
    assert dup_new.status_code == 409
    # nunca se filtra is_correct en la API pública de práctica
    public = client.get(f"/topics/{topic}/exercises")
    assert public.status_code == 200
    assert "is_correct" not in public.text


def test_registro_nombre_largo_422(client):
    r = client.post("/auth/register-request", json={
        "name": "x" * 101, "email": "a@b.co", "password": "ClaveCorrecta1", "role": "student",
    })
    assert r.status_code == 422
