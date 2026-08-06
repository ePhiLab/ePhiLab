import streamlit as st
from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header

render_header(
    eyebrow="e(Phi)Kart",
    title="Predicción del movimiento",
    subtitle="Espacio preparado para configurar el modelo físico y visualizar su respuesta.",
    badge="Estructura disponible",
)

render_placeholder_card(
    "Panel interactivo en desarrollo",
    "Aquí se incorporarán sliders, barras dinámicas, la gráfica temporal y el velocímetro sincronizado.",
)

st.markdown("## Componentes planificados")
cols = st.columns(3, gap="large")
with cols[0]:
    st.metric("Parámetros", "Sliders", border=True)
with cols[1]:
    st.metric("Visualización", "Gráfica dinámica", border=True)
with cols[2]:
    st.metric("Indicador", "Velocímetro", border=True)

render_footer()
