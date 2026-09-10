from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation


def render_experiment(
    show_header: bool = True,
    show_footer: bool = True,
    show_top_navigation: bool = False,
) -> None:
    """Renderiza la sección experimental de ePhiKart."""

    if show_top_navigation:
        render_top_navigation()

    if show_header:
        render_header(
            eyebrow="e(Phi)Kart",
            title="Experimento",
            subtitle=(
                "Registro estructurado de las condiciones y observaciones "
                "del carrito."
            ),
            badge="Módulo preparado",
        )

    render_placeholder_card(
        "Registro experimental",
        (
            "Esta página alojará los parámetros medidos, observaciones del grupo "
            "y evidencias de la experiencia."
        ),
    )

    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_experiment(
        show_header=True,
        show_footer=True,
        show_top_navigation=True,
    )
