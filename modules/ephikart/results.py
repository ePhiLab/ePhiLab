from components.cards import render_placeholder_card
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation


def render_results(
    show_header: bool = True,
    show_footer: bool = True,
    show_top_navigation: bool = False,
) -> None:
    """Renderiza la sección de resultados de ePhiKart."""

    if show_top_navigation:
        render_top_navigation()

    if show_header:
        render_header(
            eyebrow="e(Phi)Kart",
            title="Resultados",
            subtitle=(
                "Síntesis del proceso de modelado, "
                "experimentación y análisis."
            ),
            badge="Módulo preparado",
        )

    render_placeholder_card(
        "Informe de resultados",
        (
            "Se habilitarán resúmenes, tablas, gráficas seleccionadas "
            "y opciones de descarga."
        ),
    )

    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_results(
        show_header=True,
        show_footer=True,
        show_top_navigation=True,
    )
