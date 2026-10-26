from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation


# P3-A/B/C · FIZZIQ IMPORT / IMPORTACIÓN FIZZIQ
# ES: Cada archivo representa un segmento observado; no inferir liberación.
# EN: Each file represents an observed segment; do not infer release.
MAX_CSV_BYTES = 5 * 1024 * 1024


def _read_fizziq_csv(data: bytes) -> tuple[pd.DataFrame, dict]:
    """ES: Lee CSV con coma decimal. EN: Parse decimal-comma CSV files."""
    if not data:
        raise ValueError("El archivo CSV está vacío.")
    if len(data) > MAX_CSV_BYTES:
        raise ValueError("El CSV supera el límite de 5 MB.")
    text = None
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeError:
            continue
    if text is None:
        raise ValueError("No se pudo interpretar la codificación del archivo.")
    if not text.strip():
        raise ValueError("El archivo no contiene datos.")
    # ES: FizziQ puede anteponer título, fecha y líneas vacías.
    # EN: FizziQ may prepend title, date and empty lines.
    lines = text.splitlines()
    header_index = None
    for i, line in enumerate(lines):
        for delimiter_candidate in (";", ",", "\t"):
            fields = [v.strip().lower() for v in line.split(delimiter_candidate)]
            if len(fields) >= 2 and any(re.fullmatch(r"t(?:\(s\))?|tiempo(?:\s*\(s\))?|time", f) for f in fields) and any(re.fullmatch(r"x(?:\(m\))?|vx(?:\(m/s\))?|posici[oó]n|velocidad", f) for f in fields):
                header_index = i
                delimiter = delimiter_candidate
                break
        if header_index is not None:
            break
    if header_index is None:
        raise ValueError("No se encontró una fila de encabezados con tiempo y posición o velocidad.")
    raw = pd.read_csv(io.StringIO("\n".join(lines[header_index:])), sep=delimiter,
                      dtype=str, keep_default_na=False, engine="python")
    raw.columns = [str(c).strip().lstrip("\ufeff") for c in raw.columns]
    raw = raw.loc[:, ~raw.columns.str.match(r"^Unnamed:")]
    if raw.empty:
        raise ValueError("El CSV no tiene filas de mediciones.")
    if len(set(raw.columns)) != len(raw.columns):
        raise ValueError("El CSV contiene nombres de columnas duplicados.")
    return raw, {"delimiter": delimiter, "rows": len(raw), "metadata_lines": header_index}


def _number_series(series: pd.Series) -> pd.Series:
    """ES: Convierte decimales locales. EN: Convert localized decimals."""
    values = series.astype(str).str.strip().str.replace("\u00a0", "", regex=False)
    values = values.str.replace(" ", "", regex=False)
    # ES: 1.234,56 -> 1234.56; 1,23 -> 1.23.
    # EN: Handle thousands dots and decimal commas.
    comma = values.str.contains(",", regex=False)
    values.loc[comma] = values.loc[comma].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(values.replace("", np.nan), errors="coerce")


def _guess(columns: list[str], kind: str) -> int:
    patterns = {
        "time": (r"^t\s*\(?s\)?$", r"^tiempo", r"^time"),
        "position": (r"^x\s*\(?m\)?$", r"^posici", r"^position"),
        "velocity": (r"^vx\s*\(?m/s\)?$", r"^velocidad", r"^velocity"),
    }
    for i, col in enumerate(columns):
        if any(re.search(p, col.strip().lower()) for p in patterns[kind]):
            return i
    return 0 if kind == "time" else min(1, len(columns) - 1)


