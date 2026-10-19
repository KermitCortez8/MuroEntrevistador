from pathlib import Path
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

import entrevistador.interview as interview_module
from entrevistador.interview import InterviewError
from entrevistador.views import navigation as nav

OFFER = "Ingeniero de software con experiencia en Python, PostgreSQL y diseño de APIs."
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def ignore_local_credentials(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


def button(app, label):
    return next(item for item in app.button if item.label == label)


def response_mode(app):
    return next(item for item in app.radio if item.label == "¿Cómo prefieres responder?")


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
    assert not app.tabs
    assert any("¿Cómo diseñas una API?" in item.value for item in app.markdown)
    assert button(app, "Terminar y evaluar lo respondido").disabled
    # AppTest no captura micrófono: se inyecta el resultado de la transcripción.
    turn = app.session_state["muro_session"].turn
    app.session_state["muro_session"].draft.transcript = "Usaría HTTP y recursos REST."
    app.run()
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.session_state["muro_session"].interview.answered == 1
    assert app.session_state["muro_session"].interview.report == "Evaluación de práctica"
    app.switch_page(nav.HISTORY).run()
    assert len(app.chat_message) == 2
    assert not app.text_area
    assert f"transcript_{turn}" not in app.session_state
    button(app, "Nueva entrevista").click().run()
    assert not app.exception
    assert app.session_state["muro_session"].interview is None
    assert button(app, "Comenzar entrevista")


def test_ui_keeps_draft_on_generation_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.side_effect = ["Pregunta", InterviewError("Sin conexión"), "Repregunta"]
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    button(app, "Comenzar entrevista").click().run()
    app.session_state["muro_session"].draft.transcript = "Mi respuesta corregida."
    app.run()
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.error[0].value == "Sin conexión"
    assert app.text_area[0].value == "Mi respuesta corregida."
    assert app.session_state["muro_session"].interview.answered == 0
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.session_state["muro_session"].interview.answered == 1
    app.switch_page(nav.HISTORY).run()
    assert len(app.chat_message) == 3


def test_text_mode_finishes_without_audio(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.side_effect = ["Pregunta escrita", "Informe final"]
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    app.slider[0].set_value(1)
    response_mode(app).set_value("Texto")
    button(app, "Comenzar entrevista").click().run()
    assert not app.exception
    assert not app.tabs
    assert any("Pregunta escrita" in item.value for item in app.markdown)
    app.text_area[0].input("Diseñaría recursos REST con validación y pruebas.").run()
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert app.session_state["muro_session"].interview.report == "Informe final"
    assert app.session_state["muro_session"].interview.answered == 1
    provider.transcribe.assert_not_called()
    provider.speak.assert_not_called()


def test_switch_modes_preserves_drafts_and_question_audio(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.side_effect = ["Pregunta", "Siguiente pregunta"]
    provider.speak.return_value = b"audio"
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    button(app, "Comenzar entrevista").click().run()
    turn = app.session_state["muro_session"].turn
    app.session_state["muro_session"].draft.transcript = "Mi respuesta hablada."
    app.run()
    response_mode(app).set_value("Texto").run()
    app.text_area[0].input("Mi borrador escrito.").run()
    button(app, "🔊 Escuchar pregunta").click().run()
    assert not app.exception
    provider.speak.assert_called_once_with("Pregunta")
    response_mode(app).set_value("Audio").run()
    assert app.text_area[0].value == "Mi respuesta hablada."
    response_mode(app).set_value("Texto").run()
    assert app.text_area[0].value == "Mi borrador escrito."
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert (
        app.session_state["muro_session"].interview.messages[1]["content"] == "Mi borrador escrito."
    )
    assert f"written_{turn}" not in app.session_state
    assert f"transcript_{turn}" not in app.session_state


def test_ui_automatically_switches_model_and_completes_interview(monkeypatch):
    from google.genai import errors

    from tests.test_interview import text_response

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("GEMINI_CHAT_MODEL", "primary")
    client = MagicMock()
    client.models.generate_content.side_effect = [
        errors.ServerError(503, {"error": {"message": "busy"}}),
        text_response("Pregunta alternativa"),
        text_response("Informe final"),
    ]
    monkeypatch.setattr("google.genai.Client", MagicMock(return_value=client))
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    app.slider[0].set_value(1)
    response_mode(app).set_value("Texto")
    button(app, "Comenzar entrevista").click().run()
    assert not app.exception
    assert not app.error
    app.text_area[0].input("Usaría HTTP y recursos REST.").run()
    button(app, "Enviar respuesta").click().run()
    assert not app.exception
    assert not app.error
    assert app.session_state["muro_session"].interview.report == "Informe final"
    assert app.session_state["muro_session"].interview.answered == 1
    assert [call.kwargs["model"] for call in client.models.generate_content.call_args_list] == [
        "primary",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash-lite",
    ]


@pytest.mark.parametrize("path", [nav.PRACTICE, nav.HISTORY, nav.EVALUATION])
def test_pages_require_an_interview_without_crashing(path):
    app = AppTest.from_file(APP_PATH).run()
    app.switch_page(path).run()
    assert not app.exception
    assert any("Primero prepara" in item.value for item in app.info)
    assert not app.text_area


def test_navigation_keeps_drafts_voice_and_current_question(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.return_value = "Pregunta persistente"
    provider.speak.return_value = b"audio"
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    button(app, "Comenzar entrevista").click().run()
    session = app.session_state["muro_session"]
    session.draft.transcript = "Mi transcripción."
    app.run()
    response_mode(app).set_value("Texto").run()
    app.text_area[0].input("Mi borrador entre páginas.").run()
    button(app, "🔊 Escuchar pregunta").click().run()
    app.switch_page(nav.HISTORY).run()
    assert not app.exception
    assert len(app.chat_message) == 1
    app.switch_page(nav.EVALUATION).run()
    assert not app.exception
    assert any("Tu progreso merece" in item.value for item in app.markdown)
    app.switch_page(nav.PRACTICE).run()
    assert not app.exception
    assert response_mode(app).value == "Texto"
    assert app.text_area[0].value == "Mi borrador entre páginas."
    assert app.session_state["muro_session"].draft.voice == b"audio"
    response_mode(app).set_value("Audio").run()
    assert app.text_area[0].value == "Mi transcripción."
    assert app.session_state["muro_session"].interview.answered == 0
    provider.generate.assert_called_once()
    provider.speak.assert_called_once()


def test_preparation_draft_survives_visiting_other_pages():
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER).run()
    app.slider[0].set_value(8).run()
    response_mode(app).set_value("Texto").run()
    app.switch_page(nav.HISTORY).run()
    app.switch_page(nav.PREPARATION).run()
    assert not app.exception
    assert app.text_area[0].value == OFFER
    assert app.slider[0].value == 8
    assert response_mode(app).value == "Texto"


def test_history_and_evaluation_do_not_construct_api_clients(monkeypatch):
    from entrevistador.interview import Interview

    app = AppTest.from_file(APP_PATH).run()
    session = app.session_state["muro_session"]
    session.interview = Interview(OFFER)
    session.interview.messages = [{"role": "assistant", "content": "Pregunta"}]
    client_factory = MagicMock()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr("google.genai.Client", client_factory)
    app.switch_page(nav.HISTORY).run()
    assert not app.exception
    assert len(app.chat_message) == 1
    app.switch_page(nav.EVALUATION).run()
    assert not app.exception
    client_factory.assert_not_called()


def test_audio_recording_survives_page_navigation_and_can_be_transcribed(monkeypatch):
    from tests.test_interview import wav_bytes

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.return_value = "Pregunta de audio"
    provider.transcribe.return_value = "Mi respuesta oral"
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    button(app, "Comenzar entrevista").click().run()
    data = wav_bytes()
    app.audio_input[0].upload("respuesta.wav", data).run()
    assert not app.exception
    assert app.session_state["muro_session"].draft.recording == data
    app.switch_page(nav.HISTORY).run()
    app.switch_page(nav.PRACTICE).run()
    assert not app.exception
    assert not button(app, "Transcribir respuesta").disabled
    button(app, "Transcribir respuesta").click().run()
    assert not app.exception
    assert app.text_area[0].value == "Mi respuesta oral"
    provider.transcribe.assert_called_once_with(data, "es")


def test_removing_recording_clears_persisted_audio(monkeypatch):
    from tests.test_interview import wav_bytes

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    provider = MagicMock()
    provider.generate.return_value = "Pregunta de audio"
    monkeypatch.setattr(interview_module, "AIProvider", lambda *_: provider)
    app = AppTest.from_file(APP_PATH).run()
    app.text_area[0].input(OFFER)
    button(app, "Comenzar entrevista").click().run()
    app.audio_input[0].upload("respuesta.wav", wav_bytes()).run()
    app.audio_input[0].clear().run()
    assert not app.exception
    assert app.session_state["muro_session"].draft.recording is None
    assert button(app, "Transcribir respuesta").disabled


def test_migrates_open_interview_from_previous_single_page_ui(monkeypatch):
    from entrevistador.interview import Interview

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr("google.genai.Client", MagicMock())
    interview = Interview(OFFER)
    interview.messages = [{"role": "assistant", "content": "Pregunta anterior"}]
    app = AppTest.from_file(APP_PATH)
    app.session_state["interview"] = interview
    app.session_state["session_id"] = "legacy"
    app.session_state["response_mode"] = "Texto"
    app.session_state["written_legacy_0"] = "Borrador previo a la actualización."
    app.run()
    app.switch_page(nav.PRACTICE).run()
    assert not app.exception
    assert app.text_area[0].value == "Borrador previo a la actualización."
    assert app.session_state["muro_session"].interview is interview
