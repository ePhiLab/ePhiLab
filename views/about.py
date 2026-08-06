import streamlit as st

from components.footer import render_footer
from components.header import render_header


render_header(
    eyebrow="INFORMACIÓN",
    title="Acerca de e(Phi)Lab",
    subtitle="Una arquitectura modular para experimentación, enseñanza y análisis físico.",
    badge="Versión 0.1",
)

st.markdown("## Propósito")
st.write(
    "e(Phi)Lab organiza herramientas digitales de laboratorio en módulos independientes, "
    "manteniendo separadas la interfaz, la lógica física, el procesamiento de datos y la configuración general."
)

st.markdown("## Arquitectura maestra")
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("### Interfaz")
    st.code("views/\ncomponents/", language="text")
    st.markdown("### Modelo físico")
    st.code("physics/ephikart/", language="text")
with col2:
    st.markdown("### Procesamiento de datos")
    st.code("utils/\ndata/", language="text")
    st.markdown("### Configuración")
    st.code("core/", language="text")

st.info(
    "La versión 0.1 establece la identidad, la navegación y la estructura base. "
    "Los componentes dinámicos se incorporarán progresivamente sin alterar esta organización."
)

render_footer()
