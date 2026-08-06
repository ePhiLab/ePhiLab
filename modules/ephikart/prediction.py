from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from components.footer import render_footer
from components.header import render_header
from physics.ephikart.simulation import (
    KinematicParameters,
    instantaneous_state,
    simulate_motion,
)


ESPOL_BLUE = "#001C43"
SECONDARY_BLUE = "#123B68"
INTERACTIVE_BLUE = "#1677B8"
TECH_CYAN = "#38A9E0"
GRID_COLOR = "rgba(98, 125, 152, 0.18)"
MUTED_TEXT = "#627D98"


render_header(
    eyebrow="e(Phi)Kart",
    title="Predicción del movimiento",
    subtitle=(
        "Modifica las condiciones iniciales y observa, en tiempo real, cómo cambian "
        "la posición, la velocidad y la aceleración del carrito."
    ),
    badge="Simulación interactiva · v0.2",
)

st.info(
    "Esta primera implementación usa un modelo de movimiento rectilíneo con "
    "aceleración constante. En las siguientes iteraciones se sustituirá por el "
    "modelo físico definitivo del carrito impulsado por ligas.",
    icon="ℹ️",
)


def format_signed(value: float, unit: str) -> str:
    return f"{value:+.2f} {unit}"


def normalized_progress(value: float, lower: float, upper: float) -> float:
    if np.isclose(lower, upper):
        return 0.0
    return float(np.clip((value - lower) / (upper - lower), 0.0, 1.0))


def render_value_bar(
    label: str,
    value: float,
    unit: str,
    lower: float,
    upper: float,
    help_text: str,
) -> None:
    st.markdown(f"**{label}**")
    st.progress(normalized_progress(value, lower, upper), text=format_signed(value, unit))
    st.caption(help_text)


def build_timeseries_figure(
    time: np.ndarray,
    values: np.ndarray,
    observation_time: float,
    observation_value: float,
    title: str,
    y_title: str,
    line_color: str,
) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=time,
            y=values,
            mode="lines",
            name=title,
            line={"color": line_color, "width": 4},
            hovertemplate=f"t = %{{x:.2f}} s<br>{y_title} = %{{y:.3f}}<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[observation_time],
            y=[observation_value],
            mode="markers",
            name="Instante observado",
            marker={
                "size": 14,
                "color": ESPOL_BLUE,
                "line": {"color": "#FFFFFF", "width": 3},
            },
            hovertemplate=f"t = %{{x:.2f}} s<br>{y_title} = %{{y:.3f}}<extra></extra>",
        )
    )
    figure.add_vline(
        x=observation_time,
        line_width=1.5,
        line_dash="dash",
        line_color=MUTED_TEXT,
    )
    figure.update_layout(
        height=430,
        margin={"l": 15, "r": 15, "t": 35, "b": 15},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        showlegend=False,
        hovermode="x unified",
        font={"family": "Inter, Segoe UI, Arial", "color": ESPOL_BLUE},
        xaxis={
            "title": "Tiempo, t (s)",
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


def build_speedometer(speed: float, maximum_speed: float) -> go.Figure:
    gauge_max = max(1.0, maximum_speed * 1.15)
    first_limit = gauge_max * 0.45
    second_limit = gauge_max * 0.75

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=speed,
            number={"suffix": " m/s", "valueformat": ".2f", "font": {"size": 42}},
            title={"text": "Velocidad instantánea", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, gauge_max], "tickwidth": 1},
                "bar": {"color": ESPOL_BLUE, "thickness": 0.30},
                "bgcolor": "#FFFFFF",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, first_limit], "color": "rgba(56,169,224,0.18)"},
                    {"range": [first_limit, second_limit], "color": "rgba(22,119,184,0.22)"},
                    {"range": [second_limit, gauge_max], "color": "rgba(0,28,67,0.18)"},
                ],
                "threshold": {
                    "line": {"color": TECH_CYAN, "width": 5},
                    "thickness": 0.8,
                    "value": speed,
                },
            },
        )
    )
    figure.update_layout(
        height=330,
        margin={"l": 30, "r": 30, "t": 55, "b": 15},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, Arial", "color": ESPOL_BLUE},
    )
    return figure


st.markdown("## 1. Configura el movimiento")
with st.container(border=True):
    left, right = st.columns(2, gap="large")

    with left:
        initial_position = st.slider(
            "Posición inicial, x₀ (m)",
            min_value=-2.0,
            max_value=2.0,
            value=0.0,
            step=0.05,
            help="Ubicación del carrito en el instante inicial.",
        )
        initial_velocity = st.slider(
            "Velocidad inicial, v₀ (m/s)",
            min_value=-5.0,
            max_value=5.0,
            value=1.5,
            step=0.1,
            help="Velocidad del carrito al comenzar la simulación.",
        )

    with right:
        acceleration = st.slider(
            "Aceleración, a (m/s²)",
            min_value=-5.0,
            max_value=5.0,
            value=-0.5,
            step=0.1,
            help="Tasa de cambio de la velocidad.",
        )
        duration = st.slider(
            "Duración de la simulación (s)",
            min_value=1.0,
            max_value=15.0,
            value=6.0,
            step=0.5,
            help="Intervalo temporal mostrado en las gráficas.",
        )

