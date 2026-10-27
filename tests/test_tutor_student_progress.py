"""TP-01 a TP-12 y TP-15 vía HTTP real (TestClient) sobre SQLite sintético."""
import pytest
from sqlalchemy import event

from tests.conftest import auth, make_user
from app.models.student_progress import StudentProgress


def url(cls, student):
    return f"/tutor-panel/classes/{cls.id}/students/{student.id}/progress"


def test_tp01_tutor_ve_alumno_inscrito(client, world):
    r = client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"]))
    assert r.status_code == 200
    body = r.json()
    assert body["student_name"] == "ana"
    assert body["student_grade"] == 9
    assert body["subject"]["name"] == "Algebra"
    s = body["summary"]
    assert (s["total_topics"], s["practiced_topics"], s["unpracticed_topics"]) == (3, 2, 1)
    assert (s["exercises_attempted"], s["exercises_correct"]) == (15, 11)
    assert s["accuracy_percentage"] == 73.33
    assert s["average_mastery_percentage"] == 57.75


def test_tp02_tutor_ajeno_recibe_404(client, world):
    r = client.get(url(world["cA"], world["s1"]), headers=auth(world["tb"]))
    assert r.status_code == 404
    assert "ana" not in r.text


def test_tp03_alumno_no_inscrito_en_esa_clase_404(client, world):
    # s3 está en la clase de otro tutor; s1 no está en cB
    assert client.get(url(world["cA"], world["s3"]), headers=auth(world["ta"])).status_code == 404
    assert client.get(url(world["cB"], world["s1"]), headers=auth(world["tb"])).status_code == 404


def test_tp04_estudiante_403(client, world):
    assert client.get(url(world["cA"], world["s1"]), headers=auth(world["s1"])).status_code == 403


def test_tp05_admin_403(client, world):
    assert client.get(url(world["cA"], world["s1"]), headers=auth(world["adm"])).status_code == 403


def test_tp06_sin_jwt_o_invalido(client, world):
    u = url(world["cA"], world["s1"])
    assert client.get(u).status_code in (401, 403)
    assert client.get(u, headers={"Authorization": "Bearer basura"}).status_code == 401


def test_tp07_sin_progreso_200_sin_division_por_cero(client, db, world):
    db.query(StudentProgress).delete()
    db.commit()
    r = client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"]))
    assert r.status_code == 200
    s = r.json()["summary"]
    assert s["exercises_attempted"] == 0
    assert s["accuracy_percentage"] is None
    assert s["average_mastery_percentage"] is None
    assert s["practiced_topics"] == 0 and s["unpracticed_topics"] == 3
    assert all(t["practiced"] is False for t in r.json()["topics"])


def test_tp08_otras_materias_no_aparecen(client, world):
    topics = client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"])).json()["topics"]
    assert "Angulos" not in [t["topic_name"] for t in topics]
    assert "Oculto" not in [t["topic_name"] for t in topics]


def test_tp09_matricula_cancelada_denegada(client, world):
    r = client.get(url(world["cA"], world["s2"]), headers=auth(world["ta"]))
    assert r.status_code == 404


def test_tp10_orden_estable_sin_duplicados(client, world):
    topics = client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"])).json()["topics"]
    assert [t["topic_name"] for t in topics] == ["Lineales", "Inecuaciones", "Sistemas"]
    assert len({t["topic_id"] for t in topics}) == 3
    assert topics[2]["practiced"] is False and topics[2]["level"] == "new"


def test_tp11_decimales_son_numeros(client, world):
    topics = client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"])).json()["topics"]
    assert topics[1]["mastery_percentage"] == 50.5
    assert isinstance(topics[0]["mastery_percentage"], (int, float))


def test_tp12_progress_me_conserva_permisos(client, world):
    ok = client.get("/progress/me", headers=auth(world["s1"]))
    assert ok.status_code == 200
    assert len(ok.json()) == 3
    assert client.get("/progress/me", headers=auth(world["ta"])).status_code == 403


def test_tp15_sin_n_mas_1(client, db, world):
    count = {"n": 0}
    engine = db.get_bind()

    def counter(*a, **k):
        count["n"] += 1

    event.listen(engine, "before_cursor_execute", counter)
    try:
        client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"]))
        base = count["n"]
        for i in range(10):
            from app.models.topic import Topic
            db.add(Topic(subject_id=world["alg"].id, name=f"X{i}", order_number=10 + i, is_active=True))
        db.commit()
        count["n"] = 0
        client.get(url(world["cA"], world["s1"]), headers=auth(world["ta"]))
        assert count["n"] == base
    finally:
        event.remove(engine, "before_cursor_execute", counter)