def _validated_segment(raw: pd.DataFrame, time_col: str, pos_col: str | None,
                       vel_col: str | None) -> tuple[pd.DataFrame, dict]:
    """ES: Admite posición, velocidad o ambas. EN: Accept position, velocity or both."""
    selected = [c for c in (time_col, pos_col, vel_col) if c is not None]
    if len(selected) != len(set(selected)):
        raise ValueError("Tiempo, posición y velocidad deben utilizar columnas diferentes.")
    if pos_col is None and vel_col is None:
        raise ValueError("Selecciona al menos una magnitud: posición o velocidad.")
    t = _number_series(raw[time_col])
    x = _number_series(raw[pos_col]) if pos_col else pd.Series(np.nan, index=raw.index)
    v = _number_series(raw[vel_col]) if vel_col else pd.Series(np.nan, index=raw.index)
    clean = pd.DataFrame({"t_video_s": t, "x_m": x, "vx_m_s": v})
    clean = clean.replace([np.inf, -np.inf], np.nan)
    missing_t = int(clean["t_video_s"].isna().sum())
    missing_x = int(clean["x_m"].isna().sum()) if pos_col else None
    missing_v = int(clean["vx_m_s"].isna().sum()) if vel_col else None
    clean = clean.dropna(subset=["t_video_s"]).copy()
    clean = clean.dropna(subset=["x_m", "vx_m_s"], how="all").copy()
    if len(clean) < 2:
        raise ValueError("Se necesitan al menos dos registros válidos con tiempo y alguna magnitud medida.")
    duplicates = int(clean["t_video_s"].duplicated().sum())
    nonmonotonic = int((clean["t_video_s"].diff().dropna() < 0).sum())
    clean = clean.sort_values("t_video_s", kind="stable").drop_duplicates("t_video_s", keep="first").reset_index(drop=True)
    if len(clean) < 2:
        raise ValueError("No hay suficientes tiempos distintos para construir el segmento.")
    clean.insert(1, "t_segmento_s", clean["t_video_s"] - clean["t_video_s"].iloc[0])
    return clean, {
        "missing_time": missing_t, "missing_position": missing_x,
        "missing_velocity": missing_v, "duplicate_times": duplicates,
        "out_of_order": nonmonotonic, "valid_rows": len(clean),
        "valid_position": int(clean["x_m"].notna().sum()),
        "valid_velocity": int(clean["vx_m_s"].notna().sum()),
    }


