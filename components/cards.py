import html

import streamlit as st


def render_feature_card(icon: str, title: str, description: str, status: str = "Disponible") -> None:
    st.markdown(
        f"""
        <article class="feature-card">
            <div class="feature-card__top">
                <span class="feature-card__icon">{html.escape(icon)}</span>
                <span class="feature-card__status">{html.escape(status)}</span>
            </div>
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(description)}</p>
        </article>
        """,
        unsafe_allow_html=True,
    )


def render_placeholder_card(title: str, description: str, version: str = "Versión 0.2") -> None:
    st.markdown(
        f"""
        <article class="placeholder-card">
            <div class="placeholder-card__version">{html.escape(version)}</div>
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(description)}</p>
        </article>
        """,
        unsafe_allow_html=True,
    )
