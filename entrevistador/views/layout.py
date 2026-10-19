"""Menú y configuración compartidos por las cuatro páginas."""

import streamlit as st

from entrevistador.controllers.interview import InterviewController
from entrevistador.services.gemini import resolve_api_key
from entrevistador.views import components as ui
from entrevistador.views import navigation as nav


def sidebar(session):
    with st.sidebar:
        ui.sidebar_brand()
        for path, label, icon in (
            (nav.PREPARATION, "Preparación", "📝"),
            (nav.PRACTICE, "Práctica", "🎙️"),
            (nav.HISTORY, "Historial", "💬"),
            (nav.EVALUATION, "Evaluación", "✨"),
        ):
            st.page_link(path, label=label, icon=icon, use_container_width=True)
        ui.sidebar_note()
        with st.expander("Conexión con Gemini", expanded=False):
            override = st.text_input(
                "Clave de Gemini",
                type="password",
                key="api_key",
                help="Configura GEMINI_API_KEY o GOOGLE_API_KEY en .env, o introduce tu clave aquí.",
            )
            st.caption(
                "Usa tu clave de Google AI Studio. Se aplican las cuotas y tarifas de tu cuenta."
            )
        st.caption(
            "Clave configurada" if resolve_api_key(override) else "Agrega tu clave para comenzar"
        )
        st.divider()
        if session.interview and st.button("Nueva entrevista", use_container_width=True):
            InterviewController(session).reset()
            st.switch_page(nav.PREPARATION)
        with st.expander("Sobre tus datos"):
            st.caption(
                "El texto de la oferta y tus respuestas se envían a Google para la práctica. "
                "El audio se envía solo al transcribir. Las grabaciones no se guardan en disco. "
                "Tu sesión se mantiene en memoria."
            )