# P3-D · EXPERIMENTAL VELOCITY / VELOCIDAD EXPERIMENTAL
# ES: Ajustes independientes por régimen, sin inventar valores ausentes.
# EN: Separate regime fits; never synthesize missing measurements.
def _velocity_fit(frame: pd.DataFrame) -> dict | None:
    valid = frame[["t_video_s", "vx_m_s"]].dropna()
    if len(valid) < 3 or valid["t_video_s"].nunique() < 3:
        return None
    t = valid["t_video_s"].to_numpy(dtype=float)
    v = valid["vx_m_s"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(t, v, 1)
    predicted = slope * t + intercept
    ss_tot = float(np.sum((v - v.mean()) ** 2))
    r2 = float(1 - np.sum((v - predicted) ** 2) / ss_tot) if ss_tot > 1e-15 else None
    return {"slope": float(slope), "intercept": float(intercept), "r2": r2,
            "tmin": float(t.min()), "tmax": float(t.max()), "count": len(t)}


def _show_velocity_analysis(saved: dict) -> None:
    st.markdown("## Gráfica experimental de velocidad")
    st.caption("Tres mediciones del mismo video. Los puntos son datos medidos; las rectas son ajustes independientes de cada régimen.")
    frames = {key: pd.DataFrame(segment["data"]) for key, segment in saved.items()}
    all_times = [float(t) for frame in frames.values() for t in frame["t_video_s"].dropna()]
    if not all_times:
        return
    default_start = min([float(seg.get("first_video_time", min(all_times))) for seg in saved.values()])
    # ES: La retirada del dedo se confirma en el video, no en el ajuste.
    # EN: Finger release is established by video observation, not fitting.
    t0 = st.number_input("Instante en que se retira el dedo, según el video (s)",
                         min_value=0.0, value=round(default_start, 3), step=0.001,
                         format="%.3f", key="fizziq_start_video")
    relative = st.toggle("Mostrar tiempo desde que se retira el dedo", value=True,
                         key="fizziq_relative_time")
    show_fits = st.toggle("Mostrar ajustes lineales por régimen", value=True,
                          key="fizziq_show_fits")
    colors = {"completo": "#627D98", "actuando": "#F59E0B", "liberada": "#1677B8"}
    names = {"completo": "Movimiento completo", "actuando": "Liga actuando", "liberada": "Liga liberada"}
    fig = go.Figure()
    fits = {}
    for key in ("completo", "actuando", "liberada"):
        if key not in frames:
            continue
        frame = frames[key].dropna(subset=["t_video_s", "vx_m_s"])
        if frame.empty:
            continue
        times = frame["t_video_s"].to_numpy(dtype=float)
        velocities = frame["vx_m_s"].to_numpy(dtype=float)
        fig.add_trace(go.Scatter(x=times-t0 if relative else times, y=velocities,
                                 mode="markers+lines" if key == "completo" else "markers",
                                 name=names[key], marker={"size": 9, "color": colors[key]},
                                 line={"color": colors[key], "width": 1.5},
                                 hovertemplate="t = %{x:.3f} s<br>Vx = %{y:.4f} m/s<extra>%{fullData.name}</extra>"))
        if key in ("actuando", "liberada"):
            fit = _velocity_fit(frame)
            if fit:
                fits[key] = fit
                if show_fits:
                    tt = np.array([fit["tmin"], fit["tmax"]])
                    fig.add_trace(go.Scatter(x=tt-t0 if relative else tt,
                                             y=fit["slope"]*tt+fit["intercept"],
                                             mode="lines", name="Ajuste: "+names[key],
                                             line={"color": colors[key], "width": 3, "dash": "dash"}))
    fig.update_layout(height=420, margin={"l": 10, "r": 10, "t": 15, "b": 30},
                      xaxis_title="Tiempo desde inicio (s)" if relative else "Tiempo del video (s)",
                      yaxis_title="Velocidad Vx (m/s)", hovermode="closest",
                      legend={"orientation": "h", "y": -0.28},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF")
    fig.update_xaxes(fixedrange=True, gridcolor="rgba(98,125,152,0.18)")
    fig.update_yaxes(fixedrange=True, gridcolor="rgba(98,125,152,0.18)")
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False, "staticPlot": True, "responsive": True})
    if fits:
        st.markdown("### Ajustes de velocidad por régimen")
        for key in ("actuando", "liberada"):
            if key in fits:
                fit = fits[key]
                r2 = f"{fit['r2']:.3f}" if fit["r2"] is not None else "No definido"
                # Center at t0 to make the intercept interpretable to students.
                b_rel = fit["slope"]*t0 + fit["intercept"]
                st.write(f"**{names[key]}:** Vx = ({fit['slope']:.5f} m/s²) · t + ({b_rel:.5f} m/s); R² = {r2}; n = {fit['count']}")
        st.caption("En las ecuaciones, t es el tiempo transcurrido desde el instante indicado arriba. Los ajustes describen los datos, no sustituyen la observación del video.")
    if "actuando" in fits and "liberada" in fits:
        a, b = fits["actuando"], fits["liberada"]
        denominator = a["slope"]-b["slope"]
        st.markdown("### Estimación del cambio de régimen")
        if abs(denominator) < 1e-9:
            st.warning("Las pendientes son casi iguales: no hay una intersección estable para estimar la transición.")
        else:
            crossing = (b["intercept"]-a["intercept"])/denominator
            gap_start, gap_end = a["tmax"], b["tmin"]
            if gap_start <= crossing <= gap_end:
                st.metric("Intersección estimada de las rectas", f"{crossing-t0:.3f} s desde el inicio")
                st.caption(f"Equivale a t = {crossing:.3f} s del video. Estimación por extrapolación, no medición directa.")
            else:
                st.warning(f"La intersección calculada ({crossing:.3f} s del video) cae fuera del intervalo entre mediciones ({gap_start:.3f}–{gap_end:.3f} s). No se acepta como instante físico de transición.")
        st.info("Comprueba en el video cuándo la liga deja de impulsar el carrito. La retirada del dedo marca el inicio del movimiento, no necesariamente el fin del impulso elástico.")
    elif saved:
        st.info("Guarda ambos segmentos («Liga actuando» y «Liga liberada») para comparar sus ajustes y estimar la transición.")


