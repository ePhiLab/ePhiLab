import streamlit as st


DEFAULT_STATE = {
    "active_module": "e(Phi)Kart",
    "app_version": "0.1.0",
}


def initialize_session_state() -> None:
    """Inicializa variables compartidas por toda la aplicación."""
    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value
