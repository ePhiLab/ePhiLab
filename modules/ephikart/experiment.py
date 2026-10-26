"""ePhiKart — experimental setup / preparación experimental."""

from __future__ import annotations

from datetime import datetime
import csv
import io
import json

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
    # ES: Mediciones del ensayo; se mantienen durante la sesión.
    # EN: Trial measurements; retained during the session.
    "exp_distance_cm": 0.0,
    "exp_elapsed_s": 0.0,
    "exp_release_observed": "No se pudo determinar",
    "exp_release_s": 0.0,
    "exp_motion_observation": "",
    "exp_measurement_notes": "",
    "exp_measurement_saved": False,
    "exp_measurement_snapshot": None,
}


def _initialize_experiment_state() -> None:
    """ES: Inicializa sin borrar respuestas. EN: Initialize without clearing answers."""
    for key, value in EXPERIMENT_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _invalidate_preparation() -> None:
    """ES: Un cambio invalida la confirmación anterior. EN: Edits invalidate confirmation."""
    st.session_state["exp_prepared"] = False
    # ES: Las mediciones previas ya no corresponden al montaje modificado.
    # EN: Previous measurements no longer correspond to the edited setup.
    st.session_state["exp_measurement_saved"] = False
    st.session_state["exp_measurement_snapshot"] = None
    st.session_state["exp_p3_ready"] = False
    st.session_state["exp_p3_record"] = None


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
    # ES: Un nuevo guardado de condiciones invalida mediciones anteriores.
    # EN: Saving setup again invalidates previously saved measurements.
    st.session_state["exp_measurement_saved"] = False
    st.session_state["exp_measurement_snapshot"] = None
    st.session_state["exp_p3_ready"] = False
    st.session_state["exp_p3_record"] = None



def _validate_measurements() -> list[str]:
    """ES: Valida el registro manual. EN: Validate the manual record."""
    errors = []
    if st.session_state["exp_elapsed_s"] <= 0:
        errors.append("El tiempo de desplazamiento debe ser mayor que 0 s.")
    if st.session_state["exp_distance_cm"] < 0:
        errors.append("La distancia recorrida no puede ser negativa.")
    if st.session_state["exp_release_observed"] == "Sí, se midió el instante":
        if st.session_state["exp_release_s"] > st.session_state["exp_elapsed_s"]:
            errors.append("La liberación no puede ocurrir después del tiempo total registrado.")
    return errors


def _invalidate_measurements() -> None:
    """ES: Señala que el registro cambió. EN: Mark the record as edited."""
    st.session_state["exp_measurement_saved"] = False
    st.session_state["exp_p3_ready"] = False
    st.session_state["exp_p3_record"] = None