parameters = KinematicParameters(
    initial_position=initial_position,
    initial_velocity=initial_velocity,
    acceleration=acceleration,
    duration=duration,
)
simulation = simulate_motion(parameters)

st.markdown("## 2. Selecciona el instante de observación")
observation_time = st.slider(
    "Tiempo observado, t (s)",
    min_value=0.0,
    max_value=float(duration),
    value=min(float(duration) / 2.0, float(duration)),
    step=0.05,
    help="Este control sincroniza las barras, las gráficas y el velocímetro.",
)
state = instantaneous_state(parameters, observation_time)

st.markdown("## 3. Estado instantáneo del carrito")
metric_columns = st.columns(4, gap="medium")
metric_columns[0].metric("Tiempo", f"{state['time']:.2f} s", border=True)
metric_columns[1].metric("Posición", f"{state['position']:.2f} m", border=True)
metric_columns[2].metric("Velocidad", f"{state['velocity']:.2f} m/s", border=True)
metric_columns[3].metric("Aceleración", f"{state['acceleration']:.2f} m/s²", border=True)

bars_column, gauge_column = st.columns([1.15, 1], gap="large")

with bars_column:
    with st.container(border=True):
        st.markdown("### Barras dinámicas")

        position_min = float(np.min(simulation["position"]))
        position_max = float(np.max(simulation["position"]))
        velocity_min = float(np.min(simulation["velocity"]))
        velocity_max = float(np.max(simulation["velocity"]))

        render_value_bar(
            "Posición",
            state["position"],
            "m",
            position_min,
            position_max,
            "Escala relativa al recorrido calculado durante la simulación.",
        )
        render_value_bar(
            "Velocidad",
            state["velocity"],
            "m/s",
            velocity_min,
            velocity_max,
            "Escala relativa al intervalo de velocidades calculado.",
        )
        render_value_bar(
            "Aceleración",
            state["acceleration"],
            "m/s²",
            -5.0,
            5.0,
            "El centro de la escala corresponde a aceleración nula.",
        )

with gauge_column:
    with st.container(border=True):
        maximum_speed = float(np.max(np.abs(simulation["velocity"])))
        st.plotly_chart(
            build_speedometer(state["speed"], maximum_speed),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        direction = "hacia adelante" if state["velocity"] > 0 else "hacia atrás"
        if np.isclose(state["velocity"], 0.0, atol=0.02):
            direction = "momentáneamente en reposo"
        st.caption(
            f"El carrito se encuentra **{direction}**. La rapidez máxima calculada "
            f"en el intervalo es **{maximum_speed:.2f} m/s**."
        )

st.markdown("## 4. Evolución temporal")
position_tab, velocity_tab, acceleration_tab = st.tabs(
    ["Posición", "Velocidad", "Aceleración"]
)

with position_tab:
    st.plotly_chart(
        build_timeseries_figure(
            simulation["time"],
            simulation["position"],
            state["time"],
            state["position"],
            "Posición",
            "Posición, x (m)",
            INTERACTIVE_BLUE,
        ),
        use_container_width=True,
        config={"displaylogo": False, "responsive": True},
    )

with velocity_tab:
    st.plotly_chart(
        build_timeseries_figure(
            simulation["time"],
            simulation["velocity"],
            state["time"],
            state["velocity"],
            "Velocidad",
            "Velocidad, v (m/s)",
            TECH_CYAN,
        ),
        use_container_width=True,
        config={"displaylogo": False, "responsive": True},
    )

with acceleration_tab:
    st.plotly_chart(
        build_timeseries_figure(
            simulation["time"],
            simulation["acceleration"],
            state["time"],
            state["acceleration"],
            "Aceleración",
            "Aceleración, a (m/s²)",
            SECONDARY_BLUE,
        ),
        use_container_width=True,
        config={"displaylogo": False, "responsive": True},
    )

with st.expander("Ecuaciones utilizadas en esta versión"):
    st.latex(r"x(t)=x_0+v_0t+\frac{1}{2}at^2")
    st.latex(r"v(t)=v_0+at")
    st.latex(r"a(t)=a")
    st.caption(
        "Estas ecuaciones representan un movimiento rectilíneo con aceleración constante "
        "y funcionan como base para validar la interacción visual de la plataforma."
    )

render_footer()
