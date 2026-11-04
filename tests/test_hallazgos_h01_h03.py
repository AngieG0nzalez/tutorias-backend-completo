"""Revalidación: H-01 (historial de inscripciones) y H-03 (contador in_progress)."""
from tests.conftest import auth


def _catalog(client, user):
    r = client.get("/enrollments/catalog", headers=auth(user))
    assert r.status_code == 200
    return {c["title"]: c for c in r.json()}


def _set_status(client, tutor, cls, new):
    r = client.patch(f"/classes/{cls.id}", json={"status": new}, headers=auth(tutor))
    assert r.status_code == 200, r.text


def test_h01_inscripcion_sigue_visible_al_iniciar_y_completar(client, world):
    _set_status(client, world["ta"], world["cA"], "in_progress")
    item = _catalog(client, world["s1"])["A"]
    assert item["status"] == "in_progress" and item["enrollment_id"] is not None
    _set_status(client, world["ta"], world["cA"], "completed")
    item = _catalog(client, world["s1"])["A"]
    assert item["status"] == "completed" and item["enrollment_id"] is not None


def test_h01_cancelada_sigue_en_historial(client, world):
    _set_status(client, world["ta"], world["cA"], "cancelled")
    assert _catalog(client, world["s1"])["A"]["status"] == "cancelled"


def test_h01_no_inscritas_no_finalizadas_no_aparecen_y_no_se_borra_nada(client, db, world):
    from app.models.enrollment import Enrollment
    before = db.query(Enrollment).count()
    _set_status(client, world["ta"], world["cA"], "completed")
    # s2 no tiene inscripción activa visible en B ni A completada disponible: A completada
    # solo aparece a quien está inscrito; B (programada) sigue disponible para s1
    cat = _catalog(client, world["s1"])
    assert cat["B"]["enrollment_id"] is None and cat["B"]["status"] == "scheduled"
    assert db.query(Enrollment).count() == before


def test_h01_clase_ajena_finalizada_no_aparece_a_no_inscrito(client, world):
    _set_status(client, world["tb"], world["cB"], "completed")
    # s1 no está inscrito en B: ya no es oferta ni historial
    assert "B" not in _catalog(client, world["s1"])
    assert _catalog(client, world["s3"])["B"]["enrollment_id"] is not None


def test_h03_summary_cuenta_in_progress(client, world):
    _set_status(client, world["ta"], world["cA"], "in_progress")
    r = client.get("/tutor-panel/summary", headers=auth(world["ta"]))
    assert r.status_code == 200
    s = r.json()
    assert s["in_progress_classes"] == 1
    assert s["total_classes"] == (
        s["scheduled_classes"] + s["in_progress_classes"]
        + s["completed_classes"] + s["cancelled_classes"]
    )


# ---- P-01: cancelación de inscripción según estado de la clase ----
import pytest


def _enroll_id(db, user, cls):
    from app.models.enrollment import Enrollment
    return db.query(Enrollment).filter_by(user_id=user.id, class_id=cls.id).one().id


def test_p01_cancelar_en_programada_ok(client, db, world):
    eid = _enroll_id(db, world["s1"], world["cA"])
    assert client.delete(f"/enrollments/{eid}", headers=auth(world["s1"])).status_code == 200


@pytest.mark.parametrize("estado", ["in_progress", "completed", "cancelled"])
def test_p01_cancelar_bloqueado_y_se_conserva(client, db, world, estado):
    from app.models.enrollment import Enrollment
    eid = _enroll_id(db, world["s1"], world["cA"])
    if estado == "in_progress":
        _set_status(client, world["ta"], world["cA"], "in_progress")
    else:
        _set_status(client, world["ta"], world["cA"], estado)
    r = client.delete(f"/enrollments/{eid}", headers=auth(world["s1"]))
    assert r.status_code == 409
    assert db.get(Enrollment, eid) is not None


def test_p01_no_propietario_403_y_anonimo_401(client, db, world):
    eid = _enroll_id(db, world["s1"], world["cA"])
    assert client.delete(f"/enrollments/{eid}", headers=auth(world["s3"])).status_code == 403
    assert client.delete(f"/enrollments/{eid}").status_code in (401, 403)


def test_p01_admin_conserva_excepcion(client, db, world):
    eid = _enroll_id(db, world["s1"], world["cA"])
    _set_status(client, world["ta"], world["cA"], "in_progress")
    assert client.delete(f"/enrollments/{eid}", headers=auth(world["adm"])).status_code == 200
