from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header

render_header(
    eyebrow="e(Phi)Kart",
    title="Resultados",
    subtitle="Síntesis del proceso de modelado, experimentación y análisis.",
    badge="Módulo preparado",
)
render_placeholder_card(
    "Informe de resultados",
    "Se habilitarán resúmenes, tablas, gráficas seleccionadas y opciones de descarga.",
)
render_footer()
