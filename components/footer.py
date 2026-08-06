import streamlit as st


def render_footer() -> None:
    st.markdown(
        """
        <footer class="ephilab-footer">
            <strong>e(Phi)Lab</strong>
            <span>Plataforma interactiva de experimentación STEM</span>
            <span>Versión 0.1</span>
        </footer>
        """,
        unsafe_allow_html=True,
    )
