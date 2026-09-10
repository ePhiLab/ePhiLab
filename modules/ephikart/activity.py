import streamlit as st

from modules.ephikart.prediction import render_prediction
from components.header import render_header
from components.footer import render_footer
from components.top_navigation import render_top_navigation


# ============================================================
# Estado inicial del flujo
# ============================================================

if "ephikart_step" not in st.session_state:
    st.session_state.ephikart_step = 1


def unlock_step(step: int) -> None:
    """Desbloquea una nueva etapa sin cerrar las anteriores."""
    if step > st.session_state.ephikart_step:
        st.session_state.ephikart_step = step


# ============================================================
# Navegación superior
# ============================================================

render_top_navigation()


# ============================================================
# Cabecera principal
# ============================================================

render_header(
    eyebrow="e(Phi)Kart",
    title="Experiencia experimental guiada",
    subtitle=(
        "Predice, observa, analiza y compara el movimiento "
        "de un carrito impulsado por una liga elástica."
    ),
    badge="Actividad interactiva",
)

# ============================================================
# Indicador de progreso
# ============================================================

TOTAL_STEPS = 5
current_step = st.session_state.ephikart_step

progress_value = current_step / TOTAL_STEPS

st.progress(progress_value)

st.caption(
    f"Progreso de la actividad: {current_step} de {TOTAL_STEPS} etapas"
)


# ============================================================
# 1. PREDICCIÓN
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
# 2. EXPERIMENTO
# ============================================================

if st.session_state.ephikart_step >= 2:

    st.markdown("---")
    st.subheader("2. Experimento")

    st.write(
        "Realiza el experimento físico y registra el movimiento "
        "del carrito."
    )

    st.page_link(
        "modules/ephikart/experiment.py",
        label="Abrir guía del experimento",
        icon="🧪",
        use_container_width=True,
    )

    if st.button(
        "Continuar al análisis FizziQ",
        key="continue_fizziq",
        use_container_width=True,
    ):
        unlock_step(3)


# ============================================================
# 3. ANÁLISIS FIZZIQ
# ============================================================

if st.session_state.ephikart_step >= 3:

    st.markdown("---")
    st.subheader("3. Análisis FizziQ")

    st.write(
        "Importa y analiza los datos obtenidos con FizziQ."
    )

    st.page_link(
        "modules/ephikart/fizziq.py",
        label="Abrir análisis FizziQ",
        icon="📊",
        use_container_width=True,
    )

    if st.button(
        "Continuar a comparación",
        key="continue_comparison",
        use_container_width=True,
    ):
        unlock_step(4)


# ============================================================
# 4. COMPARACIÓN
# ============================================================

if st.session_state.ephikart_step >= 4:

    st.markdown("---")
    st.subheader("4. Comparación")

    st.write(
        "Compara la predicción teórica con los datos experimentales."
    )

    st.page_link(
        "modules/ephikart/comparison.py",
        label="Abrir comparación",
        icon="⚖️",
        use_container_width=True,
    )

    if st.button(
        "Continuar a resultados",
        key="continue_results",
        use_container_width=True,
    ):
        unlock_step(5)


# ============================================================
# 5. RESULTADOS
# ============================================================

if st.session_state.ephikart_step >= 5:

    st.markdown("---")
    st.subheader("5. Resultados")

    st.write(
        "Revisa los resultados finales y prepara la evidencia "
        "de la actividad."
    )

    st.page_link(
        "modules/ephikart/results.py",
        label="Abrir resultados",
        icon="📄",
        use_container_width=True,
    )

    st.success("Has desbloqueado todas las etapas de ePhiKart.")


# ============================================================
# Pie de página
# ============================================================

render_footer()
