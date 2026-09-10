import streamlit as st


def render_top_navigation() -> None:
    """Navegación superior compacta para las páginas internas de ePhiKart."""

    st.markdown('<div class="ephikart-top-nav-marker"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="small")

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
