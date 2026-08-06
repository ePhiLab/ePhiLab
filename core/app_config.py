import streamlit as st


APP_NAME = "e(Phi)Lab"
APP_ICON = "⚙️"


def configure_app() -> None:
    """Configura los metadatos generales de Streamlit."""
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get help": None,
            "Report a bug": None,
            "About": (
                "e(Phi)Lab es una plataforma interactiva para experimentación, "
                "modelado y aprendizaje STEM."
            ),
        },
    )
