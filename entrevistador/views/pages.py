"""Renderizado de las pantallas y comprobación de disponibilidad."""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from entrevistador.forms import PreparationForm
from entrevistador.integrations.gemini import resolve_api_key
from entrevistador.persistence.sessions import restore, workspace_for

SECTIONS = {
    "preparacion": "Preparación",
    "practica": "Práctica",
    "historial": "Historial",
    "evaluacion": "Evaluación",
}


@require_GET
@never_cache
def page(request, section):
    session = restore(workspace_for(request))
    draft = session.preparation
    context = {
        "section": section,
        "title": SECTIONS[section],
        "session": session,
        "interview": session.interview,
        "draft": session.draft,
        "connected": bool(resolve_api_key()),
        "needs_connection": not resolve_api_key()
        and (
            (section == "preparacion" and session.interview is None)
            or (
                section == "practica"
                and session.interview is not None
                and session.interview.report is None
            )
        ),
        "preparation_form": PreparationForm(
            initial={
                "context": draft.context,
                "level": draft.level,
                "language": "es" if draft.language == "Español" else "en",
                "question_limit": draft.question_limit,
                "mode": session.response_mode,
            }
        ),
        "progress": round(100 * session.interview.answered / session.interview.question_limit)
        if session.interview
        else 0,
        "current_question": session.interview.messages[-1]["content"]
        if session.interview and session.interview.messages and session.interview.report is None
        else "",
        "question_number": session.interview.answered + 1 if session.interview else 1,
        "is_last_question": bool(
            session.interview and session.interview.answered + 1 >= session.interview.question_limit
        ),
        "autoplay": request.GET.get("reproducir") == "1",
    }
    return render(request, f"entrevistador/pages/{section}.html", context)


@require_GET
def health(request):
    return JsonResponse({"app": "muro", "framework": "django", "status": "ok"})
