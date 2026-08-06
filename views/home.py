import streamlit as st

from components.cards import render_feature_card
from components.footer import render_footer
from components.header import render_header


render_header(
    eyebrow="ESCUELA SUPERIOR POLITÉCNICA DEL LITORAL",
    title="e(Phi)Lab",
    subtitle="Experimenta, analiza y aprende física mediante herramientas interactivas.",
    badge="Plataforma modular de experimentación STEM",
)

st.markdown(
    """
    <section class="intro-panel">
        <div>
            <span class="section-kicker">ENTORNO DIGITAL</span>
            <h2>De la predicción física al análisis experimental</h2>
        </div>
        <p>
            e(Phi)Lab integra modelado, simulación, medición y análisis de datos en una
            arquitectura diseñada para crecer con nuevos proyectos del laboratorio.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(3, gap="large")
with cols[0]:
    render_feature_card(
        "01",
        "Modela",
        "Define parámetros físicos y construye predicciones antes de realizar el experimento.",
    )
with cols[1]:
    render_feature_card(
        "02",
        "Experimenta",
        "Relaciona las variables del modelo con el comportamiento real del sistema.",
    )
with cols[2]:
    render_feature_card(
        "03",
        "Analiza",
        "Procesa datos, visualiza tendencias y compara resultados teóricos y experimentales.",
    )

st.markdown("## Módulo disponible")

left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")
with left:
    st.markdown(
        """
        <section class="module-hero">
            <span class="section-kicker section-kicker--light">MÓDULO 1</span>
            <h2>e(Phi)Kart</h2>
            <p>
                Estudia el movimiento de un carrito impulsado por energía elástica,
                conecta la predicción con la medición y analiza datos exportados desde FizziQ.
            </p>
            <div class="module-hero__tags">
                <span>Predicción</span><span>Movimiento</span><span>FizziQ</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
with right:
    st.markdown("### Capacidades previstas")
    st.markdown(
        """
        - Controles físicos mediante sliders.
        - Barras y métricas actualizadas en tiempo real.
        - Gráficas dinámicas de posición, velocidad y aceleración.
        - Velocímetro sincronizado con el instante de observación.
        - Comparación entre predicción y datos experimentales.
        """
    )
    st.page_link(
        "modules/ephikart/home.py",
        label="Abrir e(Phi)Kart",
        icon="🏎️",
        use_container_width=True,
    )

render_footer()
