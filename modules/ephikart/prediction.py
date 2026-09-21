from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
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
)


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
                    "size": 42,
                    "color": ESPOL_BLUE,
                },
            },
            title={
                "text": "Velocidad instantánea",
                "font": {
                    "size": 18,
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
        height=325,
        margin={
            "l": 30,
            "r": 30,
            "t": 60,
            "b": 10,
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
    minimum_position: float,
    maximum_position: float,
) -> go.Figure:
    """
    Spanish: Muestra la imagen aprobada del ePhiKart como un objeto móvil.
             La posición horizontal se sincroniza con x(t), mientras que
             el texto inferior comunica el estado físico instantáneo.

    English: Displays the approved ePhiKart image as a moving object.
             Horizontal position is synchronized with x(t), while the
             lower text communicates the instantaneous physical state.
    """

    figure = go.Figure()

    # ========================================================
    # P1-E.2 · APPROVED KART IMAGE / IMAGEN APROBADA DEL CARRITO
    # Spanish: Se usa exactamente el recurso gráfico guardado en assets.
    #          No se reconstruye el carrito con formas de Plotly.
    # English: The exact graphic resource stored in assets is used.
    #          The cart is no longer reconstructed with Plotly shapes.
    # ========================================================
    project_root = Path(__file__).resolve().parents[2]
    kart_image_path = (
        project_root
        / "assets"
        / "ephikart"
        / "kart_simulation.png"
    )

    # Spanish: Si falta el recurso, se genera un error claro para GitHub/Cloud.
    # English: If the asset is missing, a clear GitHub/Cloud error is raised.
    if not kart_image_path.exists():
        raise FileNotFoundError(
            "No se encontró assets/ephikart/kart_simulation.png"
        )

    kart_source = _image_file_to_data_uri(kart_image_path)

    # ========================================================
    # P1-E.2 · VISUAL POSITION / POSICIÓN VISUAL
    # Spanish: x(t) se normaliza únicamente para ubicar la miniatura
    #          dentro del escenario. La etiqueta conserva el valor físico real.
    # English: x(t) is normalized only to place the thumbnail inside the
    #          stage. The label preserves the actual physical value.
    # ========================================================
    position_span = maximum_position - minimum_position

    if abs(position_span) < 1e-12:
        normalized_position = 0.0
    else:
        normalized_position = (
            (position - minimum_position) / position_span
        )

    normalized_position = max(
        0.0,
        min(float(normalized_position), 1.0),
    )

    # Spanish: La miniatura se desplaza de izquierda a derecha sin salir del marco.
    # English: The thumbnail moves left-to-right without leaving the frame.
    kart_width = 34.0
    kart_height = 20.0
    left_limit = 3.0
    right_limit = 97.0 - kart_width
    kart_x = left_limit + normalized_position * (right_limit - left_limit)

    figure.add_layout_image(
        dict(
            source=kart_source,
            xref="x",
            yref="y",
            x=kart_x,
            y=24.0,
            sizex=kart_width,
            sizey=kart_height,
            xanchor="left",
            yanchor="top",
            sizing="contain",
            opacity=1.0,
            layer="above",
        )
    )

    # ========================================================
    # P1-E.2 · TRACK / PISTA
    # Spanish: La pista permanece fija; solo se desplaza el carrito.
    # English: The track remains fixed; only the cart moves.
    # ========================================================
    figure.add_shape(
        type="line",
        x0=1.0,
        x1=99.0,
        y0=4.0,
        y1=4.0,
        line={"color": "#8A99A8", "width": 3},
        layer="below",
    )

    # ========================================================
    # P1-E.2 · INSTANTANEOUS STATE / ESTADO INSTANTÁNEO
    # Spanish: La imagen muestra el carrito; estas etiquetas indican
    #          el estado físico calculado en el mismo t_obs.
    # English: The image shows the cart; these labels indicate the
    #          physical state calculated at the same t_obs.
    # ========================================================
    if band_active:
        elastic_state = "Ligas actuando · transmisión activa"
    else:
        elastic_state = "Ligas liberadas · sin impulso elástico"

    if velocity > 0.01:
        motion_state = "Movimiento hacia adelante"
    elif velocity < -0.01:
        motion_state = "Movimiento hacia atrás"
    else:
        motion_state = "Carrito detenido"

    figure.add_annotation(
        x=50,
        y=28.2,
        text=(
            f"<b>t = {observation_time:.2f} s</b>"
            f" &nbsp;·&nbsp; x = {position:.3f} m"
        ),
        showarrow=False,
        font={"size": 13, "color": ESPOL_BLUE},
    )

    figure.add_annotation(
        x=50,
        y=1.3,
        text=f"<b>{motion_state}</b> &nbsp;·&nbsp; {elastic_state}",
        showarrow=False,
        font={"size": 12, "color": TEXT_COLOR},
    )

    figure.update_layout(
        height=360,
        margin={"l": 5, "r": 5, "t": 15, "b": 15},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        xaxis={
            "range": [0, 100],
            "visible": False,
            "fixedrange": True,
        },
        yaxis={
            "range": [0, 30],
            "visible": False,
            "fixedrange": True,
        },
        font={
            "family": "Inter, Segoe UI, Arial",
            "color": TEXT_COLOR,
        },
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
                min_value=0.05,
                max_value=1.0,
                value=0.20,
                step=0.01,
                key="kart_natural_length",
                help=(
                    "Longitud de la liga cuando no se encuentra "
                    "estirada."
                ),
            )
    
            initial_length = st.slider(
                "Longitud estirada inicial, Lᵢ (m)",
                min_value=float(natural_length),
                max_value=2.0,
                value=max(0.50, float(natural_length)),
                step=0.01,
                key="kart_initial_length",
                help=(
                    "Longitud inicial de la liga antes de soltar "
                    "el carrito."
                ),
            )
    
        with right_column:
            spring_constant = st.slider(
                "Constante elástica de la liga, k (N/m)",
                min_value=1.0,
                max_value=50.0,
                value=15.0,
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
                max_value=20.0,
                value=10.0,
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
    # P1-A / P1-B · 2. OBSERVATION TIME / TIEMPO DE OBSERVACIÓN
    # Spanish: El slider general modifica t_obs. Las gráficas,
    #          métricas, energía y velocímetro leen este mismo valor.
    # English: The general slider updates t_obs. Charts, metrics,
    #          energy, and the speedometer read this same value.
    # ========================================================

    st.markdown("## 2. Instante de observación")

    prepare_observation_time_state(float(duration))

    with st.container(border=True):
        st.slider(
            "Desplaza el control para construir la gráfica",
            min_value=0.0,
            max_value=float(duration),
            step=0.02,
            key="t_general",
            on_change=sync_observation_time,
            args=("t_general", float(duration)),
            help=(
                "Control temporal general. Todos los controles de tiempo "
                "de la actividad representan el mismo instante t_obs."
            ),
        )

        observation_time = float(st.session_state["t_obs"])

        st.markdown(
            f"""
            <div style="
                color: #102A43;
                font-size: 1rem;
                margin-top: -0.25rem;
            ">
                Tiempo global de observación:
                <strong style="
                    color: #1677B8;
                    font-size: 1.35rem;
                ">
                    {observation_time:.2f} s
                </strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
        step=0.02,
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
        step=0.02,
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
        step=0.02,
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
            "displaylogo": False,
            "responsive": True,
        },
    )

    # ========================================================
    # P1-C.2 · SPEEDOMETER / VELOCÍMETRO
    # Spanish: El velocímetro se coloca debajo de las tres gráficas.
    #          Sigue utilizando el mismo estado instantáneo t_obs.
    # English: The speedometer is placed below the three charts.
    #          It continues using the same instantaneous t_obs state.
    # ========================================================

    with st.container(border=True):

        maximum_speed = float(
            np.max(np.abs(simulation["velocity"]))
        )

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

        # ----------------------------------------------------
        # MOVEMENT STATE / ESTADO DEL MOVIMIENTO
        # ----------------------------------------------------

        if state["velocity"] > 0.01:
            movement_state = "Movimiento hacia adelante"
        elif state["velocity"] < -0.01:
            movement_state = "Movimiento hacia atrás"
        else:
            movement_state = "Carrito detenido"

        # ----------------------------------------------------
        # ELASTIC BAND STATE / ESTADO DE LA LIGA
        # ----------------------------------------------------

        if state["band_active"]:
            band_state = "Liga actuando"
        else:
            band_state = "Liga suelta"

        st.markdown(
            f"""
            <div style="
                text-align: center;
                color: #102A43;
                line-height: 1.7;
            ">
                <strong>{movement_state}</strong><br>
                <span style="color: #627D98;">
                    {band_state}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


    ## ******************************************************
    ## BALANCE ENERGETICO
    ##****************************************************
    st.markdown("## 4. Balance energético")
    
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
