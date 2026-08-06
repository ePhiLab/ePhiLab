import html

import streamlit as st


def render_header(
    eyebrow: str,
    title: str,
    subtitle: str,
    badge: str | None = None,
) -> None:
    badge_html = (
        f'<span class="ephilab-header__badge">{html.escape(badge)}</span>'
        if badge
        else ""
    )

    st.markdown(
        f"""
        <section class="ephilab-header">
            <div class="ephilab-header__content">
                <div class="ephilab-header__eyebrow">{html.escape(eyebrow)}</div>
                <h1>{html.escape(title)}</h1>
                <p>{html.escape(subtitle)}</p>
                {badge_html}
            </div>
            <div class="ephilab-header__mark" aria-hidden="true">Φ</div>
        </section>
        """,
        unsafe_allow_html=True,
    )
