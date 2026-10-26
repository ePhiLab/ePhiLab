"""ePhiKart P3: registro de tendencias de FizziQ sin importar CSV."""
from __future__ import annotations
import math
import streamlit as st
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation

REGIMES = (("actuando", "Con la liga actuando"), ("liberada", "Sin la liga actuando"))

def _finite(value):
    try:
        number = float(str(value).strip().replace(",", "."))
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None

def _register(regime):
    prefix = f"p3_{regime}_"
    variable = st.session_state[prefix + "variable"]
    degree = st.session_state[prefix + "degree"]
    labels = ("A", "B", "C") if degree == "Cuadrático" else ("A", "B")
    coefficients = {}
    for label in labels:
        val = _finite(st.session_state[prefix + label])
        if val is None:
            st.error(f"Revisa el coeficiente {label}: debe ser un número finito.")
            return
        coefficients[label] = val
    t0 = _finite(st.session_state[prefix + "t0"])
    if t0 is None:
        st.error("Ingresa un tiempo inicial válido.")
        return
    record = {"regime": regime, "variable": variable, "model": degree,
              "coefficients": coefficients, "time_origin_video_s": t0,
              "time_variable": "Tiempo relativo al inicio del tramo (s)",
              "r2": _finite(st.session_state[prefix + "r2"]),
              "source": "Ajuste realizado por estudiantes en FizziQ"}
    st.session_state.setdefault("fizziq_fits", {})[regime] = record
    st.session_state["fizziq_p3_ready"] = len(st.session_state["fizziq_fits"]) == 2
    st.success("Ajuste guardado para el contraste experimental.")

def _formula(variable, degree):
    y = "x" if variable == "Posición x(t)" else "v"
    return f"{y}(τ) = Aτ² + Bτ + C" if degree == "Cuadrático" else f"{y}(τ) = Aτ + B"

def render_fizziq(show_header=True, show_footer=True, show_top_navigation=False):
    if show_top_navigation:
        render_top_navigation()
    if show_header:
        render_header(eyebrow="e(Phi)Kart", title="Resultados de FizziQ",
                      subtitle="Obtén los ajustes en FizziQ y registra aquí sus coeficientes.",
                      badge="P3 · Registro experimental")
    st.markdown("## 3. Resultados experimentales")
    st.info("Graba el carrito y analiza su movimiento en FizziQ. Separa los tramos con y sin acción de la liga. No necesitas exportar archivos CSV.")
    st.caption("Usa τ = 0 al inicio del tramo que ajustaste. Si FizziQ usa el tiempo absoluto del video, anota ese instante para interpretar correctamente los coeficientes.")
    for regime, title in REGIMES:
        prefix = f"p3_{regime}_"
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.radio("Gráfica ajustada en FizziQ", ["Posición x(t)", "Velocidad v(t)"],
                     key=prefix + "variable", horizontal=True)
            st.radio("Modelo que mejor representa los datos", ["Lineal", "Cuadrático"],
                     key=prefix + "degree", horizontal=True)
            variable = st.session_state[prefix + "variable"]
            degree = st.session_state[prefix + "degree"]
            st.latex(_formula(variable, degree).replace("τ", r"\tau").replace("²", "^2"))
            cols = st.columns(3 if degree == "Cuadrático" else 2)
            for col, label in zip(cols, ("A", "B", "C") if degree == "Cuadrático" else ("A", "B")):
                with col:
                    st.text_input(f"Coeficiente {label}", value="0", key=prefix + label)
            st.number_input("Tiempo del video al inicio del tramo (s)", min_value=0.0,
                            value=0.0, step=0.1, format="%.3f", key=prefix + "t0")
            st.text_input("R² del ajuste (opcional)", value="", key=prefix + "r2")
            if degree == "Cuadrático" and variable == "Posición x(t)":
                st.caption("Si la aceleración es constante: a = 2A y v(τ) = 2Aτ + B.")
            elif degree == "Lineal" and variable == "Velocidad v(t)":
                st.caption("Para este ajuste: a = A.")
            elif degree == "Lineal" and variable == "Posición x(t)":
                st.caption("Este ajuste describe velocidad constante: v = A.")
            else:
                st.caption("Este ajuste representa aceleración variable: a(τ) = 2Aτ + B.")
            if st.button("Guardar este régimen", key=prefix + "save", type="primary", use_container_width=True):
                _register(regime)
            if regime in st.session_state.get("fizziq_fits", {}):
                fit = st.session_state["fizziq_fits"][regime]
                st.success(f"Guardado: {fit['model'].lower()} de {fit['variable'].lower()}.")
    saved = st.session_state.get("fizziq_fits", {})
    st.markdown("### Registro para la comparación")
    st.write(f"Regímenes registrados: **{len(saved)} de 2**")
    if len(saved) == 2:
        st.success("Los dos regímenes están listos para P4: comparación física y energética.")
    else:
        st.warning("Guarda ambos regímenes para continuar con la comparación.")
    st.caption("La aplicación no decide qué ajuste es físicamente adecuado: el estudiante debe justificar su elección con la gráfica de FizziQ.")
    if show_footer:
        render_footer()

if __name__ == "__main__":
    render_fizziq(True, True, True)
