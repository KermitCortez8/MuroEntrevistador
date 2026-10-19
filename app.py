"""Entrada y navegación de Muro. Ejecutar con: streamlit run app.py."""

import streamlit as st
from dotenv import load_dotenv

from entrevistador.runtime import get_session
from entrevistador.views import components, layout, navigation

load_dotenv()
st.set_page_config(page_title="Muro · Entrevistador IA", page_icon="🎙️", layout="wide")


def main():
    session = get_session()
    components.apply_design()
    current_page = st.navigation(navigation.pages(), position="hidden")
    layout.sidebar(session)
    components.header(session.interview, current_page.title)
    current_page.run()
    components.footer()


if __name__ == "__main__":
    main()
