from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation

render_top_navigation()
render_header(
    eyebrow="e(Phi)Kart",
    title="Análisis FizziQ",
    subtitle="Importación y procesamiento robusto de archivos CSV exportados desde FizziQ.",
    badge="Módulo preparado",
)
render_placeholder_card(
    "Importador CSV",
    "Se incorporará detección de separador, limpieza de columnas, selección de ejes y ajustes matemáticos.",
)
render_footer()
