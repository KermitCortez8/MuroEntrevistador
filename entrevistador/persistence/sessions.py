"""Serialización explícita de las clases de dominio, sin pickle ni cookies con contenido."""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from entrevistador.domain.ai import Settings
from entrevistador.domain.interview import Interview
from entrevistador.domain.session import AnswerDraft, InterviewSession, PreparationDraft
from entrevistador.models import Workspace


class BusyError(ValueError):
    pass


def workspace_for(request):
    if not request.session.session_key:
        request.session.create()
    workspace, created = Workspace.objects.get_or_create(owner_id=request.session.session_key)
    if created:
        persist(workspace, InterviewSession())
    return workspace


def restore(workspace):
    data = workspace.state
    if not data:
        return InterviewSession()
    draft = AnswerDraft(**data["draft"])
    draft.recording = bytes(workspace.recording) if workspace.recording is not None else None
    draft.voice = bytes(workspace.voice) if workspace.voice is not None else None
    return InterviewSession(
        interview=Interview(**data["interview"]) if data["interview"] else None,
        settings=Settings(**data["settings"]) if data["settings"] else None,
        session_id=data["session_id"],
        response_mode=data["response_mode"],
        draft=draft,
        preparation=PreparationDraft(**data["preparation"]),
        working_models=data["working_models"],
    )


def persist(workspace, session):
    data = asdict(session)
    data["draft"].pop("recording")
    data["draft"].pop("voice")
    workspace.state = data
    workspace.recording = session.draft.recording
    workspace.voice = session.draft.voice
    workspace.save(update_fields=["state", "recording", "voice"])


@contextmanager
def edit_workspace(request):
    workspace = workspace_for(request)
    # UPDATE condicional funciona también con SQLite, donde select_for_update no bloquea filas.
    acquired = (
        Workspace.objects.filter(pk=workspace.pk)
        .filter(Q(busy_until__isnull=True) | Q(busy_until__lt=timezone.now()))
        .update(busy_until=timezone.now() + timedelta(minutes=5))
    )
    if not acquired:
        raise BusyError("Hay una solicitud en curso. Espera a que termine y vuelve a intentar.")
    try:
        workspace.refresh_from_db()
        session = restore(workspace)
        try:
            yield session
        finally:
            # Los borradores sobreviven a errores del proveedor; el dominio confirma el turno al final.
            persist(workspace, session)
    finally:
        Workspace.objects.filter(pk=workspace.pk).update(busy_until=None)
