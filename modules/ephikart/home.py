import streamlit as st

from components.cards import render_feature_card
from components.footer import render_footer
from components.header import render_header


render_header(
    eyebrow="e(Phi)Lab · MÓDULO 1",
    title="e(Phi)Kart",
    subtitle="Predicción, experimentación y análisis del movimiento de un carrito impulsado por energía elástica.",
    badge="Entorno de aprendizaje interactivo",
)

st.markdown(
    """
    <section class="intro-panel">
        <div>
            <span class="section-kicker">RUTA DE TRABAJO</span>
            <h2>Un flujo integrado de cinco etapas</h2>
        </div>
        <p>
            El módulo guía al estudiante desde la formulación de una predicción hasta la
            interpretación de los resultados obtenidos durante el experimento.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

items = [
    ("01", "Predicción", "Define los parámetros iniciales y estima el comportamiento esperado."),
    ("02", "Experimento", "Registra condiciones, observaciones y datos de la experiencia."),
    ("03", "Análisis FizziQ", "Carga y procesa archivos CSV exportados desde la aplicación."),
    ("04", "Comparación", "Contrasta las curvas teóricas y experimentales."),
    ("05", "Resultados", "Resume hallazgos y prepara productos de entrega."),
]

row1 = st.columns(3, gap="large")
for column, item in zip(row1, items[:3]):
    with column:
        render_feature_card(*item, status="Preparado")

row2 = st.columns([1, 1, 1], gap="large")
with row2[0]:
    render_feature_card(*items[3], status="Preparado")
with row2[1]:
    render_feature_card(*items[4], status="Preparado")
with row2[2]:
    st.markdown(
        """
        <article class="feature-card feature-card--accent">
            <div class="feature-card__top">
                <span class="feature-card__icon">V0.2</span>
                <span class="feature-card__status">Próxima etapa</span>
            </div>
            <h3>Panel dinámico</h3>
            <p>Sliders, barras en tiempo real, gráfica sincronizada y velocímetro.</p>
        </article>
        """,
        unsafe_allow_html=True,
    )

st.markdown("## Acceso rápido")
quick = st.columns(3, gap="medium")
with quick[0]:
    st.page_link("modules/ephikart/prediction.py", label="Ir a Predicción", icon="📐", use_container_width=True)
with quick[1]:
    st.page_link("modules/ephikart/experiment.py", label="Ir a Experimento", icon="🧪", use_container_width=True)
with quick[2]:
    st.page_link("modules/ephikart/fizziq.py", label="Ir a FizziQ", icon="📊", use_container_width=True)

render_footer()
