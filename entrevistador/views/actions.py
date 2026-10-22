"""Acciones POST: comenzar, responder, transcribir, evaluar y guardar borradores."""

from contextlib import contextmanager

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from entrevistador.application.interview import InterviewController
from entrevistador.domain.ai import InterviewError
from entrevistador.forms import AnswerForm, PreparationForm
from entrevistador.integrations.gemini import provider_scope, resolve_api_key, settings_from_env
from entrevistador.persistence.sessions import BusyError, edit_workspace


def check_turn(request, session):
    if request.POST.get("turn") != session.turn:
        raise ValueError("Esta página corresponde a otro turno. Recarga antes de continuar.")


def validate(form):
    if not form.is_valid():
        raise ValueError(
            " ".join(str(error) for errors in form.errors.values() for error in errors)
        )
    return form.cleaned_data


def preparation_data(session, data):
    draft = session.preparation
    draft.context = data["context"]
    draft.level = data["level"]
    draft.language = "Español" if data["language"] == "es" else "English"
    draft.question_limit = data["question_limit"]
    session.response_mode = data["mode"]


def answer_data(session, data):
    session.response_mode = data["mode"]
    session.draft.written = data["written"]
    session.draft.transcript = data["transcript"]
    if data.get("recording"):
        session.draft.recording = data["recording"].read()


@contextmanager
def controller_for(session):
    settings = session.settings or settings_from_env()
    with provider_scope(resolve_api_key(), settings, session.working_models) as provider:
        yield InterviewController(session, provider, settings)


@require_POST
@never_cache
def action(request):
    operation = request.POST.get("action")
    destination = "preparacion" if operation in {"start", "reset"} else "practica"
    try:
        with edit_workspace(request) as session:
            check_turn(request, session)
            if operation == "reset":
                InterviewController(session).reset()
                return redirect("preparacion")
            if operation not in {
                "start",
                "answer",
                "finish",
                "transcribe",
                "speak",
                "clear_recording",
            }:
                return HttpResponse("Acción desconocida.", status=400)
            if operation == "start":
                data = validate(PreparationForm(request.POST, request.FILES))
                preparation_data(session, data)
                controller = InterviewController(session)
                context = data["context"]
                if data["document"]:
                    context = controller.load_document(
                        data["document"].name, data["document"].read()
                    )
                elif not context:
                    context = session.preparation.document_context
                with controller_for(session) as controller:
                    controller.start(
                        context, data["level"], data["language"], data["question_limit"]
                    )
                destination = "practica"
            else:
                if session.interview is None:
                    raise ValueError("Primero prepara e inicia una entrevista.")
                if session.interview.report is not None:
                    raise ValueError("La entrevista ya terminó. Puedes consultar tu evaluación.")
                data = validate(AnswerForm(request.POST, request.FILES))
                answer_data(session, data)
                if operation == "clear_recording":
                    session.draft.recording = None
                else:
                    with controller_for(session) as controller:
                        if operation == "answer":
                            text = (
                                data["written"] if data["mode"] == "Texto" else data["transcript"]
                            )
                            controller.answer(text)
                        elif operation == "finish":
                            controller.finish()
                        elif operation == "transcribe":
                            controller.transcribe()
                        elif operation == "speak":
                            controller.speak()
                if session.interview.report is not None:
                    destination = "evaluacion"
    except BusyError as exc:
        messages.error(request, str(exc))
    except (InterviewError, ValueError) as exc:
        messages.error(request, str(exc))
    else:
        if operation == "speak":
            return redirect("/practica/?reproducir=1")
    return redirect(destination)


@require_POST
@never_cache
def draft(request):
    try:
        with edit_workspace(request) as session:
            check_turn(request, session)
            if request.POST.get("kind") == "preparacion":
                if session.interview is not None:
                    raise ValueError("La entrevista ya comenzó.")
                preparation_data(session, validate(PreparationForm(request.POST)))
            else:
                if session.interview is None or session.interview.report is not None:
                    raise ValueError("No hay una pregunta pendiente.")
                answer_data(session, validate(AnswerForm(request.POST)))
    except BusyError as exc:
        return JsonResponse({"error": str(exc)}, status=409)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"saved": True})
