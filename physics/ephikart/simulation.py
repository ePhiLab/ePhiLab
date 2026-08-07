"""Modelo físico del carrito impulsado por una liga elástica."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


GRAVITY = 9.81


@dataclass(frozen=True)
class ElasticKartParameters:
    """Parámetros físicos de la simulación de e(Phi)Kart."""

    initial_position: float
    initial_velocity: float

    natural_length: float
    initial_length: float
    spring_constant: float

    mass: float
    friction_coefficient: float

    duration: float
    samples: int = 1201


def validate_parameters(parameters: ElasticKartParameters) -> None:
    """Valida que los parámetros físicos sean consistentes."""

    if parameters.mass <= 0:
        raise ValueError("La masa debe ser mayor que cero.")

    if parameters.spring_constant < 0:
        raise ValueError("La constante elástica no puede ser negativa.")

    if parameters.natural_length <= 0:
        raise ValueError("La longitud natural debe ser mayor que cero.")

    if parameters.initial_length < parameters.natural_length:
        raise ValueError(
            "La longitud estirada inicial debe ser mayor o igual "
            "que la longitud natural."
        )

    if parameters.friction_coefficient < 0:
        raise ValueError("El coeficiente de fricción no puede ser negativo.")

    if parameters.duration <= 0:
        raise ValueError("La duración debe ser mayor que cero.")


def simulate_motion(
    parameters: ElasticKartParameters,
) -> dict[str, np.ndarray | float | None]:
    """
    Simula el movimiento mediante integración Euler-Cromer.

    Convención:

    - x = 0 representa la posición inicial del carrito.
    - El carrito se mueve inicialmente en la dirección positiva.
    - La longitud de la liga disminuye según:

        L(t) = L_i - [x(t) - x_0]

    - La liga actúa únicamente mientras L(t) > L_0.
    - Después de soltarse la liga, solo actúa la fricción cinética.
    """

    validate_parameters(parameters)

    time = np.linspace(0.0, parameters.duration, parameters.samples)
    dt = float(time[1] - time[0])

    position = np.zeros(parameters.samples, dtype=float)
    velocity = np.zeros(parameters.samples, dtype=float)
    acceleration = np.zeros(parameters.samples, dtype=float)

    elastic_force = np.zeros(parameters.samples, dtype=float)
    friction_force = np.zeros(parameters.samples, dtype=float)
    band_length = np.zeros(parameters.samples, dtype=float)

    band_active = np.zeros(parameters.samples, dtype=bool)
    # Energías y trabajo
    kinetic_energy = np.zeros(parameters.samples, dtype=float)
    elastic_energy = np.zeros(parameters.samples, dtype=float)
    friction_work = np.zeros(parameters.samples, dtype=float)
    mechanical_energy = np.zeros(parameters.samples, dtype=float)


    

    position[0] = parameters.initial_position
    velocity[0] = parameters.initial_velocity

    release_time: float | None = None
    release_position: float | None = None

    for index in range(parameters.samples - 1):
        displacement = position[index] - parameters.initial_position

        current_length = max(
            parameters.initial_length - displacement,
            parameters.natural_length,
        )

        band_length[index] = current_length

        extension = max(
            current_length - parameters.natural_length,
            0.0,
        )
        # Energía cinética instantánea
        kinetic_energy[index] = (
            0.5
            * parameters.mass
            * velocity[index] ** 2
        )

        # Energía potencial elástica almacenada en la liga
        elastic_energy[index] = (
            0.5
            * parameters.spring_constant
            * extension ** 2
        )

        # Energía mecánica instantánea
        mechanical_energy[index] = (
            kinetic_energy[index]
            + elastic_energy[index]
        )

        is_band_active = extension > 1e-9
        band_active[index] = is_band_active

        if is_band_active:
            elastic_force[index] = parameters.spring_constant * extension
        else:
            elastic_force[index] = 0.0

            if release_time is None:
                release_time = float(time[index])
                release_position = float(position[index])

        # La fricción se opone al movimiento.
        if velocity[index] > 1e-8:
            friction_force[index] = (
                -parameters.friction_coefficient
                * parameters.mass
                * GRAVITY
            )
        elif velocity[index] < -1e-8:
            friction_force[index] = (
                parameters.friction_coefficient
                * parameters.mass
                * GRAVITY
            )
        else:
            # Al inicio, si la liga puede vencer la fricción, el carrito avanza.
            maximum_static_like_force = (
                parameters.friction_coefficient
                * parameters.mass
                * GRAVITY
            )

            if elastic_force[index] > maximum_static_like_force:
                friction_force[index] = -maximum_static_like_force
            else:
                friction_force[index] = -elastic_force[index]

        net_force = elastic_force[index] + friction_force[index]
        acceleration[index] = net_force / parameters.mass

        # Integración Euler-Cromer.
        next_velocity = velocity[index] + acceleration[index] * dt
        next_position = position[index] + next_velocity * dt

        # Una vez que la liga se soltó, el carrito no debe invertir su
        # movimiento por efecto de la fricción.
        if (
            not is_band_active
            and velocity[index] > 0
            and next_velocity < 0
        ):
            next_velocity = 0.0
            next_position = position[index]

        # Desplazamiento realizado durante este paso temporal
        delta_x = next_position - position[index]

        # Trabajo acumulado realizado por la fricción.
        # Al oponerse al movimiento normalmente será negativo.
        friction_work[index + 1] = (
            friction_work[index]
            + friction_force[index] * delta_x
        )


        velocity[index + 1] = next_velocity
        position[index + 1] = next_position

   

    # Calculamos el último estado.
    final_displacement = position[-1] - parameters.initial_position

    band_length[-1] = max(
        parameters.initial_length - final_displacement,
        parameters.natural_length,
    )

    final_extension = max(
        band_length[-1] - parameters.natural_length,
        0.0,
    )
    kinetic_energy[-1] = (
        0.5
        * parameters.mass
        * velocity[-1] ** 2    
    )

    elastic_energy[-1] = (
        0.5
        * parameters.spring_constant
        * final_extension ** 2
    )

    mechanical_energy[-1] = (
        kinetic_energy[-1]
        + elastic_energy[-1]
    )




    band_active[-1] = final_extension > 1e-9
    elastic_force[-1] = parameters.spring_constant * final_extension

    if velocity[-1] > 1e-8:
        friction_force[-1] = (
            -parameters.friction_coefficient
            * parameters.mass
            * GRAVITY
        )
    elif velocity[-1] < -1e-8:
        friction_force[-1] = (
            parameters.friction_coefficient
            * parameters.mass
            * GRAVITY
        )
    else:
        friction_force[-1] = 0.0

    acceleration[-1] = (
        elastic_force[-1] + friction_force[-1]
    ) / parameters.mass

    if release_time is None and not band_active[-1]:
        release_time = float(time[-1])
        release_position = float(position[-1])

    return {
        "time": time,
        "position": position,
        "velocity": velocity,
        "speed": np.abs(velocity),
        "acceleration": acceleration,
        "elastic_force": elastic_force,
        "friction_force": friction_force,
        "band_length": band_length,
        "band_active": band_active,
        "kinetic_energy": kinetic_energy,
        "elastic_energy": elastic_energy,
        "friction_work": friction_work,
        "mechanical_energy": mechanical_energy,
        "release_time": release_time,
        "release_position": release_position,
    }


def instantaneous_state(
    simulation: dict[str, np.ndarray | float | None],
    observation_time: float,
) -> dict[str, float | bool]:
    """Interpola el estado del carrito en el instante seleccionado."""

    time = simulation["time"]

    if not isinstance(time, np.ndarray):
        raise TypeError("La simulación no contiene un arreglo temporal válido.")

    bounded_time = float(
        np.clip(
            observation_time,
            float(time[0]),
            float(time[-1]),
        )
    )

    def interpolate(variable_name: str) -> float:
        values = simulation[variable_name]

        if not isinstance(values, np.ndarray):
            raise TypeError(
                f"La variable {variable_name} no contiene un arreglo válido."
            )

        return float(np.interp(bounded_time, time, values))

    band_active_values = simulation["band_active"]

    if not isinstance(band_active_values, np.ndarray):
        raise TypeError("El estado de la liga no es válido.")

    nearest_index = int(np.abs(time - bounded_time).argmin())

    return {
        "time": bounded_time,
        "position": interpolate("position"),
        "velocity": interpolate("velocity"),
        "speed": abs(interpolate("velocity")),
        "acceleration": interpolate("acceleration"),
        "elastic_force": interpolate("elastic_force"),
        "friction_force": interpolate("friction_force"),
        "band_length": interpolate("band_length"),
        "band_active": bool(band_active_values[nearest_index]),
        "kinetic_energy": interpolate("kinetic_energy"),
        "elastic_energy": interpolate("elastic_energy"),
        "friction_work": interpolate("friction_work"),
        "mechanical_energy": interpolate("mechanical_energy"),
    }
