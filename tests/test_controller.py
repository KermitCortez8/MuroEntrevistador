from unittest.mock import MagicMock

import pytest

from entrevistador.controllers.interview import InterviewController
from entrevistador.interview import InterviewError
from entrevistador.session import InterviewSession

OFFER = "Ingeniero de software con experiencia en Python y diseño de APIs."


def started_controller():
    provider = MagicMock()
    provider.generate.return_value = "Pregunta"
    controller = InterviewController(InterviewSession(), provider)
    controller.start(OFFER, "Intermedio", "es", 2)
    return controller, provider


def test_start_failure_keeps_preparation_and_session_unchanged():
    provider = MagicMock()
    provider.generate.side_effect = InterviewError("No disponible")
    session = InterviewSession()
    session.preparation.context = OFFER
    original_id = session.session_id
    with pytest.raises(InterviewError):
        InterviewController(session, provider).start(OFFER, "Intermedio", "es", 2)
    assert session.interview is None
    assert session.preparation.context == OFFER
    assert session.session_id == original_id


def test_answer_failure_keeps_drafts_until_retry_succeeds():
    controller, provider = started_controller()
    draft = controller.session.draft
    draft.written = "Mi respuesta"
    draft.transcript = "Mi transcripción"
    draft.recording = b"recording"
    provider.generate.side_effect = [InterviewError("No disponible"), "Otra pregunta"]
    with pytest.raises(InterviewError):
        controller.answer(draft.written)
    assert controller.interview.answered == 0
    assert controller.session.draft is draft
    controller.answer(draft.written)
    assert controller.interview.answered == 1
    assert controller.session.draft.written == ""
    assert controller.session.draft.recording is None


def test_voice_cached_and_failed_transcription_retains_recording():
    controller, provider = started_controller()
    provider.speak.return_value = b"voice"
    assert controller.speak() == controller.speak() == b"voice"
    provider.speak.assert_called_once_with("Pregunta")
    provider.transcribe.side_effect = [InterviewError("No disponible"), "Texto hablado"]
    with pytest.raises(InterviewError):
        controller.transcribe(b"recording")
    assert controller.session.draft.recording == b"recording"
    assert controller.transcribe() == "Texto hablado"
    assert controller.session.draft.transcript == "Texto hablado"


def test_reset_clears_interview_and_drafts_and_changes_widget_namespace():
    controller, _ = started_controller()
    original_id = controller.session.session_id
    controller.session.response_mode = "Texto"
    controller.session.draft.written = "Borrador"
    controller.session.working_models["primary"] = "backup"
    controller.reset()
    assert controller.interview is None
    assert controller.session.session_id != original_id
    assert controller.session.draft.written == ""
    assert controller.session.settings is None
    assert controller.session.response_mode == "Texto"
    assert not controller.session.working_models


def test_document_error_does_not_overwrite_valid_context():
    controller = InterviewController(InterviewSession())
    assert controller.load_document("oferta.txt", OFFER.encode()) == OFFER
    with pytest.raises(ValueError):
        controller.load_document("invalid.exe", b"binary")
    assert controller.session.preparation.document_context == OFFER
    assert controller.session.preparation.document_name == "oferta.txt"


def test_missing_provider_and_duplicate_start_are_recoverable():
    controller = InterviewController(InterviewSession())
    with pytest.raises(InterviewError, match="clave"):
        controller.start(OFFER, "Intermedio", "es", 2)
    controller, _ = started_controller()
    with pytest.raises(InterviewError, match="Ya tienes"):
        controller.start(OFFER, "Intermedio", "es", 2)
