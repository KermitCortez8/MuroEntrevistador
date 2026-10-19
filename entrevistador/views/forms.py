"""Sincroniza widgets efímeros con los borradores persistentes de la sesión."""

import streamlit as st


def seed(key, value):
    if key not in st.session_state:
        st.session_state[key] = value
    return key


def save_field(target, field, key):
    setattr(target, field, st.session_state[key])


def save_recording(draft, key):
    audio = st.session_state[key]
    draft.recording = audio.getvalue() if audio is not None else None
