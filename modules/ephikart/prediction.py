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
