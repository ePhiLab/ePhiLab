from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.footer import render_footer
from components.header import render_header
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


render_header(
    eyebrow="e(Phi)Kart",
    title="Predicción del movimiento",
    subtitle=(
        "Simula el movimiento de un carrito impulsado por una liga "
        "elástica y sometido a fricción."
    ),
    badge="Modelo físico interactivo",
)


def reset_prediction() -> None:
    """Restablece los valores iniciales de la página."""

    keys_to_remove = [
        "kart_initial_position",
        "kart_initial_velocity",
        "kart_natural_length",
        "kart_initial_length",
        "kart_spring_constant",
        "kart_mass",
        "kart_friction",
        "kart_duration",
        "kart_observation_time",
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

    # Curva futura en gris tenue.
    figure.add_trace(
        go.Scatter(
            x=complete_time,
            y=complete_values,
            mode="lines",
            name="Trayectoria completa",
            line={
                "color": "rgba(98, 125, 152, 0.18)",
                "width": 2,
                "dash": "dot",
            },
            hoverinfo="skip",
            showlegend=False,
        )
    )

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

title_column, reset_column = st.columns([6, 1])

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


st.markdown("## 2. Instante de observación")

with st.container(border=True):
    observation_time = st.slider(
        "Desplaza el control para construir la gráfica",
        min_value=0.0,
        max_value=float(duration),
        value=min(
            st.session_state.get(
                "kart_observation_time",
                0.0,
            ),
            float(duration),
        ),
        step=0.02,
        key="kart_observation_time",
        help=(
            "Este slider controla simultáneamente la curva visible, "
            "las métricas y el velocímetro."
        ),
    )

    st.markdown(
        f"""
        <div style="
            color: #102A43;
            font-size: 1rem;
            margin-top: -0.25rem;
        ">
            Tiempo actual:
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


st.markdown("## 3. Estado instantáneo")

metric_columns = st.columns(5, gap="medium")

metric_columns[0].metric(
    "Posición",
    f"{state['position']:.3f} m",
    border=True,
)

metric_columns[1].metric(
    "Velocidad",
    f"{state['velocity']:.3f} m/s",
    border=True,
)

metric_columns[2].metric(
    "Aceleración",
    f"{state['acceleration']:.3f} m/s²",
    border=True,
)

metric_columns[3].metric(
    "Fuerza elástica",
    f"{state['elastic_force']:.3f} N",
    border=True,
)

metric_columns[4].metric(
    "Fuerza de fricción",
    f"{state['friction_force']:.3f} N",
    border=True,
)


velocity_column, position_column = st.columns(2, gap="medium")

with velocity_column:
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

with position_column:
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
    initial_mechanical_energy = float(
    simulation["mechanical_energy"][0]
    )

    expected_mechanical_energy = (
        initial_mechanical_energy
        + state["friction_work"]
    )

    energy_balance_error = (
        state["mechanical_energy"]
        - expected_mechanical_energy
    )

    balance_columns = st.columns(3)

    balance_columns[0].metric(
        "Energía mecánica inicial",
        f"{initial_mechanical_energy:.3f} J",
    )

    balance_columns[1].metric(
        "Energía mecánica actual",
        f"{state['mechanical_energy']:.3f} J",
    )

    balance_columns[2].metric(
        "Error del balance",
        f"{energy_balance_error:.4f} J",
    )




acceleration_column, gauge_column = st.columns(
    [1.35, 1],
    gap="medium",
)

with acceleration_column:
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

with gauge_column:
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
            },
        )

        if state["velocity"] > 0.01:
            movement_state = "Movimiento hacia adelante"
        elif state["velocity"] < -0.01:
            movement_state = "Movimiento hacia atrás"
        else:
            movement_state = "Carrito detenido"

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
        """
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


render_footer()
