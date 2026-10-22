from contextlib import contextmanager
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from entrevistador.domain.ai import InterviewError
from entrevistador.models import Workspace
from entrevistador.persistence.sessions import persist, restore
from entrevistador.templatetags.formatting import richtext
from tests.factories import wav_bytes

pytestmark = pytest.mark.django_db
OFFER = "Ingeniero de software con experiencia en Python, PostgreSQL y diseño de APIs."


@pytest.fixture(autouse=True)
def ignore_credentials(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


@pytest.fixture
def provider(monkeypatch):
    provider = MagicMock()
    provider.generate.side_effect = ["¿Cómo diseñas una API?", "## Evaluación\nBuena respuesta."]
    provider.transcribe.return_value = "Usaría recursos REST."
    provider.speak.return_value = wav_bytes()

    @contextmanager
    def scope(*args):
        yield provider

    monkeypatch.setattr("entrevistador.views.actions.provider_scope", scope)
    return provider


def state(client):
    return restore(Workspace.objects.get(owner_id=client.session.session_key))


def post(client, action, **kwargs):
    data = {
        "action": action,
        "turn": state(client).turn,
        "mode": "Texto",
        "written": "",
        "transcript": "",
        **kwargs,
    }
    return client.post("/accion/", data, follow=True)


def start(client, **kwargs):
    client.get("/")
    return post(
        client,
        "start",
        context=kwargs.pop("context", OFFER),
        level="Intermedio",
        language="es",
        question_limit=kwargs.pop("question_limit", 1),
        **kwargs,
    )


@pytest.mark.parametrize("path", ["/", "/practica/", "/historial/", "/evaluacion/"])
def test_pages_render_without_key_or_interview(client, path, monkeypatch):
    factory = MagicMock()
    monkeypatch.setattr("google.genai.Client", factory)
    result = client.get(path)
    assert result.status_code == 200
    assert b"muro" in result.content
    factory.assert_not_called()


def test_full_interview_report_download_and_reset(client, provider):
    result = start(client)
    assert result.status_code == 200
    assert "¿Cómo diseñas una API?" in result.content.decode()
    result = post(client, "answer", written="Diseñaría recursos REST con validación.")
    assert result.redirect_chain[-1][0] == "/evaluacion/"
    assert state(client).interview.answered == 1
    assert "<h2>Evaluación</h2>" in result.content.decode()
    assert client.get("/descargar/entrevista/").status_code == 200
    assert b"REST" in client.get("/descargar/entrevista/").content
    assert b"Buena respuesta" in client.get("/descargar/evaluacion/").content
    post(client, "reset")
    assert state(client).interview is None
    assert client.get("/descargar/entrevista/").status_code == 404


def test_failed_answer_retains_draft_and_can_retry(client, provider):
    start(client)
    provider.generate.side_effect = [InterviewError("Sin conexión"), "Evaluación"]
    result = post(client, "answer", written="Mi respuesta con ejemplo.")
    assert "Sin conexión" in result.content.decode()
    assert state(client).interview.answered == 0
    assert state(client).draft.written == "Mi respuesta con ejemplo."
    post(client, "answer", written=state(client).draft.written)
    assert state(client).interview.answered == 1
    assert state(client).draft.written == ""


def test_duplicate_and_stale_posts_cannot_answer_twice(client, provider):
    provider.generate.side_effect = ["Pregunta", "Otra pregunta", "Informe"]
    start(client, question_limit=2)
    turn = state(client).turn
    post(client, "answer", written="Mi respuesta")
    result = client.post(
        "/accion/",
        {"action": "answer", "turn": turn, "mode": "Texto", "written": "Duplicada"},
        follow=True,
    )
    assert "otro turno" in result.content.decode()
    assert state(client).interview.answered == 1
    assert provider.generate.call_count == 2


def test_audio_transcribe_speak_navigation_and_clear(client, provider):
    start(client, question_limit=2)
    audio = wav_bytes()
    post(
        client,
        "transcribe",
        mode="Audio",
        recording=SimpleUploadedFile("respuesta.wav", audio, content_type="audio/wav"),
    )
    assert state(client).draft.transcript == "Usaría recursos REST."
    provider.transcribe.assert_called_once_with(audio, "es")
    client.get("/historial/")
    turn = state(client).turn
    assert client.get(f"/audio/respuesta/?turn={turn}").content == audio
    post(client, "speak", mode="Audio", transcript="Usaría recursos REST.")
    assert client.get(f"/audio/pregunta/?turn={turn}").content == audio
    post(client, "speak", mode="Audio", transcript="Usaría recursos REST.")
    provider.speak.assert_called_once()
    post(client, "clear_recording", mode="Audio", transcript="Usaría recursos REST.")
    assert state(client).draft.recording is None
    assert client.get(f"/audio/respuesta/?turn={turn}").status_code == 404


def test_failed_transcription_keeps_recording(client, provider):
    start(client)
    provider.transcribe.side_effect = InterviewError("Sin conexión")
    data = wav_bytes()
    post(client, "transcribe", mode="Audio", recording=SimpleUploadedFile("r.wav", data))
    assert state(client).draft.recording == data
    assert state(client).interview.answered == 0


def test_document_upload_and_failed_start_keep_preparation(client, provider):
    provider.generate.side_effect = InterviewError("Sin conexión")
    result = start(client, context="", document=SimpleUploadedFile("oferta.txt", OFFER.encode()))
    assert "Sin conexión" in result.content.decode()
    assert state(client).interview is None
    assert state(client).preparation.document_context == OFFER
    provider.generate.side_effect = ["Pregunta"]
    post(client, "start", context="", level="Intermedio", language="es", question_limit=1)
    assert state(client).interview.context == OFFER


def test_invalid_document_does_not_start(client, provider):
    result = start(client, document=SimpleUploadedFile("bad.exe", b"data"))
    assert "Formato no admitido" in result.content.decode()
    assert state(client).interview is None
    provider.generate.assert_not_called()


def test_browser_sessions_are_isolated(client, provider):
    start(client)
    other = Client()
    other.get("/")
    assert state(other).interview is None
    assert other.get("/descargar/entrevista/").status_code == 404
    turn = state(client).turn
    assert other.get(f"/audio/pregunta/?turn={turn}").status_code == 404


def test_csrf_is_required_and_codespaces_origin_is_supported(settings):
    client = Client(enforce_csrf_checks=True)
    client.get("/")
    data = {
        "turn": state(client).turn,
        "kind": "preparacion",
        "context": OFFER,
        "level": "Intermedio",
        "language": "es",
        "question_limit": 5,
        "mode": "Texto",
    }
    assert client.post("/borrador/", data).status_code == 403
    settings.ALLOWED_HOSTS = ["localhost", "example-8000.app.github.dev"]
    settings.CSRF_TRUSTED_ORIGINS = ["https://example-8000.app.github.dev"]
    response = client.post(
        "/borrador/",
        data,
        HTTP_HOST="example-8000.app.github.dev",
        HTTP_ORIGIN="https://example-8000.app.github.dev",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert response.status_code == 200
    assert state(client).preparation.context == OFFER


def test_gemini_key_is_only_read_from_environment(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-test-key")
    browser_session = client.session
    browser_session["api_key"] = "obsolete-browser-key"
    browser_session.save()
    result = client.get("/")
    assert 'name="api_key"' not in result.content.decode()
    assert b"env-test-key" not in result.content
    assert b"obsolete-browser-key" not in result.content
    assert client.post("/conexion/", {"api_key": "ignored"}).status_code == 404
    factory = MagicMock()
    monkeypatch.setattr("google.genai.Client", factory)
    start(client)
    assert factory.call_args.kwargs["api_key"] == "env-test-key"


def test_missing_env_key_prevents_start_despite_old_session_key(client):
    browser_session = client.session
    browser_session["api_key"] = "obsolete-browser-key"
    browser_session.save()
    result = start(client)
    assert state(client).interview is None
    assert "Falta la clave GEMINI_API_KEY" in result.content.decode()


def test_drafts_survive_navigation_and_json_serialization(client, provider):
    client.get("/")
    result = client.post(
        "/borrador/",
        {
            "turn": state(client).turn,
            "kind": "preparacion",
            "context": OFFER,
            "level": "Avanzado",
            "language": "en",
            "question_limit": 8,
            "mode": "Texto",
        },
    )
    assert result.status_code == 200
    client.get("/historial/")
    assert OFFER in client.get("/").content.decode()
    start(client)
    result = client.post(
        "/borrador/",
        {
            "turn": state(client).turn,
            "kind": "respuesta",
            "mode": "Audio",
            "written": "Borrador escrito",
            "transcript": "Borrador oral",
        },
    )
    assert result.status_code == 200
    assert state(client).draft.written == "Borrador escrito"
    assert state(client).draft.transcript == "Borrador oral"
    result = client.get("/practica/")
    assert b"Borrador escrito" in result.content and b"Borrador oral" in result.content


def test_busy_workspace_rejects_simultaneous_actions(client, provider):
    start(client)
    Workspace.objects.filter(owner_id=client.session.session_key).update(
        busy_until=timezone.now() + timedelta(minutes=1)
    )
    result = post(client, "answer", written="Respuesta duplicada")
    assert "solicitud en curso" in result.content.decode()
    assert state(client).interview.answered == 0
    result = client.post("/borrador/", {"turn": state(client).turn})
    assert result.status_code == 409
    assert provider.generate.call_count == 1


def test_early_finish_requires_answer_and_excludes_pending_question(client, provider):
    provider.generate.side_effect = ["Pregunta", "Otra pregunta", "Informe"]
    start(client, question_limit=3)
    post(client, "finish")
    assert state(client).interview.report is None
    post(client, "answer", written="Respondida")
    post(client, "finish")
    assert state(client).interview.report == "Informe"
    assert "Otra pregunta" not in str(provider.generate.call_args.args[1])


def test_state_restores_audio_and_settings(client, provider):
    start(client)
    workspace = Workspace.objects.get(owner_id=client.session.session_key)
    session = restore(workspace)
    session.draft.recording = b"audio"
    session.draft.voice = b"voice"
    persist(workspace, session)
    workspace.refresh_from_db()
    result = restore(workspace)
    assert result.draft.recording == b"audio" and result.draft.voice == b"voice"
    assert result.settings.chat_model == session.settings.chat_model


def test_markdown_escapes_html_and_unsafe_urls():
    html = richtext("# Informe\n<script>alert(1)</script>\n[x](javascript:alert(1))")
    assert "<h1>Informe</h1>" in html
    assert "<script>" not in html
    assert 'href="javascript:' not in html


def test_methods_and_health(client):
    assert client.get("/accion/").status_code == 405
    assert client.get("/borrador/").status_code == 405
    assert client.get("/conexion/").status_code == 404
    assert client.get("/health/").json() == {"app": "muro", "framework": "django", "status": "ok"}


def test_saved_key_cleanup_preserves_interview_and_session(client, provider):
    from importlib import import_module

    from django.apps import apps
    from django.contrib.sessions.models import Session

    start(client)
    session = client.session
    session["api_key"] = "obsolete-private-key"
    session["other_preference"] = "keep"
    session.save()
    row = Session.objects.get(pk=session.session_key)
    expiry = row.expire_date
    migration = import_module("entrevistador.migrations.0002_remove_saved_credentials")
    migration.remove_saved_keys(apps, MagicMock(connection=MagicMock(alias="default")))
    assert "api_key" not in client.session
    assert client.session["other_preference"] == "keep"
    assert state(client).interview.context == OFFER
    row.refresh_from_db()
    assert row.expire_date == expiry


def test_unused_preparation_source_cleanup_preserves_saved_interview(client, provider):
    from importlib import import_module

    from django.apps import apps

    start(client)
    workspace = Workspace.objects.get(owner_id=client.session.session_key)
    workspace.state["preparation"]["source"] = "Pegar texto"
    workspace.recording = b"recording"
    workspace.voice = b"voice"
    workspace.save(update_fields=["state", "recording", "voice"])
    expected_state = dict(workspace.state)
    expected_state["preparation"] = dict(workspace.state["preparation"])
    expected_state["preparation"].pop("source")
    migration = import_module("entrevistador.migrations.0003_remove_unused_preparation_source")
    migration.remove_unused_source(apps, MagicMock(connection=MagicMock(alias="default")))
    workspace.refresh_from_db()
    assert workspace.state == expected_state
    assert workspace.recording == b"recording" and workspace.voice == b"voice"
    restored = restore(workspace)
    assert restored.interview.context == OFFER
    assert restored.session_id == expected_state["session_id"]