def _save_measurements() -> None:
    """ES: Guarda una copia vinculada al montaje. EN: Save a setup-linked copy."""
    if not st.session_state.get("exp_prepared") or _validate_measurements():
        st.session_state["exp_measurement_saved"] = False
        return
    fields = (
        "exp_distance_cm", "exp_elapsed_s", "exp_release_observed",
        "exp_motion_observation", "exp_measurement_notes",
    )
    snapshot = {field: st.session_state[field] for field in fields}
    snapshot["exp_release_s"] = (
        st.session_state["exp_release_s"]
        if st.session_state["exp_release_observed"] == "Sí, se midió el instante"
        else None
    )
    snapshot["trial"] = st.session_state["exp_saved_snapshot"]["exp_trial"]
    snapshot["setup_recorded_at"] = st.session_state["exp_saved_snapshot"]["recorded_at"]
    snapshot["recorded_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    st.session_state["exp_measurement_snapshot"] = snapshot
    st.session_state["exp_measurement_saved"] = True


def _render_measurements() -> None:
    """ES: Formulario vertical P2-C. EN: Vertical P2-C form."""
    st.markdown("## 2.2. Ejecución y mediciones")
    st.caption(
        "Registra lo observado durante el ensayo. En P3 se analizarán los "
        "datos del video mediante FizziQ. No inventes valores que no mediste."
    )
    if not st.session_state["exp_prepared"]:
        st.info("Guarda primero las condiciones del experimento para habilitar el registro.")
        return

    with st.container(border=True):
        st.caption(f"Ensayo {st.session_state['exp_saved_snapshot']['exp_trial']} · Registro manual")
        st.number_input(
            "Distancia recorrida, Δs (cm)", min_value=0.0, max_value=100000.0,
            step=1.0, format="%.1f", key="exp_distance_cm",
            on_change=_invalidate_measurements,
            help="Longitud total recorrida sobre la pista; no confundir con la posición final.",
        )
        st.number_input(
            "Tiempo total observado, Δt (s)", min_value=0.0, max_value=3600.0,
            step=0.02, format="%.2f", key="exp_elapsed_s",
            on_change=_invalidate_measurements,
            help="Tiempo medido desde la liberación inicial hasta el evento final observado.",
        )
        st.selectbox(
            "¿Se identificó el instante en que las ligas se soltaron?",
            options=("No se pudo determinar", "Sí, se midió el instante", "No se soltaron durante el registro"),
            key="exp_release_observed", on_change=_invalidate_measurements,
        )
        if st.session_state["exp_release_observed"] == "Sí, se midió el instante":
            st.number_input(
                "Instante de liberación de las ligas (s)",
                min_value=0.0, max_value=3600.0, step=0.02, format="%.2f",
                key="exp_release_s", on_change=_invalidate_measurements,
            )
        st.text_area(
            "¿Qué ocurrió durante el desplazamiento?",
            key="exp_motion_observation", on_change=_invalidate_measurements,
            placeholder="Ej.: las ligas se soltaron y el carrito siguió avanzando…",
        )
        st.text_area(
            "Incidencias o dificultades de medición (opcional)",
            key="exp_measurement_notes", on_change=_invalidate_measurements,
            placeholder="Ej.: movimiento lateral, problemas de cronometraje…",
        )

    errors = _validate_measurements()
    for error in errors:
        st.error(error)
    # ES: Contraste del botón primario en el tema ESPOL.
    # EN: Primary button contrast in the ESPOL theme.
    st.markdown("""<style>
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primary"] p {color:#FFFFFF !important;}
    </style>""", unsafe_allow_html=True)
    st.button(
        "Guardar mediciones del ensayo", key="exp_save_measurements",
        type="primary", use_container_width=True,
        disabled=bool(errors), on_click=_save_measurements,
    )
    if st.session_state["exp_measurement_saved"]:
        st.success("Mediciones guardadas en esta sesión.")
        st.caption(
            "Se conserva una copia vinculada a las condiciones guardadas. "
            "P3 permitirá incorporar y analizar el archivo CSV de FizziQ."
        )



def _build_experiment_record() -> dict | None:
    """ES: Une copias confirmadas; EN: Join confirmed snapshots only."""
    setup = st.session_state.get("exp_saved_snapshot")
    measurement = st.session_state.get("exp_measurement_snapshot")
    if not st.session_state.get("exp_prepared") or not setup:
        return None
    if not st.session_state.get("exp_measurement_saved") or not measurement:
        return None
    # ES: Prefijos evitan colisiones y mantienen unidades explícitas.
    # EN: Prefixes avoid collisions and preserve explicit units.
    record = {
        "schema_version": "ephikart-exp-v1",
        "source": "Registro manual ePhiKart (no es CSV FizziQ)",
        **setup,
        **{f"measurement_{key}": value for key, value in measurement.items()},
    }
    return record


def _render_experiment_handoff() -> None:
    """ES: Descarga y entrega a P3; EN: Download and hand off to P3."""
    st.markdown("## 2.3. Conservación del registro y preparación para FizziQ")
    st.caption(
        "Descarga el registro manual del ensayo. El análisis de posiciones "
        "obtenidas del video se realizará posteriormente en FizziQ."
    )
    record = _build_experiment_record()
    if record is None:
        st.info("Guarda primero las condiciones y las mediciones del ensayo.")
        st.session_state["exp_p3_ready"] = False
        st.session_state["exp_p3_record"] = None
        return

    # ES: Esta copia es el contrato de datos para la siguiente etapa.
    # EN: This copy is the data contract for the next stage.
    st.session_state["exp_p3_record"] = record.copy()
    st.session_state["exp_p3_ready"] = True

    trial = int(record["exp_trial"])
    group = str(record.get("exp_group", "")).strip() or "sin_grupo"
    safe_group = "".join(c if c.isalnum() or c in "-_" else "_" for c in group)[:35]
    basename = f"ePhiKart_ensayo_{trial}_{safe_group}"

    # ES: JSON preserva los tipos y los valores nulos.
    # EN: JSON preserves types and null values.
    json_data = json.dumps(record, ensure_ascii=False, indent=2)
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=list(record.keys()))
    writer.writeheader()
    writer.writerow(record)

    with st.container(border=True):
        st.success(f"Ensayo {trial} listo para la siguiente etapa.")
        st.caption(
            "Los datos siguen en la sesión de Streamlit. Descarga una copia "
            "antes de cerrar la pestaña o reiniciar la aplicación."
        )
        st.download_button(
            "Descargar registro experimental (CSV)",
            data=csv_buffer.getvalue().encode("utf-8-sig"),
            file_name=f"{basename}.csv",
            mime="text/csv",
            use_container_width=True,
            key="exp_download_csv",
        )
        st.download_button(
            "Descargar respaldo del ensayo (JSON)",
            data=json_data.encode("utf-8"),
            file_name=f"{basename}.json",
            mime="application/json",
            use_container_width=True,
            key="exp_download_json",
        )
        st.caption(
            "Este CSV contiene una fila de mediciones manuales. "
            "No debe importarse como trayectoria temporal de FizziQ."
        )


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

    st.markdown("## 2.1. Preparación experimental")
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

    # ES: Registro P2-C, vinculado al montaje previamente confirmado.
    # EN: P2-C recording, linked to the previously confirmed setup.
    _render_measurements()

    # ES: P2-D/E ofrece respaldo y un registro compartido con P3.
    # EN: P2-D/E offers backups and a shared record for P3.
    _render_experiment_handoff()

    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_experiment(
        show_header=True, show_footer=True, show_top_navigation=True,
    )
