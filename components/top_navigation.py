import streamlit as st


def render_top_navigation() -> None:
    """Barra superior compacta para volver al inicio general o al módulo ePhiKart."""

    col1, col2, spacer = st.columns([1.25, 1.25, 3.5], gap="small")

    with col1:
        st.page_link(
            "views/home.py",
            label="Inicio e(Phi)Lab",
            icon="🏠",
            use_container_width=True,
        )

    with col2:
        st.page_link(
            "modules/ephikart/home.py",
            label="Inicio ePhiKart",
            icon="🏎️",
            use_container_width=True,
        )
