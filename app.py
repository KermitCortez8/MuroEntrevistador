"""Ejecutar con: streamlit run app.py."""

import os
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from entrevistador.documents import extract_document, validate_context
from entrevistador.interview import AIProvider, Interview, InterviewError, Settings

load_dotenv()
st.set_page_config(page_title="Muro · Entrevistador IA", page_icon="🎙️", layout="centered")


def main():
    st.title("🎙️ Muro · Entrevistador IA")
    st.write("Practica para tu próxima entrevista de ingeniería, con tu propia voz.")
    interview = st.session_state.get("interview")

    with st.sidebar:
        st.header("Tu sesión")
        api_key = st.text_input(
            "Clave de OpenAI",
            type="password",
            key="api_key",
            help="También puedes configurar OPENAI_API_KEY en el archivo .env.",
        ) or os.getenv("OPENAI_API_KEY", "")
        st.caption("La API requiere una clave y saldo propios; el uso genera cargos en OpenAI.")
        st.divider()
        st.write(
            "1. Agrega una oferta o plantilla.\n2. Escucha o lee la pregunta.\n3. Responde por audio."
        )
        st.caption(
            "Al iniciar, el texto se envía a OpenAI. Al transcribir, también se envía el audio. "
            "La aplicación mantiene la sesión en memoria y no guarda grabaciones en disco."
        )
        if interview and st.button("Nueva entrevista", use_container_width=True):
            for key in list(st.session_state):
                if key != "api_key":
                    del st.session_state[key]
            st.rerun()

    settings = st.session_state.get("settings") or Settings(
        chat_model=os.getenv("OPENAI_CHAT_MODEL") or "gpt-4.1-mini",
        transcription_model=os.getenv("OPENAI_TRANSCRIPTION_MODEL") or "gpt-4o-mini-transcribe",
        tts_model=os.getenv("OPENAI_TTS_MODEL") or "gpt-4o-mini-tts",
    )
    client = OpenAI(api_key=api_key, timeout=60.0, max_retries=1) if api_key else None
    provider = AIProvider(client, settings) if client else None
    try:
        if interview is None:
            setup(provider, settings)
        else:
            conversation(interview, provider)
    finally:
        if client:
            client.close()


def setup(provider, settings):
    st.subheader("Prepara tu entrevista")
    source = st.radio(
        "¿Cómo agregarás la oferta?", ["Pegar texto", "Cargar archivo"], horizontal=True
    )
    context = ""
    if source == "Pegar texto":
        context = st.text_area(
            "Oferta laboral o plantilla de entrevista",
            height=240,
            max_chars=20_000,
            placeholder="Puesto, especialidad, responsabilidades, requisitos y temas a evaluar…",
        )
    else:
        uploaded = st.file_uploader(
            "Oferta o plantilla · máximo 5 MB", type=["txt", "md", "pdf", "docx"]
        )
        if uploaded is not None:
            try:
                context = extract_document(uploaded.name, uploaded.getvalue())
                with st.expander("Texto extraído", expanded=True):
                    st.text(context)
            except ValueError as exc:
                st.error(str(exc))

    left, right = st.columns(2)
    level = left.selectbox("Nivel", ["Inicial", "Intermedio", "Avanzado"], index=1)
    language = right.selectbox("Idioma de la entrevista", ["Español", "English"])
    limit = st.slider("Número de preguntas (incluye repreguntas)", 1, 15, 5)
    if provider is None:
        st.info("Configura tu clave de OpenAI en la barra lateral o en .env para comenzar.")
    if st.button("Comenzar entrevista", type="primary", disabled=provider is None):
        try:
            candidate = Interview(
                context=validate_context(context),
                level=level,
                language="es" if language == "Español" else "en",
                question_limit=limit,
            )
            with st.spinner("Preparando tu primera pregunta…"):
                candidate.start(provider)
            st.session_state.interview = candidate
            st.session_state.settings = settings
            st.session_state.session_id = uuid4().hex
            st.rerun()
        except (ValueError, InterviewError) as exc:
            st.error(str(exc))


def conversation(interview, provider):
    turn = f"{st.session_state.session_id}_{interview.answered}"
    for key in list(st.session_state):
        if key.startswith(("audio_", "transcript_", "voice_")) and (
            interview.report is not None or not key.endswith(turn)
        ):
            del st.session_state[key]
    st.progress(
        interview.answered / interview.question_limit,
        text=f"{interview.answered} de {interview.question_limit} preguntas respondidas · {interview.level}",
    )
    with st.expander("Oferta o plantilla de esta sesión"):
        st.text(interview.context)
    for message in interview.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if interview.report is not None:
        st.subheader("Tu evaluación")
        st.markdown(interview.report)
        st.caption("Evaluación orientativa generada por IA para tu práctica personal.")
    else:
        if provider is None:
            st.info("Agrega tu clave de OpenAI para continuar esta entrevista.")
        voice_key = f"voice_{turn}"
        if st.button("🔊 Escuchar pregunta", disabled=provider is None):
            try:
                if voice_key not in st.session_state:
                    with st.spinner("Generando voz…"):
                        st.session_state[voice_key] = provider.speak(
                            interview.messages[-1]["content"]
                        )
            except InterviewError as exc:
                st.error(str(exc))
        if voice_key in st.session_state:
            st.audio(st.session_state[voice_key], format="audio/mp3")
        st.caption("La voz del entrevistador es generada por IA.")
        st.subheader("Tu respuesta")
        st.caption(
            "Graba, detén la grabación y pulsa Transcribir. Puedes corregir el texto antes de enviarlo."
        )
        audio = st.audio_input("Graba tu respuesta", key=f"audio_{turn}", sample_rate=16000)
        transcript_key = f"transcript_{turn}"
        if st.button("Transcribir respuesta", disabled=audio is None or provider is None):
            try:
                with st.spinner("Transcribiendo tu respuesta…"):
                    st.session_state[transcript_key] = provider.transcribe(
                        audio.getvalue(),
                        interview.language,
                    )
            except InterviewError as exc:
                st.error(str(exc))
        if transcript_key in st.session_state:
            with st.form(f"confirm_{turn}"):
                answer = st.text_area(
                    "Revisa tu transcripción", key=transcript_key, max_chars=12_000
                )
                submitted = st.form_submit_button(
                    "Enviar respuesta",
                    type="primary",
                    disabled=provider is None,
                )
            if submitted:
                try:
                    with st.spinner("Evaluando tu respuesta…"):
                        interview.answer(provider, answer)
                    st.rerun()
                except InterviewError as exc:
                    st.error(str(exc))
        if st.button(
            "Terminar y evaluar lo respondido",
            disabled=not interview.answered or provider is None,
            help="La respuesta pendiente de envío no se incluirá en la evaluación.",
        ):
            try:
                with st.spinner("Preparando tu evaluación…"):
                    interview.finish(provider)
                st.rerun()
            except InterviewError as exc:
                st.error(str(exc))

    st.download_button(
        "Descargar entrevista (.md)",
        data=interview.export_markdown(),
        file_name="entrevista.md",
        mime="text/markdown",
    )


if __name__ == "__main__":
    main()
