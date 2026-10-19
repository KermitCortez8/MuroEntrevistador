"""Adaptador entre la sesión de Streamlit y los controladores independientes."""

from contextlib import contextmanager

import streamlit as st

from entrevistador.controllers.interview import InterviewController
from entrevistador.services.gemini import provider_scope, resolve_api_key, settings_from_env
from entrevistador.session import InterviewSession


def get_session() -> InterviewSession:
    if "muro_session" not in st.session_state:
        # Conserva entrevistas abiertas antes de la migración a páginas.
        session = InterviewSession(
            interview=st.session_state.get("interview"),
            settings=st.session_state.get("settings"),
            response_mode=st.session_state.get("response_mode", "Audio"),
        )
        if session.interview is not None:
            session.session_id = st.session_state.get("session_id", session.session_id)
            for field, prefix in (
                ("written", "written"),
                ("transcript", "transcript"),
                ("voice", "voice"),
            ):
                value = st.session_state.get(f"{prefix}_{session.turn}")
                if value is not None:
                    setattr(session.draft, field, value)
        session.working_models.update(st.session_state.get("working_models", {}))
        st.session_state.muro_session = session
    return st.session_state.muro_session


@contextmanager
def controller_scope():
    session = get_session()
    settings = session.settings or settings_from_env()
    api_key = resolve_api_key(st.session_state.get("api_key", ""))
    with provider_scope(api_key, settings, session.working_models) as provider:
        yield InterviewController(session, provider, settings)
