from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation

render_top_navigation()
render_header(
    eyebrow="e(Phi)Kart",
    title="Comparación",
    subtitle="Contraste entre la predicción del modelo y la evidencia experimental.",
    badge="Módulo preparado",
)
render_placeholder_card(
    "Predicción frente a experimento",
    "Esta página presentará curvas superpuestas, errores, métricas y discusión guiada de resultados.",
)
render_footer()
