"""Pruebas focalizadas de Entrega 5 (sin base de datos real, datos sintéticos)."""
import pytest
from pydantic import ValidationError

from app.main import app
from app.schemas.adaptive import AdaptiveRecommendationResponse
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseOptionResponse,
    ExerciseResponse,
)


def _opts(correct=(0,), n=4):
    return [
        {"option_text": f"op{i}", "is_correct": i in correct} for i in range(n)
    ]


def test_practice_schemas_do_not_expose_is_correct():
    assert "is_correct" not in ExerciseOptionResponse.model_fields
    assert "is_correct" not in ExerciseResponse.model_fields
    assert "is_correct" not in str(AdaptiveRecommendationResponse.model_json_schema())


def test_exercise_requires_four_options():
    base = {"statement": "¿Cuánto es 2+2?"}
    ExerciseCreate(**base, options=_opts())
    for n in (2, 3, 5):
        with pytest.raises(ValidationError):
            ExerciseCreate(**base, options=_opts(n=n))


def test_exercise_requires_exactly_one_correct():
    base = {"statement": "¿Cuánto es 2+2?"}
    for correct in ((), (0, 1)):
        with pytest.raises(ValidationError):
            ExerciseCreate(**base, options=_opts(correct=correct))


def test_exercise_rejects_duplicate_options_and_extra_fields():
    ops = _opts()
    ops[1]["option_text"] = "OP0"
    with pytest.raises(ValidationError):
        ExerciseCreate(statement="¿Cuánto es 2+2?", options=ops)
    with pytest.raises(ValidationError):
        ExerciseCreate(statement="¿Cuánto es 2+2?", options=_opts(), x=1)


def test_no_duplicate_method_path_routes():
    seen = set()
    for r in app.routes:
        for m in getattr(r, "methods", None) or ():
            key = (m, r.path)
            assert key not in seen, key
            seen.add(key)


def test_sensitive_routes_have_auth_dependency():
    sensitive = ("/admin", "/content", "/tutor-panel", "/suggestions")
    for r in app.routes:
        path = getattr(r, "path", "")
        if path.startswith(sensitive):
            assert r.dependant.dependencies, f"sin dependencia de auth: {path}"


def test_cors_origins_from_env(monkeypatch):
    import importlib

    import app.main as main

    monkeypatch.setenv("CORS_ORIGINS", "https://a.com/, https://b.com")
    importlib.reload(main)
    cors = [m for m in main.app.user_middleware if m.cls.__name__ == "CORSMiddleware"][0]
    assert cors.kwargs["allow_origins"] == ["https://a.com", "https://b.com"]
    monkeypatch.delenv("CORS_ORIGINS")
    importlib.reload(main)
