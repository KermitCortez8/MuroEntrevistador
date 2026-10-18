from pathlib import Path
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

import entrevistador.interview as interview_module
from entrevistador.interview import InterviewError

OFFER = "Ingeniero de software con experiencia en Python, PostgreSQL y diseño de APIs."
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def ignore_local_credentials(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_setup_requires_key(monkeypatch):
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert button(app, "Comenzar entrevista").disabled
    assert len(app.info) == 1


@pytest.mark.parametrize(
    ("gemini_key", "google_key", "expected"),
    [("gemini-test", "google-test", "gemini-test"), ("", "google-test", "google-test")],
)
def test_credentials_support_google_key_and_sidebar_override(
    monkeypatch, gemini_key, google_key, expected
):
    monkeypatch.setenv("GEMINI_API_KEY", gemini_key)
    monkeypatch.setenv("GOOGLE_API_KEY", google_key)
    client_factory = MagicMock()
    monkeypatch.setattr("google.genai.Client", client_factory)
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert client_factory.call_args.kwargs["api_key"] == expected
    assert client_factory.call_args.kwargs["vertexai"] is False
    client_factory.return_value.close.assert_called_once()
    app.text_input[0].input("sidebar-test").run()
    assert not app.exception
    assert client_factory.call_args.kwargs["api_key"] == "sidebar-test"


def test_ui_start_answer_report_and_reset(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.side_effect = ["¿Cómo diseñas una API?", "Evaluación de práctica"]
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    app.slider[0].set_value(1)
    button(app, "Comenzar entrevista").click().run()
    assert not app.exception
    assert len(app.chat_message) == 1
    assert button(app, "Terminar y evaluar lo respondido").disabled
    # AppTest no captura micrófono: se inyecta el resultado de la transcripción.
    turn = f"{app.session_state['session_id']}_0"
    app.session_state[f"transcript_{turn}"] = "Usaría HTTP y recursos REST."
    app.run()
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.session_state["interview"].answered == 1
    assert app.session_state["interview"].report == "Evaluación de práctica"
    assert len(app.chat_message) == 2
    assert not app.text_area
    assert f"transcript_{turn}" not in app.session_state
    button(app, "Nueva entrevista").click().run()
    assert not app.exception
    assert "interview" not in app.session_state
    assert button(app, "Comenzar entrevista")


def test_ui_keeps_draft_on_generation_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.side_effect = ["Pregunta", InterviewError("Sin conexión"), "Repregunta"]
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    button(app, "Comenzar entrevista").click().run()
    turn = f"{app.session_state['session_id']}_0"
    app.session_state[f"transcript_{turn}"] = "Mi respuesta corregida."
    app.run()
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.error[0].value == "Sin conexión"
    assert app.text_area[0].value == "Mi respuesta corregida."
    assert app.session_state["interview"].answered == 0
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.session_state["interview"].answered == 1
    assert len(app.chat_message) == 3
