from __future__ import annotations

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

def build_kart_visual() -> go.Figure:
    """
    Spanish: Construye una vista lateral esquemática del ePhiKart real.
             Se muestran solo elementos pedagógicos, sin dimensiones
             ni detalles constructivos sensibles.
    English: Builds a schematic side view of the real ePhiKart.
             Only pedagogical elements are shown, without dimensions
             or sensitive construction details.
    """

    figure = go.Figure()

    # P1-E.1 · TRACK / PISTA
    # Spanish: Referencia visual del suelo, no una cota dimensional.
    # English: Visual ground reference, not a dimensional reference.
    figure.add_shape(
        type="line", x0=0.5, x1=29.5, y0=1.0, y1=1.0,
        line={"color": "#8A99A8", "width": 3},
    )

    # P1-E.1 · BLACK PLATFORM / PLATAFORMA NEGRA
    # Spanish: Plataforma lateral que sostiene el conjunto impreso.
    # English: Side platform supporting the printed mechanism.
    figure.add_shape(
        type="rect", x0=3.0, x1=27.0, y0=4.0, y1=6.2,
        line={"color": "#20262D", "width": 2},
        fillcolor="#252B31",
    )

    # P1-E.1 · WHEELS / RUEDAS
    # Spanish: Se conserva solo la diferencia visual entre ruedas.
    # English: Only the visual size difference between wheels is preserved.
    for x0, x1, y0, y1 in [
        (3.5, 11.5, 1.0, 9.0),
        (22.0, 27.5, 1.0, 6.5),
    ]:
        figure.add_shape(
            type="circle", x0=x0, x1=x1, y0=y0, y1=y1,
            line={"color": "#35AFC0", "width": 5},
            fillcolor="#F4C515",
        )

    # Spanish: Centros amarillos de las ruedas impresas.
    # English: Yellow hubs of the printed wheels.
    figure.add_shape(
        type="circle", x0=6.8, x1=8.2, y0=4.3, y1=5.7,
        line={"color": "#D5A900", "width": 2},
        fillcolor="#F4C515",
    )
    figure.add_shape(
        type="circle", x0=24.15, x1=25.35, y0=3.15, y1=4.35,
        line={"color": "#D5A900", "width": 2},
        fillcolor="#F4C515",
    )

    # P1-E.1 · 3D-PRINTED SUPPORT / SOPORTE IMPRESO EN 3D
    # Spanish: Conjunto mecánico amarillo visible sobre la plataforma.
    # English: Yellow mechanical assembly visible above the platform.
    figure.add_shape(
        type="rect", x0=7.8, x1=15.3, y0=5.6, y1=8.0,
        line={"color": "#D5A900", "width": 2},
        fillcolor="#F4C515",
    )

    # P1-E.1 · VISIBLE LARGE GEAR / ENGRANAJE GRANDE VISIBLE
    # Spanish: Solo se dibuja el engranaje grande visible lateralmente.
    # English: Only the large gear visible from the side is drawn.
    figure.add_shape(
        type="circle", x0=8.8, x1=15.8, y0=6.4, y1=13.4,
        line={"color": "#D5A900", "width": 3},
        fillcolor="#F4C515",
    )
    figure.add_shape(
        type="circle", x0=11.6, x1=13.0, y0=9.2, y1=10.6,
        line={"color": "#B48E00", "width": 2},
        fillcolor="#FFF3A6",
    )

    # P1-E.1 · FRONT BAND SUPPORT / SOPORTE DELANTERO DE LIGAS
    # Spanish: Soporte frontal donde se fijan las dos ligas.
    # English: Front support where both elastic bands are fixed.
    figure.add_shape(
        type="rect", x0=23.7, x1=27.2, y0=6.0, y1=8.2,
        line={"color": "#D5A900", "width": 2},
        fillcolor="#F4C515",
    )

    # P1-E.1 · ELASTIC BANDS / LIGAS ELÁSTICAS
    # Spanish: Dos ligas desde el soporte frontal hacia el engranaje.
    # English: Two bands running from the front support toward the gear.
    figure.add_shape(
        type="line", x0=13.2, x1=25.2, y0=10.6, y1=7.6,
        line={"color": "#E58A22", "width": 5},
    )
    figure.add_shape(
        type="line", x0=13.0, x1=25.2, y0=9.7, y1=7.0,
        line={"color": "#7D4AA8", "width": 5},
    )

    # P1-E.1 · PEDAGOGICAL LABELS / ETIQUETAS PEDAGÓGICAS
    # Spanish: Se omiten dimensiones, relaciones y detalles de fabricación.
    # English: Dimensions, ratios, and manufacturing details are omitted.
    figure.add_annotation(
        x=12.3, y=14.0, text="Engranaje visible",
        showarrow=False, font={"size": 12, "color": TEXT_COLOR},
    )
    figure.add_annotation(
        x=7.5, y=0.15, text="Rueda trasera · motriz",
        showarrow=False, font={"size": 11, "color": MUTED_TEXT},
    )
    figure.add_annotation(
        x=24.8, y=0.15, text="Rueda delantera",
        showarrow=False, font={"size": 11, "color": MUTED_TEXT},
    )
    figure.add_annotation(
        x=24.0, y=12.4, text="Movimiento →",
        showarrow=False, font={"size": 13, "color": INTERACTIVE_BLUE},
    )

    figure.update_layout(
        title={
            "text": "Representación física del ePhiKart",
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 17, "color": ESPOL_BLUE},
        },
        height=410,
        margin={"l": 10, "r": 10, "t": 55, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        xaxis={"range": [0, 30], "visible": False, "fixedrange": True},
        yaxis={
            "range": [-0.8, 15],
            "visible": False,
            "fixedrange": True,
            "scaleanchor": "x",
            "scaleratio": 1,
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
    # P1-E.1 · PHYSICAL KART VISUAL / REPRESENTACIÓN FÍSICA
    # Spanish: En esta primera etapa se muestra el mecanismo
    #          estático para validar su geometría y apariencia.
    # English: This first stage displays the static mechanism
    #          to validate its geometry and appearance.
    # ========================================================

    st.markdown("#### Representación del sistema")

    with st.container(border=True):
        st.plotly_chart(
            build_kart_visual(),
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
