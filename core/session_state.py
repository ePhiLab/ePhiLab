import streamlit as st


# ============================================================
# GLOBAL DEFAULT STATE / ESTADO GLOBAL PREDETERMINADO
# Spanish: Estas variables están disponibles para toda la aplicación.
# English: These variables are available throughout the application.
# ============================================================

DEFAULT_STATE = {
    "active_module": "e(Phi)Kart",
    "app_version": "0.1.0",

    # P1-A · GLOBAL OBSERVATION TIME / TIEMPO GLOBAL DE OBSERVACIÓN
    # Spanish: t_obs es la única fuente de verdad temporal de ePhiKart.
    #          Gráficas, métricas, energía, animación y controles espejo
    #          deberán leer y modificar este mismo valor.
    # English: t_obs is ePhiKart's single temporal source of truth.
    #          Charts, metrics, energy, animation, and mirror controls
    #          must read and update this same value.
    "t_obs": 0.0,
}


def initialize_session_state() -> None:
    """
    Spanish: Inicializa las variables compartidas por toda la aplicación
    sin sobrescribir valores que ya existan durante la sesión.

    English: Initializes application-wide shared variables without
    overwriting values that already exist during the session.
    """

    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value

