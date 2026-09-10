from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation

render_header(
    eyebrow="e(Phi)Kart",
    title="Experimento",
    subtitle="Registro estructurado de las condiciones y observaciones del carrito.",
    badge="Módulo preparado",
)
render_placeholder_card(
    "Registro experimental",
    "Esta página alojará los parámetros medidos, observaciones del grupo y evidencias de la experiencia.",
)
render_footer()
