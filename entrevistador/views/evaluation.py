"""Informe final y descarga independiente."""

import streamlit as st

from entrevistador.views import components as ui
from entrevistador.views import navigation as nav


def render(controller):
    if not nav.require_interview(controller):
        return
    interview = controller.interview
    nav.session_progress(interview)
    st.subheader("Tu evaluación")
    if interview.report is None:
        ui.empty_evaluation()
        st.page_link(nav.PRACTICE, label="Continuar práctica", icon="🎙️")
        return
    with st.container(border=True, key="report_card"):
        st.markdown(interview.report)
    st.download_button(
        "Descargar evaluación (.md)",
        data=interview.report,
        file_name="evaluacion.md",
        mime="text/markdown",
    )
    st.caption("Evaluación orientativa generada por IA para tu práctica personal.")
    st.page_link(nav.HISTORY, label="Revisar mis respuestas", icon="💬")
