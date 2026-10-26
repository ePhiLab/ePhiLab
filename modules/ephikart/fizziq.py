from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

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
    try:
        delimiter = csv.Sniffer().sniff(text[:4096], delimiters=";,\t").delimiter
    except csv.Error:
        delimiter = ";" if text.splitlines()[0].count(";") >= text.splitlines()[0].count(",") else ","
    raw = pd.read_csv(io.StringIO(text), sep=delimiter, dtype=str, keep_default_na=False)
    raw.columns = [str(c).strip().lstrip("\ufeff") for c in raw.columns]
    raw = raw.loc[:, ~raw.columns.str.match(r"^Unnamed:")]
    if raw.empty:
        raise ValueError("El CSV no tiene filas de mediciones.")
    if len(set(raw.columns)) != len(raw.columns):
        raise ValueError("El CSV contiene nombres de columnas duplicados.")
    return raw, {"delimiter": delimiter, "rows": len(raw)}


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


def _validated_segment(raw: pd.DataFrame, time_col: str, pos_col: str, vel_col: str | None) -> tuple[pd.DataFrame, dict]:
    if time_col == pos_col or (vel_col is not None and vel_col in (time_col, pos_col)):
        raise ValueError("Tiempo, posición y velocidad deben utilizar columnas diferentes.")
    t = _number_series(raw[time_col])
    x = _number_series(raw[pos_col])
    v = _number_series(raw[vel_col]) if vel_col else pd.Series(np.nan, index=raw.index)
    missing_t = int(t.isna().sum())
    missing_x = int(x.isna().sum())
    missing_v = int(v.isna().sum()) if vel_col else None
    clean = pd.DataFrame({"t_video_s": t, "x_m": x, "vx_m_s": v})
    clean = clean.replace([np.inf, -np.inf], np.nan)
    clean = clean.dropna(subset=["t_video_s", "x_m"]).copy()
    if len(clean) < 2:
        raise ValueError("Se necesitan al menos dos registros válidos de tiempo y posición.")
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
    }


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
    st.info("Carga por separado el tramo con la liga actuando y el tramo posterior a la liberación. El CSV no determina por sí solo cuándo se soltó la liga.")
    regime = st.radio("Régimen físico del segmento", ("Liga actuando", "Liga liberada"), horizontal=True)
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
            pos_col = st.selectbox("Posición x (m)", columns, index=_guess(columns, "position"), key="fizziq_pos_col")
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
                if checks["missing_time"] or checks["missing_position"]:
                    warnings.append(f"Filas sin tiempo: {checks['missing_time']}; sin posición: {checks['missing_position']} (se excluyen).")
                if checks["missing_velocity"]:
                    warnings.append(f"Velocidades ausentes: {checks['missing_velocity']} (se conservan las posiciones).")
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
                    key = "actuando" if regime == "Liga actuando" else "liberada"
                    st.session_state.setdefault("fizziq_segments", {})[key] = {
                        "regime": regime, "filename": uploaded.name,
                        "data": clean.to_dict(orient="records"), "checks": checks,
                    }
                    st.success(f"Segmento «{regime}» guardado en esta sesión.")
    saved = st.session_state.get("fizziq_segments", {})
    if saved:
        st.markdown("### Segmentos disponibles en esta sesión")
        for key in ("actuando", "liberada"):
            if key in saved:
                segment = saved[key]
                st.write(f"**{segment['regime']}** · {segment['filename']} · {len(segment['data'])} mediciones")
        st.caption("Los datos permanecen en la sesión de Streamlit. Todavía no se realiza el ajuste matemático ni se determina el instante de liberación.")
    if show_footer:
        render_footer()


if __name__ == "__main__":
    render_fizziq(show_header=True, show_footer=True, show_top_navigation=True)
