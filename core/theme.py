from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
CSS_FILE = ROOT_DIR / "assets" / "styles" / "main.css"


def load_global_theme() -> None:
    """Carga la hoja de estilos global de la aplicación."""
    if not CSS_FILE.exists():
        st.warning("No se encontró la hoja de estilos global.")
        return

    css = CSS_FILE.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
