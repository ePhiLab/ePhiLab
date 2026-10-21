"""ePhiKart — experimental setup / preparación experimental."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation


# ES: Claves persistentes para la preparación experimental.
# EN: Persistent keys for the experimental setup.
EXPERIMENT_DEFAULTS = {
    "exp_group": "",
    "exp_trial": 1,
    "exp_mass_g": 250.0,
    "exp_natural_cm": 8.5,
    "exp_stretched_cm": 15.0,
    "exp_initial_x_cm": 0.0,
    "exp_surface": "Superficie horizontal lisa",
    "exp_release_method": "Liberación manual, sin empuje adicional",
    "exp_measurement_method": "Medición directa",
    "exp_notes": "",
    "exp_prepared": False,
    "exp_saved_snapshot": None,
}


def _initialize_experiment_state() -> None:
    """ES: Inicializa sin borrar respuestas. EN: Initialize without clearing answers."""
    for key, value in EXPERIMENT_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _invalidate_preparation() -> None:
    """ES: Un cambio invalida la confirmación anterior. EN: Edits invalidate confirmation."""
    st.session_state["exp_prepared"] = False


def _validate_setup() -> list[str]:
    """ES: Verifica coherencia física. EN: Check physical consistency."""
    errors = []
    if st.session_state["exp_stretched_cm"] <= st.session_state["exp_natural_cm"]:
        errors.append("La longitud estirada debe ser mayor que la longitud natural.")
    if st.session_state["exp_mass_g"] <= 0:
        errors.append("La masa debe ser mayor que cero.")
    return errors


def _save_setup() -> None:
    """ES: Congela una copia del registro. EN: Freeze a snapshot of the setup."""
    errors = _validate_setup()
    if errors:
        st.session_state["exp_prepared"] = False
        return
    keys = (
        "exp_group", "exp_trial", "exp_mass_g", "exp_natural_cm",
        "exp_stretched_cm", "exp_initial_x_cm", "exp_surface",
        "exp_release_method", "exp_measurement_method", "exp_notes",
    )
    st.session_state["exp_saved_snapshot"] = {
        key: st.session_state[key] for key in keys
    }
    st.session_state["exp_saved_snapshot"]["recorded_at"] = (
        datetime.now().astimezone().isoformat(timespec="seconds")
    )
    st.session_state["exp_prepared"] = True


def render_experiment(
    show_header: bool = True,
    show_footer: bool = True,
    show_top_navigation: bool = False,
) -> None:
    """ES: Renderiza la preparación experimental. EN: Render experimental setup."""
    _initialize_experiment_state()

    if show_top_navigation:
        render_top_navigation()

    if show_header:
        render_header(
            eyebrow="e(Phi)Kart",
            title="Experimento",
            subtitle="Preparación y registro de las condiciones reales del carrito.",
            badge="P2 · Preparación experimental",
        )

    st.markdown("### 1. Preparación experimental")
    st.caption(
        "Registra las condiciones del montaje real. Estos datos corresponden "
        "al experimento, no modifican automáticamente la predicción."
    )

    # ES: Campos apilados para facilitar el uso con una mano en smartphone.
    # EN: Stacked inputs support one-handed use on smartphones.
    with st.container(border=True):
        st.text_input(
            "Grupo o identificador (opcional)", key="exp_group",
            placeholder="Ej.: Grupo 3", on_change=_invalidate_preparation,
        )
        st.number_input(
            "Número de ensayo", min_value=1, max_value=100,
            step=1, key="exp_trial", on_change=_invalidate_preparation,
        )
        st.number_input(
            "Masa total del carrito (g)", min_value=0.1,
            max_value=5000.0, step=1.0, format="%.1f",
            key="exp_mass_g", on_change=_invalidate_preparation,
            help="Masa medida del carrito con los elementos utilizados.",
        )
        st.number_input(
            "Longitud natural de las ligas, L₀ (cm)", min_value=0.1,
            max_value=100.0, step=0.1, format="%.1f",
            key="exp_natural_cm", on_change=_invalidate_preparation,
        )
        st.number_input(
            "Longitud inicial estirada, Lᵢ (cm)", min_value=0.1,
            max_value=100.0, step=0.1, format="%.1f",
            key="exp_stretched_cm", on_change=_invalidate_preparation,
        )
        st.number_input(
            "Posición inicial del carrito, x₀ (cm)",
            min_value=-10000.0, max_value=10000.0, step=1.0,
            format="%.1f", key="exp_initial_x_cm",
            on_change=_invalidate_preparation,
            help="Posición del punto de referencia escogido por el grupo.",
        )
        st.selectbox(
            "Superficie de rodadura",
            options=(
                "Superficie horizontal lisa", "Superficie horizontal rugosa",
                "Otra superficie",
            ), key="exp_surface", on_change=_invalidate_preparation,
        )
        st.selectbox(
            "Procedimiento de liberación",
            options=(
                "Liberación manual, sin empuje adicional",
                "Liberación mediante mecanismo", "Otro procedimiento",
            ), key="exp_release_method", on_change=_invalidate_preparation,
        )
        st.selectbox(
            "Origen de las medidas",
            options=("Medición directa", "Valor estimado", "Mixto"),
            key="exp_measurement_method", on_change=_invalidate_preparation,
        )
        st.text_area(
            "Observaciones del montaje (opcional)", key="exp_notes",
            placeholder="Ej.: alineación, tensión, irregularidades de la pista…",
            on_change=_invalidate_preparation,
        )

    errors = _validate_setup()
    for error in errors:
        st.error(error)

    # ES: Se guardan los datos solamente después de la validación.
    # EN: Data are confirmed only after validation.
    st.button(
        "Guardar condiciones del experimento",
        key="exp_save_setup", type="primary", use_container_width=True,
        on_click=_save_setup, disabled=bool(errors),
    )

    if st.session_state["exp_prepared"]:
        st.success("Condiciones experimentales guardadas para este ensayo.")
        snapshot = st.session_state["exp_saved_snapshot"]
        if snapshot:
            st.caption(
                f"Ensayo {snapshot['exp_trial']} · "
                f"m = {snapshot['exp_mass_g']:.1f} g · "
                f"L₀ = {snapshot['exp_natural_cm']:.1f} cm · "
                f"Lᵢ = {snapshot['exp_stretched_cm']:.1f} cm"
            )
    else:
        st.info("Completa y guarda las condiciones antes de continuar con las mediciones.")

    st.markdown("### 2. Ejecución y mediciones")
    st.caption("P2-C: registro de observaciones y mediciones — siguiente etapa.")

    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_experiment(
        show_header=True, show_footer=True, show_top_navigation=True,
    )
