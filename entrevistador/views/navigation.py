"""Rutas registradas en st.navigation, compartidas por enlaces y redirecciones."""

import streamlit as st

PREPARATION = "entrevistador/pages/preparacion.py"
PRACTICE = "entrevistador/pages/practica.py"
HISTORY = "entrevistador/pages/historial.py"
EVALUATION = "entrevistador/pages/evaluacion.py"


def pages():
    return [
        st.Page(PREPARATION, title="Preparación", default=True),
        st.Page(PRACTICE, title="Práctica", url_path="practica"),
        st.Page(HISTORY, title="Historial", url_path="historial"),
        st.Page(EVALUATION, title="Evaluación", url_path="evaluacion"),
    ]


def require_interview(controller) -> bool:
    if controller.interview is not None:
        return True
    st.info("Primero prepara una entrevista para acceder a esta página.")
    st.page_link(PREPARATION, label="Preparar mi entrevista")
    return False


def session_progress(interview):
    answered, level, status = st.columns(3)
    answered.metric("Respuestas", f"{interview.answered} / {interview.question_limit}")
    level.metric("Nivel", interview.level)
    status.metric("Sesión", "Completada" if interview.report is not None else "En práctica")
    st.progress(interview.answered / interview.question_limit)
