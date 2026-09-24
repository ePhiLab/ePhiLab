from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation
from physics.ephikart.simulation import (
    ElasticKartParameters,
    instantaneous_state,
    simulate_motion,
)


ESPOL_BLUE = "#001C43"
SECONDARY_BLUE = "#123B68"
INTERACTIVE_BLUE = "#1677B8"
TECH_CYAN = "#38A9E0"

POSITION_GREEN = "#16834B"
ACCELERATION_RED = "#C0392B"

TEXT_COLOR = "#102A43"
MUTED_TEXT = "#627D98"
GRID_COLOR = "rgba(98, 125, 152, 0.18)"


# ============================================================
# P1-A / P1-B · GLOBAL TIME STATE / ESTADO TEMPORAL GLOBAL
# Spanish: t_obs es la única fuente de verdad temporal.
#          Los sliders t_general, t_x, t_v y t_a son controles
#          espejo que siempre representan el mismo instante.
# English: t_obs is the single temporal source of truth.
#          Sliders t_general, t_x, t_v, and t_a are mirror
#          controls that always represent the same instant.
# ============================================================

TIME_SLIDER_KEYS = (
    "t_general",
    "t_x",
    "t_v",
    "t_a",
    "t_energy",
)

# P1-M · FINE TIME CONTROL / CONTROL TEMPORAL FINO
# Spanish: Todos los controles temporales usan la misma resolución.
# English: All temporal controls use the same resolution.
TIME_STEP = 0.02
TIME_INPUT_KEY = "t_manual"


def clamp_observation_time(
    value: float,
    duration: float,
) -> float:
    """
    Spanish: Limita el tiempo de observación al intervalo válido.
    English: Clamps observation time to the valid interval.
    """

    return max(0.0, min(float(value), float(duration)))


def prepare_observation_time_state(duration: float) -> None:
    """
    Spanish: Prepara t_obs y sincroniza los sliders espejo antes
             de dibujar los widgets.
    English: Prepares t_obs and synchronizes mirror sliders before
             rendering the widgets.
    """

    current_time = clamp_observation_time(
        st.session_state.get("t_obs", 0.0),
        duration,
    )

    st.session_state["t_obs"] = current_time

    for slider_key in TIME_SLIDER_KEYS:
        st.session_state[slider_key] = current_time

    # Spanish: La casilla numérica refleja el mismo t_obs.
    # English: The numeric input mirrors the same t_obs.
    st.session_state[TIME_INPUT_KEY] = current_time


def sync_observation_time(
    source_key: str,
    duration: float,
) -> None:
    """
    Spanish: Copia el valor del slider modificado hacia t_obs y
             hacia todos los demás sliders espejo.
    English: Copies the changed slider value into t_obs and all
             remaining mirror sliders.
    """

    new_time = clamp_observation_time(
        st.session_state.get(source_key, 0.0),
        duration,
    )

    st.session_state["t_obs"] = new_time

    for slider_key in TIME_SLIDER_KEYS:
        st.session_state[slider_key] = new_time

    st.session_state[TIME_INPUT_KEY] = new_time


def sync_manual_observation_time(duration: float) -> None:
    """
    Spanish: Valida el tiempo escrito manualmente. Si está fuera del
             intervalo [0, t_max], reinicia t_obs a 0.0 s.
    English: Validates manually entered time. If it is outside the
             [0, t_max] interval, t_obs resets to 0.0 s.
    """

    requested_time = float(st.session_state.get(TIME_INPUT_KEY, 0.0))
    new_time = requested_time if 0.0 <= requested_time <= duration else 0.0

    st.session_state["t_obs"] = new_time
    st.session_state[TIME_INPUT_KEY] = new_time
    for slider_key in TIME_SLIDER_KEYS:
        st.session_state[slider_key] = new_time


def step_observation_time(delta: float, duration: float) -> None:
    """
    Spanish: Avanza o retrocede t_obs un paso, respetando los límites.
    English: Moves t_obs one step forward or backward within the limits.
    """

    current_time = float(st.session_state.get("t_obs", 0.0))
    new_time = clamp_observation_time(current_time + delta, duration)
    # Spanish: Redondear evita residuos binarios como 2.1000000001.
    # English: Rounding avoids binary residues such as 2.1000000001.
    new_time = round(new_time, 2)

    st.session_state["t_obs"] = new_time
    st.session_state[TIME_INPUT_KEY] = new_time
    for slider_key in TIME_SLIDER_KEYS:
        st.session_state[slider_key] = new_time


def normalize_physical_control_state() -> None:
    """
    Spanish: Corrige valores guardados por versiones anteriores para que
             los nuevos rangos físicos no bloqueen los sliders.
    English: Corrects values saved by earlier versions so the new physical
             ranges cannot leave sliders in an invalid state.
    """

    limits = {
        "kart_natural_length": (0.07, 0.10, 0.085),
        "kart_initial_length": (0.101, 0.20, 0.15),
        "kart_spring_constant": (5.0, 20.0, 10.0),
        "kart_duration": (1.0, 5.0, 4.0),
    }

    for key, (minimum, maximum, default) in limits.items():
        if key in st.session_state:
            value = float(st.session_state[key])
            if not minimum <= value <= maximum:
                st.session_state[key] = default


