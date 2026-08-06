from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT_DIR / "assets" / "logos" / "logo_espol.png"


def render_sidebar_brand() -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)

        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand__name">e(Phi)Lab</div>
                <div class="sidebar-brand__tagline">Laboratorio digital STEM</div>
                <div class="sidebar-brand__module">Módulo activo · e(Phi)Kart</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