def render_fizziq(show_header: bool = True, show_footer: bool = True, show_top_navigation: bool = False) -> None:
    """ES: Importación por régimen. EN: Regime-aware CSV import."""
    if show_top_navigation:
        render_top_navigation()
    if show_header:
        render_header(
            eyebrow="e(Phi)Kart", title="Análisis FizziQ",
            subtitle="Importa segmentos experimentales del movimiento registrados en video.",
            badge="Importación y validación CSV",
        )

    st.markdown("## Importación de datos experimentales")
    st.info("Puedes cargar el movimiento completo y, por separado, los tramos con la liga actuando y liberada. Todos corresponden al mismo video. El inicio ocurre al retirar el dedo; la liberación de la liga es un evento posterior.")
    regime = st.radio("Régimen físico del segmento", ("Movimiento completo", "Liga actuando", "Liga liberada"), horizontal=True)
    uploaded = st.file_uploader("Archivo CSV exportado desde FizziQ", type=["csv"], key="fizziq_csv_upload")
    if uploaded is not None:
        try:
            raw, meta = _read_fizziq_csv(uploaded.getvalue())
        except (ValueError, pd.errors.ParserError, UnicodeError) as exc:
            st.error(f"No se pudo importar el archivo: {exc}")
        else:
            st.success(f"CSV leído: {meta['rows']} filas · separador {repr(meta['delimiter'])} · {len(raw.columns)} columnas")
            st.markdown("### Identificación de columnas")
            columns = list(raw.columns)
            time_col = st.selectbox("Tiempo del video (s)", columns, index=_guess(columns, "time"), key="fizziq_time_col")
            pos_options = ["No disponible"] + columns
            pos_default = _guess(columns, "position") + 1 if any(re.search(r"^x(?:\(m\))?$|posici|position", c.lower()) for c in columns) else 0
            pos_choice = st.selectbox("Posición x (m), opcional", pos_options, index=pos_default, key="fizziq_pos_col")
            pos_col = None if pos_choice == "No disponible" else pos_choice
            velocity_options = ["No disponible"] + columns
            vel_guess = _guess(columns, "velocity")
            velocity_default = vel_guess + 1 if any(re.search(r"^vx|velocidad|velocity", c.lower()) for c in columns) else 0
            vel_choice = st.selectbox("Velocidad Vx (m/s), opcional", velocity_options, index=velocity_default, key="fizziq_vel_col")
            vel_col = None if vel_choice == "No disponible" else vel_choice
            try:
                clean, checks = _validated_segment(raw, time_col, pos_col, vel_col)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.markdown("### Validación de mediciones")
                a, b, c = st.columns(3)
                a.metric("Registros válidos", checks["valid_rows"])
                b.metric("Tiempo inicial del video", f"{clean['t_video_s'].iloc[0]:.3f} s")
                c.metric("Tiempo final del video", f"{clean['t_video_s'].iloc[-1]:.3f} s")
                warnings = []
                if checks["missing_time"] or (checks["missing_position"] or 0):
                    warnings.append(f"Tiempos ausentes: {checks['missing_time']}; posiciones ausentes: {checks['missing_position'] or 0}. Se excluyen solo filas sin tiempo ni magnitud medida.")
                if checks["missing_velocity"]:
                    warnings.append(f"Velocidades ausentes: {checks['missing_velocity']} (no se reemplazan por cero).")
                if checks["duplicate_times"]:
                    warnings.append(f"Tiempos duplicados: {checks['duplicate_times']} (se conserva la primera medición).")
                if checks["out_of_order"]:
                    warnings.append(f"Retrocesos temporales en el archivo: {checks['out_of_order']} (se ordena por tiempo).")
                if warnings:
                    for warning in warnings:
                        st.warning(warning)
                else:
                    st.success("No se detectaron problemas en las columnas seleccionadas.")
                st.caption("t_video_s es el tiempo original de FizziQ; t_segmento_s empieza en cero únicamente para este segmento. No es el tiempo de liberación.")
                st.dataframe(clean, use_container_width=True, hide_index=True)
                st.markdown("### Registrar el segmento")
                st.caption("La clasificación se realiza según la observación del video; no se infiere mediante ajustes automáticos.")
                if st.button("Guardar segmento validado", type="primary", use_container_width=True):
                    key = {"Movimiento completo": "completo", "Liga actuando": "actuando", "Liga liberada": "liberada"}[regime]
                    st.session_state.setdefault("fizziq_segments", {})[key] = {
                        "regime": regime, "filename": uploaded.name,
                        "data": clean.to_dict(orient="records"), "checks": checks,
                        "first_video_time": float(_number_series(raw[time_col]).dropna().iloc[0]),
                    }
                    st.success(f"Segmento «{regime}» guardado en esta sesión.")
    saved = st.session_state.get("fizziq_segments", {})
    if saved:
        st.markdown("### Segmentos disponibles en esta sesión")
        for key in ("completo", "actuando", "liberada"):
            if key in saved:
                segment = saved[key]
                st.write(f"**{segment['regime']}** · {segment['filename']} · {len(segment['data'])} mediciones · x: {segment['checks']['valid_position']} · Vx: {segment['checks']['valid_velocity']}")
        st.caption("Los datos permanecen en la sesión de Streamlit. Todavía no se realiza el ajuste matemático ni se determina el instante de liberación.")
    if saved:
        _show_velocity_analysis(saved)
    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_fizziq(show_header=True, show_footer=True, show_top_navigation=True)
