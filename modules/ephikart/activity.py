import streamlit as st

from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation
from modules.ephikart.comparison import render_comparison
from modules.ephikart.experiment import render_experiment
from modules.ephikart.fizziq import render_fizziq
from modules.ephikart.prediction import render_prediction
from modules.ephikart.results import render_results


# ============================================================
# P0-D · INTEGRATED ACTIVITY / ACTIVIDAD INTEGRADA
# Spanish: Esta página es la experiencia principal de ePhiKart.
#          Cada etapa se desbloquea hacia abajo y las etapas previas
#          permanecen visibles.
# English: This page is the main ePhiKart experience.
#          Each stage unlocks downward while previous stages remain visible.
# ============================================================

TOTAL_STEPS = 5


# ============================================================
# FLOW STATE / ESTADO DEL FLUJO
# Spanish: ephikart_step guarda la etapa máxima desbloqueada.
# English: ephikart_step stores the highest unlocked stage.
# ============================================================

if "ephikart_step" not in st.session_state:
    st.session_state.ephikart_step = 1


def unlock_step(step: int) -> None:
    """
    Spanish: Desbloquea una nueva etapa sin cerrar las anteriores.
    English: Unlocks a new stage without closing previous stages.
    """

    if step > st.session_state.ephikart_step:
        st.session_state.ephikart_step = min(step, TOTAL_STEPS)


# ============================================================
# TOP NAVIGATION / NAVEGACIÓN SUPERIOR
# Spanish: Se mantiene únicamente la navegación general.
# English: Only the general top navigation is kept.
# ============================================================

render_top_navigation()


# ============================================================
# MAIN HEADER / CABECERA PRINCIPAL
# Spanish: La actividad usa una sola cabecera global.
# English: The activity uses one global header.
# ============================================================

render_header(
    eyebrow="e(Phi)Kart",
    title="Experiencia experimental guiada",
    subtitle=(
        "Predice, experimenta, analiza y compara el movimiento "
        "de un carrito impulsado por una liga elástica."
    ),
    badge="Actividad interactiva",
)


# ============================================================
# PROGRESS INDICATOR / INDICADOR DE PROGRESO
# Spanish: El progreso refleja la última etapa desbloqueada.
# English: Progress reflects the highest unlocked stage.
# ============================================================

current_step = int(st.session_state.ephikart_step)
progress_value = current_step / TOTAL_STEPS

st.progress(progress_value)
st.caption(
    f"Progreso de la actividad: {current_step} de {TOTAL_STEPS} etapas"
)


# ============================================================
# 1. PREDICTION / PREDICCIÓN
# Spanish: La predicción se muestra directamente en el flujo principal.
# English: Prediction is rendered directly inside the main flow.
# ============================================================

st.markdown("---")
st.subheader("1. Predicción")

st.write(
    "Configura el sistema y analiza cómo esperas que se comporte "
    "el carrito antes de realizar el experimento."
)

render_prediction(
    show_header=False,
    show_footer=False,
)

if st.button(
    "Continuar al experimento",
    key="continue_experiment",
    use_container_width=True,
):
    unlock_step(2)


# ============================================================
# 2. EXPERIMENT / EXPERIMENTO
# Spanish: Se incorpora sin navegar a otra página.
# English: This section is embedded without navigating away.
# ============================================================

if st.session_state.ephikart_step >= 2:
    st.markdown("---")
    st.subheader("2. Experimento")

    st.write(
        "Realiza el experimento físico y registra el movimiento "
        "del carrito."
    )

    render_experiment(
        show_header=False,
        show_footer=False,
    )

    if st.button(
        "Continuar al análisis FizziQ",
        key="continue_fizziq",
        use_container_width=True,
    ):
        unlock_step(3)


# ============================================================
# 3. FIZZIQ ANALYSIS / ANÁLISIS FIZZIQ
# Spanish: El análisis de datos se mantiene dentro de la misma página.
# English: Data analysis remains inside the same page.
# ============================================================

if st.session_state.ephikart_step >= 3:
    st.markdown("---")
    st.subheader("3. Análisis FizziQ")

    st.write(
        "Importa y analiza los datos obtenidos con FizziQ."
    )

    render_fizziq(
        show_header=False,
        show_footer=False,
    )

    if st.button(
        "Continuar a comparación",
        key="continue_comparison",
        use_container_width=True,
    ):
        unlock_step(4)


# ============================================================
# 4. COMPARISON / COMPARACIÓN
# Spanish: La comparación aparece debajo de las etapas anteriores.
# English: Comparison appears below all previously unlocked stages.
# ============================================================

if st.session_state.ephikart_step >= 4:
    st.markdown("---")
    st.subheader("4. Comparación")

    st.write(
        "Compara la predicción teórica con los datos experimentales."
    )

    render_comparison(
        show_header=False,
        show_footer=False,
    )

    if st.button(
        "Continuar a resultados",
        key="continue_results",
        use_container_width=True,
    ):
        unlock_step(5)


# ============================================================
# 5. RESULTS / RESULTADOS
# Spanish: La síntesis final cierra la experiencia integrada.
# English: The final synthesis closes the integrated experience.
# ============================================================

if st.session_state.ephikart_step >= 5:
    st.markdown("---")
    st.subheader("5. Resultados")

    st.write(
        "Revisa los resultados finales y prepara la evidencia "
        "de la actividad."
    )

    render_results(
        show_header=False,
        show_footer=False,
    )

    st.success(
        "Has desbloqueado todas las etapas de ePhiKart."
    )


# ============================================================
# GLOBAL FOOTER / PIE DE PÁGINA GLOBAL
# Spanish: Los módulos embebidos no muestran su propio footer.
#          Este es el único pie de página de la actividad.
# English: Embedded modules do not render their own footer.
#          This is the activity's only footer.
# ============================================================

render_footer()
