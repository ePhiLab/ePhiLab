import streamlit as st

from components.cards import render_feature_card
from components.footer import render_footer
from components.header import render_header


# ============================================================
# P0-D · MAIN ENTRY POINT / PUNTO DE ENTRADA PRINCIPAL
# Spanish: Esta página presenta ePhiKart y dirige al estudiante
#          hacia una única experiencia guiada.
# English: This page introduces ePhiKart and directs the student
#          to a single guided learning experience.
# ============================================================

render_header(
    eyebrow="e(Phi)Lab · MÓDULO 1",
    title="e(Phi)Kart",
    subtitle=(
        "Predicción, experimentación y análisis del movimiento de un "
        "carrito impulsado por energía elástica."
    ),
    badge="Entorno de aprendizaje interactivo",
)


# ============================================================
# PRIMARY CALL TO ACTION / LLAMADO PRINCIPAL A LA ACCIÓN
# Spanish: La actividad integrada es ahora la ruta principal.
# English: The integrated activity is now the primary route.
# ============================================================

st.page_link(
    "modules/ephikart/activity.py",
    label="Iniciar experiencia ePhiKart",
    icon="🚀",
    use_container_width=True,
)

st.caption(
    "La actividad conserva el progreso visible y desbloquea cada etapa "
    "de forma secuencial."
)


# ============================================================
# LEARNING ROUTE / RUTA DE APRENDIZAJE
# Spanish: Se muestran las cinco etapas como mapa de la experiencia,
#          pero sin accesos independientes que rompan el flujo.
# English: The five stages are shown as a map of the experience,
#          without independent shortcuts that break the flow.
# ============================================================

st.markdown(
    """
    <section class="intro-panel">
        <div>
            <span class="section-kicker">RUTA DE TRABAJO</span>
            <h2>Un flujo integrado de cinco etapas</h2>
        </div>
        <p>
            El módulo guía al estudiante desde la formulación de una predicción
            hasta la interpretación de los resultados obtenidos durante el
            experimento.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

items = [
    (
        "01",
        "Predicción",
        "Define los parámetros iniciales y estima el comportamiento esperado.",
    ),
    (
        "02",
        "Experimento",
        "Registra condiciones, observaciones y datos de la experiencia.",
    ),
    (
        "03",
        "Análisis FizziQ",
        "Carga y procesa archivos CSV exportados desde la aplicación.",
    ),
    (
        "04",
        "Comparación",
        "Contrasta las curvas teóricas y experimentales.",
    ),
    (
        "05",
        "Resultados",
        "Resume hallazgos y prepara productos de entrega.",
    ),
]

row1 = st.columns(3, gap="large")

for column, item in zip(row1, items[:3]):
    with column:
        render_feature_card(*item, status="Etapa")

row2 = st.columns([1, 1, 1], gap="large")

with row2[0]:
    render_feature_card(*items[3], status="Etapa")

with row2[1]:
    render_feature_card(*items[4], status="Etapa")

with row2[2]:
    st.markdown(
        """
        <article class="feature-card feature-card--accent">
            <div class="feature-card__top">
                <span class="feature-card__icon">P0</span>
                <span class="feature-card__status">Flujo integrado</span>
            </div>
            <h3>Una sola experiencia</h3>
            <p>
                Las etapas se desbloquean hacia abajo y las anteriores
                permanecen disponibles para consulta.
            </p>
        </article>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER / PIE DE PÁGINA
# Spanish: Se mantiene un único pie de página al final.
# English: A single footer is kept at the end of the page.
# ============================================================

render_footer()
