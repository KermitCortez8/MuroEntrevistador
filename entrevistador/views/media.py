"""Audios privados y descargas de la entrevista y la evaluación."""

from django.http import Http404, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from entrevistador.persistence.sessions import restore, workspace_for


@require_GET
@never_cache
def audio(request, kind):
    session = restore(workspace_for(request))
    if request.GET.get("turn") != session.turn:
        raise Http404
    data = (
        session.draft.voice
        if kind == "pregunta"
        else (session.draft.recording if kind == "respuesta" else None)
    )
    if data is None:
        raise Http404
    response = HttpResponse(data, content_type="audio/wav")
    response["Cache-Control"] = "private, no-store"
    return response


@require_GET
@never_cache
def download(request, kind):
    interview = restore(workspace_for(request)).interview
    if interview is None or kind not in {"entrevista", "evaluacion"}:
        raise Http404
    if kind == "evaluacion" and interview.report is None:
        raise Http404
    content = interview.export_markdown() if kind == "entrevista" else interview.report
    response = HttpResponse(content, content_type="text/markdown; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{kind}.md"'
    return response
