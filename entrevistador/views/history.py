"""Historial y exportación de la entrevista."""

import streamlit as st

from entrevistador.views import navigation as nav


def render(controller):
    if not nav.require_interview(controller):
        return
    interview = controller.interview
    nav.session_progress(interview)
    st.subheader("Tu conversación")
    with st.expander("Oferta o plantilla de esta sesión"):
        st.text(interview.context)
    for message in interview.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.download_button(
        "Descargar entrevista (.md)",
        data=interview.export_markdown(),
        file_name="entrevista.md",
        mime="text/markdown",
    )
    st.page_link(
        nav.EVALUATION if interview.report is not None else nav.PRACTICE,
        label="Ver evaluación" if interview.report is not None else "Continuar práctica",
    )
