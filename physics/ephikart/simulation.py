"""Funciones de simulación para la vista de predicción de e(Phi)Kart."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class KinematicParameters:
    """Parámetros de un movimiento rectilíneo con aceleración constante."""

    initial_position: float
    initial_velocity: float
    acceleration: float
    duration: float
    samples: int = 301


def simulate_motion(parameters: KinematicParameters) -> dict[str, np.ndarray]:
    """Calcula tiempo, posición, velocidad y aceleración del carrito."""
    time = np.linspace(0.0, parameters.duration, parameters.samples)
    position = (
        parameters.initial_position
        + parameters.initial_velocity * time
        + 0.5 * parameters.acceleration * time**2
    )
    velocity = parameters.initial_velocity + parameters.acceleration * time
    acceleration = np.full_like(time, parameters.acceleration, dtype=float)

    return {
        "time": time,
        "position": position,
        "velocity": velocity,
        "acceleration": acceleration,
    }


def instantaneous_state(
    parameters: KinematicParameters,
    observation_time: float,
) -> dict[str, float]:
    """Devuelve el estado cinemático para un instante determinado."""
    bounded_time = min(max(observation_time, 0.0), parameters.duration)
    position = (
        parameters.initial_position
        + parameters.initial_velocity * bounded_time
        + 0.5 * parameters.acceleration * bounded_time**2
    )
    velocity = parameters.initial_velocity + parameters.acceleration * bounded_time

    return {
        "time": bounded_time,
        "position": position,
        "velocity": velocity,
        "speed": abs(velocity),
        "acceleration": parameters.acceleration,
    }