def reset_prediction() -> None:
    """
    Spanish: Restablece parámetros y controles temporales.
    English: Resets parameters and temporal controls.
    """

    keys_to_remove = [
        "kart_initial_position",
        "kart_initial_velocity",
        "kart_natural_length",
        "kart_initial_length",
        "kart_spring_constant",
        "kart_mass",
        "kart_friction",
        "kart_duration",

        # P1-A / P1-B · GLOBAL TIME / TIEMPO GLOBAL
        # Spanish: Se elimina también la clave antigua para evitar
        #          conservar estados de versiones previas.
        # English: The legacy key is also removed to avoid keeping
        #          state from earlier versions.
        "kart_observation_time",
        "t_obs",
        "t_general",
        "t_x",
        "t_v",
        "t_a",
        "t_energy",
        "t_manual",
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)


def slice_until_time(
    time: np.ndarray,
    values: np.ndarray,
    observation_time: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Recorta una serie hasta el instante seleccionado."""

    valid_mask = time <= observation_time

    visible_time = time[valid_mask]
    visible_values = values[valid_mask]

    # Garantiza que aparezca al menos el primer punto.
    if visible_time.size == 0:
        visible_time = time[:1]
        visible_values = values[:1]

    return visible_time, visible_values


def build_progressive_chart(
    *,
    complete_time: np.ndarray,
    complete_values: np.ndarray,
    observation_time: float,
    observation_value: float,
    release_time: float | None,
    title: str,
    y_title: str,
    line_name: str,
    line_color: str,
) -> go.Figure:
    """
    Construye una gráfica que solo muestra la curva hasta el tiempo observado.
    """

    visible_time, visible_values = slice_until_time(
        complete_time,
        complete_values,
        observation_time,
    )

    figure = go.Figure()
    # ========================================================
    # P1-C.1 · HIDE FUTURE TRAJECTORY / OCULTAR TRAYECTORIA FUTURA
    # Spanish: No se dibuja la parte de la trayectoria posterior
    #          a t_obs. El estudiante construye la gráfica conforme
    #          avanza el tiempo de observación.
    # English: The trajectory after t_obs is not displayed.
    #          The student builds the graph progressively as the
    #          observation time advances.
    # ========================================================


    
    # Parte ya recorrida de la curva.
    figure.add_trace(
        go.Scatter(
            x=visible_time,
            y=visible_values,
            mode="lines",
            name=line_name,
            line={
                "color": line_color,
                "width": 4,
            },
            fill="tozeroy" if title == "Velocidad vs. tiempo" else None,
            fillcolor=(
                "rgba(22, 119, 184, 0.10)"
                if title == "Velocidad vs. tiempo"
                else None
            ),
            hovertemplate=(
                "t = %{x:.2f} s"
                f"<br>{y_title} = %{{y:.3f}}"
                "<extra></extra>"
            ),
        )
    )

    # Punto del instante actual.
    figure.add_trace(
        go.Scatter(
            x=[observation_time],
            y=[observation_value],
            mode="markers",
            name="Instante actual",
            marker={
                "size": 13,
                "color": line_color,
                "line": {
                    "color": "#FFFFFF",
                    "width": 3,
                },
            },
            hovertemplate=(
                "t = %{x:.2f} s"
                f"<br>{y_title} = %{{y:.3f}}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_vline(
        x=observation_time,
        line_width=1.5,
        line_dash="dash",
        line_color=INTERACTIVE_BLUE,
    )

    figure.add_annotation(
        x=observation_time,
        y=0,
        yref="paper",
        text=f"{observation_time:.2f} s",
        showarrow=False,
        yshift=-30,
        bgcolor=INTERACTIVE_BLUE,
        bordercolor=INTERACTIVE_BLUE,
        font={
            "color": "#FFFFFF",
            "size": 11,
        },
    )

    if release_time is not None:
        figure.add_vline(
            x=release_time,
            line_width=1.2,
            line_dash="dash",
            line_color="#303030",
        )

        figure.add_annotation(
            x=release_time,
            y=0.94,
            yref="paper",
            text=(
                "La liga se suelta"
                f"<br>t = {release_time:.2f} s"
            ),
            showarrow=False,
            bgcolor="#FFFFFF",
            bordercolor="#B8C4D0",
            borderwidth=1,
            borderpad=5,
            font={
                "color": TEXT_COLOR,
                "size": 11,
            },
        )

    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 17,
                "color": ESPOL_BLUE,
            },
        },
        height=410,
        margin={
            "l": 15,
            "r": 15,
            "t": 55,
            "b": 45,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        hovermode="closest",
        font={
            "family": "Inter, Segoe UI, Arial",
            "color": TEXT_COLOR,
        },
        xaxis={
            "title": "Tiempo, t (s)",
            "range": [
                float(complete_time[0]),
                float(complete_time[-1]),
            ],
            "gridcolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
        },
        yaxis={
            "title": y_title,
            "gridcolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
        },
    )

    return figure


def build_speedometer(
    velocity: float,
    maximum_speed: float,
) -> go.Figure:
    """Construye el velocímetro sincronizado con el slider temporal."""

    gauge_limit = max(1.0, maximum_speed * 1.15)

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=abs(velocity),
            number={
                "suffix": " m/s",
                "valueformat": ".2f",
                "font": {
                    "size": 30,
                    "color": ESPOL_BLUE,
                },
            },
            title={
                "text": "Velocidad instantánea",
                "font": {
                    "size": 15,
                    "color": ESPOL_BLUE,
                },
            },
            gauge={
                "shape": "angular",
                "axis": {
                    "range": [0, gauge_limit],
                    "tickwidth": 1,
                    "tickcolor": ESPOL_BLUE,
                },
                "bar": {
                    "color": ESPOL_BLUE,
                    "thickness": 0.25,
                },
                "bgcolor": "#FFFFFF",
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, gauge_limit * 0.45],
                        "color": "rgba(56, 169, 224, 0.18)",
                    },
                    {
                        "range": [
                            gauge_limit * 0.45,
                            gauge_limit * 0.75,
                        ],
                        "color": "rgba(22, 119, 184, 0.20)",
                    },
                    {
                        "range": [
                            gauge_limit * 0.75,
                            gauge_limit,
                        ],
                        "color": "rgba(0, 28, 67, 0.16)",
                    },
                ],
                "threshold": {
                    "line": {
                        "color": TECH_CYAN,
                        "width": 5,
                    },
                    "thickness": 0.85,
                    "value": abs(velocity),
                },
            },
        )
    )

    figure.update_layout(
        # Mobile-first: compact gauge so cart + controls + gauge
        # fit within one smartphone viewport after a short scroll.
        # Mobile-first: velocímetro compacto para que carrito +
        # controles + gauge quepan en una pantalla del celular.
        height=175,
        margin={
            "l": 18,
            "r": 18,
            "t": 38,
            "b": 0,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Inter, Segoe UI, Arial",
            "color": TEXT_COLOR,
        },
    )

    return figure

def _image_file_to_data_uri(image_path: Path) -> str:
    """
    Spanish: Convierte la imagen local del carrito en un URI embebido
             para que Plotly pueda desplazarla dentro de la simulación.
    English: Converts the local cart image into an embedded URI so
             Plotly can move it inside the simulation.
    """

    encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def build_kart_visual(
    position: float,
    velocity: float,
    band_active: bool,
    observation_time: float,
    release_time: float | None,
    minimum_position: float,
    maximum_position: float,
) -> go.Figure:
    """
    Spanish: Representa el ePhiKart sobre una regla dinámica fija en metros.
             La regla usa el recorrido completo y el carrito se ubica según x(t_obs).
    English: Represents ePhiKart on a fixed dynamic ruler in meters.
             The ruler uses the full trajectory and the cart is placed from x(t_obs).
    """

    # HOTFIX · CART CENTER / CENTRO DEL CARRITO
    # Spanish: La coordenada horizontal central del sprite coincide con x(t_obs).
    # English: The sprite horizontal center coincides with x(t_obs).
    center_x = float(position)

    # HOTFIX 2 · MOTION STATE / ESTADO DE MOVIMIENTO
    # Spanish: Se determina con la velocidad instantánea y se mantiene
    #          independiente del estado mecánico de las ligas.
    # English: It is determined from instantaneous velocity and remains
    #          independent from the mechanical state of the bands.
    if velocity > 0.01:
        motion_state = "Movimiento hacia adelante"
    elif velocity < -0.01:
        motion_state = "Movimiento hacia atrás"
    else:
        motion_state = "Carrito detenido"


    figure = go.Figure()

    # P1-E.2 · FIXED DYNAMIC SCALE / ESCALA DINÁMICA FIJA
    # Spanish: El rango depende de toda la simulación, nunca del t_obs actual.
    # English: The range depends on the whole simulation, never on current t_obs.
    physical_min = float(min(minimum_position, maximum_position))
    physical_max = float(max(minimum_position, maximum_position))
    physical_span = physical_max - physical_min

    if physical_span < 1e-9:
        physical_span = 1.0
        physical_max = physical_min + physical_span

    margin = max(0.08 * physical_span, 0.05)
    scale_min = physical_min - margin
    scale_max = physical_max + margin
    scale_span = scale_max - scale_min

    # P1-E.2 · NICE TICKS / DIVISIONES LEGIBLES
    # Spanish: Pasos 1-2-5 producen aproximadamente 5–7 referencias.
    # English: 1-2-5 steps produce approximately 5–7 references.
    raw_step = scale_span / 6.0
    magnitude = 10.0 ** np.floor(np.log10(max(raw_step, 1e-12)))
    normalized_step = raw_step / magnitude

    if normalized_step <= 1.0:
        nice_factor = 1.0
    elif normalized_step <= 2.0:
        nice_factor = 2.0
    elif normalized_step <= 5.0:
        nice_factor = 5.0
    else:
        nice_factor = 10.0

    tick_step = nice_factor * magnitude
    axis_min = float(np.floor(scale_min / tick_step) * tick_step)
    axis_max = float(np.ceil(scale_max / tick_step) * tick_step)

    if axis_max <= axis_min:
        axis_max = axis_min + tick_step

    tick_values = np.arange(axis_min, axis_max + 0.5 * tick_step, tick_step)

    # P1-E.3 · APPROVED IMAGE / IMAGEN APROBADA
    # Spanish: Se conserva exactamente el PNG aprobado en assets.
    # English: The exact approved PNG stored in assets is preserved.
    project_root = Path(__file__).resolve().parents[2]
    kart_image_path = project_root / "assets" / "ephikart" / "kart_simulation.png"

    if not kart_image_path.exists():
        raise FileNotFoundError(
            "No se encontró assets/ephikart/kart_simulation.png"
        )

    kart_source = _image_file_to_data_uri(kart_image_path)

    # P1-E.3 · PHYSICAL POSITION / POSICIÓN FÍSICA
    # Spanish: El centro del sprite sigue directamente x(t_obs).
    # English: The sprite center directly follows x(t_obs).
    axis_span = axis_max - axis_min
    kart_width = 0.28 * axis_span
    kart_left = float(position) - 0.5 * kart_width

    # Spanish: Solo se limita el dibujo para evitar que la imagen salga del marco.
    # English: Drawing is only clamped to keep the image inside the frame.
    kart_left = max(axis_min, min(kart_left, axis_max - kart_width))

    figure.add_layout_image(
        dict(
            source=kart_source,
            xref="x",
            yref="y",
            x=kart_left,
            y=0.78,
            sizex=kart_width,
            sizey=0.42,
            xanchor="left",
            yanchor="top",
            sizing="contain",
            opacity=1.0,
            layer="above",
        )
    )

    # P1-E.2 · RULER / REGLA
    # Spanish: La pista funciona ahora como referencia métrica.
    # English: The track now works as a metric reference.
    figure.add_shape(
        type="line",
        x0=axis_min, x1=axis_max,
        y0=0.23, y1=0.23,
        line={"color": "#8A99A8", "width": 3},
        layer="below",
    )

    for tick in tick_values:
        figure.add_shape(
            type="line",
            x0=float(tick), x1=float(tick),
            y0=0.20, y1=0.26,
            line={"color": "#627D98", "width": 1.5},
            layer="below",
        )

    # Spanish: Marca azul de la posición instantánea.
    # English: Blue mark for the instantaneous position.
    figure.add_shape(
        type="line",
        x0=float(position), x1=float(position),
        y0=0.20, y1=0.31,
        line={"color": INTERACTIVE_BLUE, "width": 3},
        layer="above",
    )

    # P1-E.3 · STATE / ESTADO
    # MOBILE VISUAL 2 · THREE BAND STATES / TRES ESTADOS DE LA LIGA
    # Spanish: La liberación se mantiene visible durante una ventana breve
    #          para que el estudiante pueda identificarla con pasos de 0.02 s.
    # English: Release remains visible for a brief window so students can
    #          identify it while stepping through time in 0.02 s increments.
    release_window = max(0.04, 2.0 * TIME_STEP)
    is_release_event = (
        release_time is not None
        and abs(observation_time - float(release_time)) <= release_window
    )

    if band_active and not is_release_event:
        elastic_state = "LIGAS ACTUANDO"
        elastic_detail = "transmisión elástica activa"
        band_color = "#F59E0B"       # Amber / Ámbar
        band_text_color = "#3B2A00"
    elif is_release_event:
        elastic_state = "LIGAS SE SUELTAN"
        elastic_detail = "fin del impulso elástico"
        band_color = "#22C55E"       # Green / Verde
        band_text_color = "#063B17"
    else:
        elastic_state = "MOVIMIENTO LIBRE"
        elastic_detail = "ligas liberadas · sin impulso elástico"
        band_color = "#3B82F6"       # Blue / Azul
        band_text_color = "#FFFFFF"

    figure.add_annotation(
        x=center_x,
        y=0.96,
        text=(
            f"<b>t = {observation_time:.2f} s</b>"
            f" &nbsp;·&nbsp; x = {position:.3f} m"
        ),
        showarrow=False,
        font={"size": 11, "color": ESPOL_BLUE},
    )

    figure.add_annotation(
        # Spanish: Coordenadas "paper" mantienen la etiqueta fija al centro.
        # English: "paper" coordinates keep the label fixed at center.
        x=0.5,
        xref="paper",
        y=0.08,
        yref="paper",
        text=f"<b>{motion_state}</b>",
        showarrow=False,
        font={"size": 10, "color": TEXT_COLOR},
        xanchor="center",
    )

    figure.add_annotation(
        # Spanish: El estado de la liga permanece fijo y centrado.
        # English: Band status remains fixed and centered.
        x=0.5,
        xref="paper",
        y=-0.02,
        yref="paper",
        text=f"<b>{elastic_state}</b> · {elastic_detail}",
        showarrow=False,
        font={"size": 9, "color": band_text_color},
        bgcolor=band_color,
        bordercolor=band_color,
        borderpad=4,
        opacity=0.92,
        xanchor="center",
    )

    # MOBILE VISUAL 2 · RELEASE EVENT MARKER / MARCADOR DEL EVENTO DE LIBERACIÓN
    # Spanish: Una señal verde sobre el carrito destaca el momento en que
    #          las ligas dejan de transmitir impulso elástico.
    # English: A green signal above the cart highlights the instant when
    #          the bands stop transmitting elastic impulse.
    if is_release_event:
        figure.add_annotation(
            x=position,
            y=0.58,
            text="<b>LIBERACIÓN</b>",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#22C55E",
            ax=0,
            ay=-24,
            font={"size": 9, "color": "#063B17"},
            bgcolor="#DCFCE7",
            bordercolor="#22C55E",
            borderpad=3,
        )

    figure.update_layout(
        # Mobile-first: reduce vertical footprint substantially.
        # Mobile-first: reduce de forma importante el espacio vertical.
        height=235,
        margin={"l": 10, "r": 10, "t": 8, "b": 34},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        xaxis={
            "range": [axis_min, axis_max],
            "tickmode": "array",
            "tickvals": [float(v) for v in tick_values],
            "ticktext": [f"{v:g} m" for v in tick_values],
            "tickfont": {"size": 9, "color": MUTED_TEXT},
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "fixedrange": True,
        },
        yaxis={
            "range": [-0.10, 1.03],
            "visible": False,
            "fixedrange": True,
        },
        font={"family": "Inter, Segoe UI, Arial", "color": TEXT_COLOR},
    )

    return figure


def build_energy_chart(
    kinetic_energy: float,
    elastic_energy: float,
    friction_work: float,
    mechanical_energy: float,
    observation_time: float,
) -> go.Figure:
    """
    Gráfico de barras de energía correspondiente
    al instante seleccionado.
    """

    labels = [
        "Energía cinética",
        "Energía elástica",
        "Trabajo de fricción",
        "Energía mecánica",
    ]

    values = [
        kinetic_energy,
        elastic_energy,
        friction_work,
        mechanical_energy,
    ]

    colors = [
        "#1677B8",   # Azul interactivo
        "#38A9E0",   # Celeste tecnológico
        "#C0392B",   # Trabajo de fricción
        "#001C43",   # Azul ESPOL
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[
                f"{value:.3f} J"
                for value in values
            ],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{x}"
                "<br>%{y:.4f} J"
                "<extra></extra>"
            ),
        )
    )

    figure.add_hline(
        y=0,
        line_width=1.5,
        line_color="#627D98",
    )

    figure.update_layout(
        title={
            "text": (
                "Balance energético "
                f"· t = {observation_time:.2f} s"
            ),
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 17,
                "color": ESPOL_BLUE,
            },
        },
        height=390,
        margin={
            "l": 20,
            "r": 20,
            "t": 65,
            "b": 30,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        font={
            "family": "Inter, Segoe UI, Arial",
            "color": TEXT_COLOR,
        },
        xaxis={
            "title": "",
            "tickfont": {
                "size": 12,
                "color": TEXT_COLOR,
            },
        },
        yaxis={
            "title": "Energía / trabajo (J)",
            "gridcolor": GRID_COLOR,
            "zeroline": False,
        },
    )

    return figure
    

def build_prediction_pdf(
    *,
    parameters: ElasticKartParameters,
    simulation: dict,
    state: dict,
    position_figure: go.Figure,
    velocity_figure: go.Figure,
    acceleration_figure: go.Figure,
    energy_figure: go.Figure,
) -> bytes:
    """
    Spanish: Genera un PDF de la predicción hasta el instante t_obs fijado
             por el estudiante e incorpora las gráficas visibles en ese instante.
    English: Generates a prediction PDF up to the student's fixed t_obs and
             includes the charts visible at that instant.
    """

    # Local import keeps PDF dependencies isolated from the simulation core.
    # La importación local mantiene las dependencias PDF aisladas del núcleo.
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.25 * cm,
        bottomMargin=1.25 * cm,
        title="ePhiKart - Predicción",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ePhiKartTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#001C43"),
        fontSize=20,
        leading=24,
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "ePhiKartSection",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#001C43"),
        fontSize=13,
        leading=16,
        spaceBefore=8,
        spaceAfter=6,
    )
    centered_style = ParagraphStyle(
        "Centered",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#102A43"),
        fontSize=9,
    )

    story = [
        Paragraph("e(Phi)Kart - Documento de predicción", title_style),
        Paragraph(
            f"Estado registrado en <b>t = {state['time']:.2f} s</b>. "
            "Las gráficas corresponden al instante de observación fijado por el estudiante.",
            styles["BodyText"],
        ),
        Spacer(1, 0.25 * cm),
        Paragraph("Parámetros de simulación", section_style),
    ]

    parameter_rows = [
        ["Magnitud", "Valor", "Magnitud", "Valor"],
        ["Posición inicial", f"{parameters.initial_position:.3f} m",
         "Velocidad inicial", f"{parameters.initial_velocity:.3f} m/s"],
        ["Longitud natural L0", f"{parameters.natural_length:.3f} m",
         "Longitud inicial Li", f"{parameters.initial_length:.3f} m"],
        ["Constante elástica k", f"{parameters.spring_constant:.2f} N/m",
         "Masa", f"{parameters.mass:.3f} kg"],
        ["Coeficiente de fricción", f"{parameters.friction_coefficient:.2f}",
         "Tiempo máximo", f"{parameters.duration:.2f} s"],
    ]
    parameter_table = Table(parameter_rows, colWidths=[4.1*cm, 2.6*cm, 4.1*cm, 2.6*cm])
    parameter_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#001C43")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4D0")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [parameter_table, Spacer(1, 0.25 * cm)]

    story.append(Paragraph("Estado instantáneo", section_style))
    state_rows = [
        ["Posición", "Velocidad", "Aceleración", "F. elástica", "F. fricción"],
        [
            f"{state['position']:.3f} m",
            f"{state['velocity']:.3f} m/s",
            f"{state['acceleration']:.3f} m/s²",
            f"{state['elastic_force']:.3f} N",
            f"{state['friction_force']:.3f} N",
        ],
    ]
    state_table = Table(state_rows, colWidths=[3.0*cm]*5)
    state_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF6FC")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#001C43")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4D0")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.3),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [state_table, Spacer(1, 0.25 * cm)]

    # Spanish: Plotly exporta exactamente las figuras que ya se muestran.
    # English: Plotly exports the exact figures already shown on screen.
    figures = [
        ("Posición vs. tiempo", position_figure),
        ("Velocidad vs. tiempo", velocity_figure),
        ("Aceleración vs. tiempo", acceleration_figure),
        ("Balance energético", energy_figure),
    ]

    for index, (caption, figure) in enumerate(figures):
        if index == 2:
            story.append(PageBreak())

        image_bytes = pio.to_image(
            figure,
            format="png",
            width=1000,
            height=520,
            scale=1.35,
        )
        image_stream = BytesIO(image_bytes)
        story.append(
            KeepTogether([
                Paragraph(caption, section_style),
                Image(image_stream, width=17.0*cm, height=8.84*cm),
                Paragraph(
                    f"Captura correspondiente a t = {state['time']:.2f} s",
                    centered_style,
                ),
                Spacer(1, 0.15*cm),
            ])
        )

    story.append(Paragraph("Energía en el instante seleccionado", section_style))
    energy_rows = [
        ["Cinética", "Elástica", "Trabajo de fricción", "Mecánica"],
        [
            f"{state['kinetic_energy']:.3f} J",
            f"{state['elastic_energy']:.3f} J",
            f"{state['friction_work']:.3f} J",
            f"{state['mechanical_energy']:.3f} J",
        ],
    ]
    energy_table = Table(energy_rows, colWidths=[3.75*cm]*4)
    energy_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF6FC")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4D0")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(energy_table)

    document.build(story)
    return buffer.getvalue()


def render_prediction(
    show_header: bool = True,
    show_footer: bool = True,
    show_top_navigation: bool = False,
) -> None:
    """Renderiza la herramienta de predicción de ePhiKart."""

    if show_top_navigation:
        render_top_navigation()

    if show_header:
        render_header(
            eyebrow="e(Phi)Kart",
            title="Predicción del movimiento",
            subtitle=(
                "Simula el movimiento de un carrito impulsado por una liga "
                "elástica y sometido a fricción."
            ),
            badge="Modelo físico interactivo",
        )


    title_column, reset_column = st.columns([6, 1])

    ##*****************************
    # 1. configura el movimiento
    ##**************************
    
    with title_column:
        st.markdown("## 1. Configura el movimiento")
    
    with reset_column:
        st.button(
            "↻ Reiniciar",
            use_container_width=True,
            on_click=reset_prediction,
        )
    
    
    # P1-M · PHYSICAL RANGES / RANGOS FÍSICOS
    # Spanish: Normaliza estados antiguos antes de crear los widgets.
    # English: Normalize legacy state before creating the widgets.
    normalize_physical_control_state()

    with st.container(border=True):
        left_column, right_column = st.columns(2, gap="large")
    
        with left_column:
            initial_position = st.slider(
                "Posición inicial, x₀ (m)",
                min_value=-1.0,
                max_value=1.0,
                value=0.0,
                step=0.01,
                key="kart_initial_position",
                help="Posición desde la cual comienza el carrito.",
            )
    
            initial_velocity = st.slider(
                "Velocidad inicial, v₀ (m/s)",
                min_value=0.0,
                max_value=3.0,
                value=0.0,
                step=0.05,
                key="kart_initial_velocity",
                help="Velocidad del carrito en el instante inicial.",
            )
    
            natural_length = st.slider(
                "Longitud natural de la liga, L₀ (m)",
                min_value=0.07,
                max_value=0.10,
                value=0.085,
                step=0.005,
                key="kart_natural_length",
                help=(
                    "Longitud de la liga cuando no se encuentra "
                    "estirada."
                ),
            )
    
            initial_length = st.slider(
                "Longitud estirada inicial, Lᵢ (m)",
                min_value=0.101,
                max_value=0.200,
                value=0.150,
                step=0.001,
                key="kart_initial_length",
                help=(
                    "Longitud inicial de la liga antes de soltar "
                    "el carrito."
                ),
            )
    
        with right_column:
            spring_constant = st.slider(
                "Constante elástica de la liga, k (N/m)",
                min_value=5.0,
                max_value=20.0,
                value=10.0,
                step=0.5,
                key="kart_spring_constant",
                help="Rigidez efectiva de la liga.",
            )
    
            friction_coefficient = st.slider(
                "Coeficiente de fricción cinética, μ",
                min_value=0.0,
                max_value=0.50,
                value=0.05,
                step=0.01,
                key="kart_friction",
                help=(
                    "Coeficiente de fricción entre las ruedas "
                    "y la superficie."
                ),
            )
    
            mass = st.slider(
                "Masa del carrito, m (kg)",
                min_value=0.05,
                max_value=2.0,
                value=0.25,
                step=0.01,
                key="kart_mass",
                help="Masa total del carrito.",
            )
    
            duration = st.slider(
                "Duración máxima de la simulación, tₘₐₓ (s)",
                min_value=1.0,
                max_value=5.0,
                value=4.0,
                step=0.5,
                key="kart_duration",
                help="Tiempo máximo que se mostrará en las gráficas.",
            )
    
    
    parameters = ElasticKartParameters(
        initial_position=initial_position,
        initial_velocity=initial_velocity,
        natural_length=natural_length,
        initial_length=initial_length,
        spring_constant=spring_constant,
        mass=mass,
        friction_coefficient=friction_coefficient,
        duration=duration,
    )
    
    try:
        simulation = simulate_motion(parameters)
    except ValueError as error:
        st.error(str(error))
        st.stop()
    
    # ========================================================
    # P1-E.4 · GLOBAL TIME PREPARATION / PREPARACIÓN DEL TIEMPO GLOBAL
    # Spanish: t_obs se prepara aquí, pero los controles visibles se
    #          muestran debajo de la representación del carrito.
    # English: t_obs is prepared here, while the visible controls are
    #          rendered below the cart representation.
    # ========================================================
    prepare_observation_time_state(float(duration))
    observation_time = float(st.session_state["t_obs"])

    state = instantaneous_state(
        simulation,
        observation_time,
    )
    
    release_time = simulation["release_time"]

        # ========================================================
    # P1-D.1 · INSTANTANEOUS STATE / ESTADO INSTANTÁNEO
    # Spanish: Las variables se organizan según su significado
    #          físico: primero las variables cinemáticas y luego
    #          las fuerzas que actúan sobre el carrito.
    # English: Variables are organized according to their
    #          physical meaning: kinematic variables first,
    #          followed by the forces acting on the cart.
    # ========================================================

    st.markdown("## 3. Estado instantáneo")

    # --------------------------------------------------------
    # OBSERVATION TIME / TIEMPO DE OBSERVACIÓN
    # Spanish: Todas las métricas corresponden al mismo t_obs.
    # English: All metrics correspond to the same t_obs.
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div style="
            color: #627D98;
            font-size: 0.95rem;
            margin-top: -0.35rem;
            margin-bottom: 0.85rem;
        ">
            Estado del sistema en
            <strong style="
                color: #1677B8;
                font-size: 1.05rem;
            ">
                t = {state['time']:.2f} s
            </strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # KINEMATICS / CINEMÁTICA
    # --------------------------------------------------------

    st.markdown("#### Movimiento")

    motion_columns = st.columns(3, gap="medium")

    motion_columns[0].metric(
        label="Posición x",
        value=f"{state['position']:.3f} m",
        border=True,
    )

    motion_columns[1].metric(
        label="Velocidad v",
        value=f"{state['velocity']:.3f} m/s",
        border=True,
    )

    motion_columns[2].metric(
        label="Aceleración a",
        value=f"{state['acceleration']:.3f} m/s²",
        border=True,
    )

    # --------------------------------------------------------
    # DYNAMICS / DINÁMICA
    # --------------------------------------------------------

    st.markdown("#### Fuerzas")

    force_columns = st.columns(2, gap="medium")

    force_columns[0].metric(
        label="Fuerza elástica",
        value=f"{state['elastic_force']:.3f} N",
        border=True,
    )

    force_columns[1].metric(
        label="Fuerza de fricción",
        value=f"{state['friction_force']:.3f} N",
        border=True,
    )
        # ========================================================
    # P1-E.2 · DYNAMIC KART VISUAL / REPRESENTACIÓN DINÁMICA
    # Spanish: La imagen aprobada del carrito se desplaza según x(t)
    #          y comunica el estado físico correspondiente a t_obs.
    # English: The approved cart image moves according to x(t) and
    #          communicates the physical state corresponding to t_obs.
    # ========================================================

    st.markdown("#### Representación del sistema")

    with st.container(border=True):
        st.plotly_chart(
            build_kart_visual(
                position=state["position"],
                velocity=state["velocity"],
                band_active=state["band_active"],
                observation_time=state["time"],
                release_time=simulation.get("release_time"),
                minimum_position=float(np.min(simulation["position"])),
                maximum_position=float(np.max(simulation["position"])),
            ),
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

    # ========================================================
    # P1-E.4 · GLOBAL TIME CONTROLS / CONTROLES DE TIEMPO GLOBAL
    # Spanish: Todos los controles temporales principales quedan debajo
    #          del carrito y modifican la misma variable global t_obs.
    # English: All main time controls sit below the cart and update the
    #          same global t_obs variable.
    # ========================================================
    st.slider(
        "Tiempo de observación global, t (s)",
        min_value=0.0,
        max_value=float(duration),
        step=TIME_STEP,
        key="t_general",
        on_change=sync_observation_time,
        args=("t_general", float(duration)),
    )

    time_minus, time_input, time_plus = st.columns([1, 1.35, 1], gap="small")

    with time_minus:
        st.button(
            "−0.02 s",
            key="time_step_minus",
            use_container_width=True,
            on_click=step_observation_time,
            args=(-TIME_STEP, float(duration)),
        )

    with time_input:
        st.number_input(
            "Tiempo exacto, t (s)",
            step=TIME_STEP,
            format="%.2f",
            key=TIME_INPUT_KEY,
            on_change=sync_manual_observation_time,
            args=(float(duration),),
            help=(
                "Ingrese un valor entre 0.00 s y tₘₐₓ. "
                "Si está fuera del rango, el tiempo vuelve a 0.00 s."
            ),
        )

    with time_plus:
        st.button(
            "+0.02 s",
            key="time_step_plus",
            use_container_width=True,
            on_click=step_observation_time,
            args=(TIME_STEP, float(duration)),
        )

    # ========================================================
    # P1-E.4 · SPEEDOMETER NEXT TO CART / VELOCÍMETRO JUNTO AL CARRITO
    # Spanish: El velocímetro queda inmediatamente debajo de los controles
    #          del carrito para reducir el desplazamiento en smartphone.
    # English: The speedometer is immediately below the cart controls to
    #          reduce scrolling distance on smartphones.
    # ========================================================
    with st.container(border=True):
        maximum_speed = float(np.max(np.abs(simulation["velocity"])))

        st.plotly_chart(
            build_speedometer(
                velocity=state["velocity"],
                maximum_speed=maximum_speed,
            ),
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

        # Spanish: El estado de movimiento y de la liga ya aparece dentro
        #          de la representación compacta del carrito.
        # English: Motion and band states are already shown inside the
        #          compact cart representation.


    # ========================================================
    # P1-C.2 · MOBILE-FIRST CHART LAYOUT
    #          DISTRIBUCIÓN DE GRÁFICAS MOBILE-FIRST
    # Spanish: Posición y velocidad se muestran verticalmente y
    #          ocupan todo el ancho disponible. Esto mejora la
    #          lectura tanto en computadora como en smartphone.
    # English: Position and velocity are displayed vertically
    #          using the full available width. This improves
    #          readability on both desktop and smartphone.
    # ========================================================

    # --------------------------------------------------------
    # POSITION x(t) / POSICIÓN x(t)
    # --------------------------------------------------------

    st.slider(
        "Tiempo de observación para x(t), t (s)",
        min_value=0.0,
        max_value=float(duration),
        step=TIME_STEP,
        key="t_x",
        on_change=sync_observation_time,
        args=("t_x", float(duration)),
    )

    position_figure = build_progressive_chart(
        complete_time=simulation["time"],
        complete_values=simulation["position"],
        observation_time=state["time"],
        observation_value=state["position"],
        release_time=release_time,
        title="Posición vs. tiempo",
        y_title="Posición, x (m)",
        line_name="x(t)",
        line_color=POSITION_GREEN,
    )

    st.plotly_chart(
        position_figure,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "displaylogo": False,
            "responsive": True,
        },
    )

    # --------------------------------------------------------
    # VELOCITY v(t) / VELOCIDAD v(t)
    # --------------------------------------------------------

    st.slider(
        "Tiempo de observación para v(t), t (s)",
        min_value=0.0,
        max_value=float(duration),
        step=TIME_STEP,
        key="t_v",
        on_change=sync_observation_time,
        args=("t_v", float(duration)),
    )

    velocity_figure = build_progressive_chart(
        complete_time=simulation["time"],
        complete_values=simulation["velocity"],
        observation_time=state["time"],
        observation_value=state["velocity"],
        release_time=release_time,
        title="Velocidad vs. tiempo",
        y_title="Velocidad, v (m/s)",
        line_name="v(t)",
        line_color=INTERACTIVE_BLUE,
    )

    st.plotly_chart(
        velocity_figure,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "displaylogo": False,
            "responsive": True,
        },
    )
        # ========================================================
    # P1-C.2 · ACCELERATION CHART / GRÁFICA DE ACELERACIÓN
    # Spanish: La gráfica a(t) ocupa ahora todo el ancho disponible,
    #          manteniendo el mismo orden y estructura que x(t) y v(t).
    # English: The a(t) chart now uses the full available width,
    #          following the same order and structure as x(t) and v(t).
    # ========================================================

    # --------------------------------------------------------
    # ACCELERATION a(t) / ACELERACIÓN a(t)
    # --------------------------------------------------------

    st.slider(
        "Tiempo de observación para a(t), t (s)",
        min_value=0.0,
        max_value=float(duration),
        step=TIME_STEP,
        key="t_a",
        on_change=sync_observation_time,
        args=("t_a", float(duration)),
    )

    acceleration_figure = build_progressive_chart(
        complete_time=simulation["time"],
        complete_values=simulation["acceleration"],
        observation_time=state["time"],
        observation_value=state["acceleration"],
        release_time=release_time,
        title="Aceleración vs. tiempo",
        y_title="Aceleración, a (m/s²)",
        line_name="a(t)",
        line_color=ACCELERATION_RED,
    )

    st.plotly_chart(
        acceleration_figure,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "displaylogo": False,
            "responsive": True,
        },
    )

    # P1-E.4 · SPEEDOMETER MOVED / VELOCÍMETRO REUBICADO
    # Spanish: El velocímetro ya fue mostrado junto al carrito.
    # English: The speedometer was already rendered next to the cart.


    ## ******************************************************
    ## BALANCE ENERGETICO
    ##****************************************************
    st.markdown("## 4. Balance energético")
    

    # ========================================================
    # P1-E.6 · ENERGY TIME MIRROR / ESPEJO TEMPORAL DE ENERGÍA
    # Spanish: Permite explorar el balance energético sin regresar
    #          al carrito y modifica exactamente el mismo t_obs.
    # English: Lets students explore the energy balance without
    #          returning to the cart and updates the exact same t_obs.
    # ========================================================
    st.slider(
        "Tiempo de observación para energía, t (s)",
        min_value=0.0,
        max_value=float(duration),
        step=TIME_STEP,
        key="t_energy",
        on_change=sync_observation_time,
        args=("t_energy", float(duration)),
        help=(
            "Control espejo del tiempo global. Al moverlo se actualizan "
            "el balance energético y todos los elementos asociados a t_obs."
        ),
    )

    st.caption(
        f"Balance energético mostrado en t = {state['time']:.2f} s"
    )

    with st.container(border=True):
    
        # ---------------------------------------------------------
        # Energía mecánica inicial y energía mecánica actual
        # ---------------------------------------------------------
    
        initial_mechanical_energy = float(
            simulation["mechanical_energy"][0]
        )
    
        current_mechanical_energy = float(
            state["mechanical_energy"]
        )
    
        energy_info_columns = st.columns(2, gap="medium")
    
        with energy_info_columns[0]:
            st.metric(
                label="Energía mecánica inicial del sistema",
                value=f"{initial_mechanical_energy:.3f} J",
                border=True,
            )
    
        with energy_info_columns[1]:
            st.metric(
                label=(
                    "Energía mecánica en "
                    f"t = {state['time']:.2f} s"
                ),
                value=f"{current_mechanical_energy:.3f} J",
                border=True,
            )
    
        # ---------------------------------------------------------
        ## Gráfico energia 
        # ---------------------------------------------------------
    
        energy_figure = build_energy_chart(
            kinetic_energy=state["kinetic_energy"],
            elastic_energy=state["elastic_energy"],
            friction_work=state["friction_work"],
            mechanical_energy=state["mechanical_energy"],
            observation_time=state["time"],
        )
    
        st.plotly_chart(
            energy_figure,
            use_container_width=True,
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )
    
    #************************************************************
    
    with st.expander("Modelo físico utilizado"):
        st.markdown(
            r"""
            Mientras la liga se encuentra estirada:
    
            \[
            F_e = k(L-L_0)
            \]
    
            La fuerza de fricción cinética es:
    
            \[
            F_f = -\\mu m g
            \]
    
            La aceleración instantánea se calcula mediante:
    
            \[
            a(t)=\\frac{F_e+F_f}{m}
            \]
    
            Cuando la longitud de la liga alcanza su longitud natural,
            la fuerza elástica se vuelve cero. Desde ese instante, la
            aceleración queda determinada únicamente por la fricción y
            la velocidad disminuye linealmente hasta que el carrito se
            detiene.
            """
        )



    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_prediction(show_top_navigation=True)
