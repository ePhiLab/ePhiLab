from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]


def run_navigation() -> None:
    """Construye y ejecuta la navegación maestra de e(Phi)Lab."""
    

    pages = {
        "Principal": [
            st.Page(
                ROOT_DIR / "views" / "home.py",
                title="Inicio",
                icon="🏠",
                url_path="inicio",
                default=True,
            ),
        ],
        "Módulo 1 · e(Phi)Kart": [
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "home.py",
                title="Portada del módulo",
                icon="🏎️",
                url_path="ephikart",
            ),
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "activity.py",
                title="Actividad ePhiKart",
                icon="🧭",
                url_path="ephikart-actividad",
            ),
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "prediction.py",
                title="Predicción",
                icon="📐",
                url_path="ephikart-prediccion",
            ),
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "experiment.py",
                title="Experimento",
                icon="🧪",
                url_path="ephikart-experimento",
            ),
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "fizziq.py",
                title="Análisis FizziQ",
                icon="📊",
                url_path="ephikart-fizziq",
            ),
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "comparison.py",
                title="Comparación",
                icon="⚖️",
                url_path="ephikart-comparacion",
            ),
            st.Page(
                ROOT_DIR / "modules" / "ephikart" / "results.py",
                title="Resultados",
                icon="📄",
                url_path="ephikart-resultados",
            ),
        ],
        "Información": [
            st.Page(
                ROOT_DIR / "views" / "about.py",
                title="Acerca del proyecto",
                icon="ℹ️",
                url_path="acerca-de",
            ),
        ],
    }

    navigation = st.navigation(
    pages,
    position="hidden",
    )
    navigation.run()
