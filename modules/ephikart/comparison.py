from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation


def render_comparison(
    show_header: bool = True,
    show_footer: bool = True,
    show_top_navigation: bool = False,
) -> None:
    """Renderiza la sección de comparación de ePhiKart."""

    if show_top_navigation:
        render_top_navigation()

    if show_header:
        render_header(
            eyebrow="e(Phi)Kart",
            title="Comparación",
            subtitle=(
                "Contraste entre la predicción del modelo "
                "y la evidencia experimental."
            ),
            badge="Módulo preparado",
        )

    render_placeholder_card(
        "Predicción frente a experimento",
        (
            "Esta página presentará curvas superpuestas, errores, "
            "métricas y discusión guiada de resultados."
        ),
    )

    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_comparison(
        show_header=True,
        show_footer=True,
        show_top_navigation=True,
    )
