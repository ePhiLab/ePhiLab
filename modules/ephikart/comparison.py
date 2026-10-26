"""ePhiKart P4 — contraste físico y energético de ajustes FizziQ (sin CSV)."""
from __future__ import annotations
import math
import streamlit as st
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation


def _fit_velocity(fit, video_time):
    """Return velocity in m/s or None for a position/velocity polynomial fit."""
    tau = video_time - float(fit['time_origin_video_s'])
    co = fit['coefficients']
    a, b, c = float(co['A']), float(co['B']), float(co.get('C', 0))
    is_quad = fit['model'] == 'Cuadrático'
    if fit['variable'] == 'Posición x(t)':
        return (2*a*tau+b) if is_quad else a
    return (a*tau*tau+b*tau+c) if is_quad else (a*tau+b)


def _fit_acceleration(fit, video_time):
    tau = video_time - float(fit['time_origin_video_s'])
    a, b = float(fit['coefficients']['A']), float(fit['coefficients']['B'])
    if fit['variable'] == 'Posición x(t)':
        return 2*a if fit['model'] == 'Cuadrático' else 0.0
    return (2*a*tau+b) if fit['model'] == 'Cuadrático' else a


def _metric_error(reference, measured):
    if abs(reference) < 1e-12:
        return None
    return 100*abs(measured-reference)/abs(reference)


def _fmt(value, unit='', digits=4):
    return f'{value:.{digits}f} {unit}'.strip()


def render_comparison(show_header=True, show_footer=True, show_top_navigation=False):
    if show_top_navigation:
        render_top_navigation()
    if show_header:
        render_header(eyebrow='e(Phi)Kart', title='Contraste experimental',
                      subtitle='Compara las predicciones con los resultados del carrito.',
                      badge='P4 · Interpretación física')
    st.markdown('## 4. Predicción frente al experimento')
    fits = st.session_state.get('fizziq_fits', {})
    setup = st.session_state.get('exp_saved_snapshot') or {}
    if not all(k in fits for k in ('actuando', 'liberada')):
        st.warning('Primero guarda los ajustes de ambos regímenes en P3.')
        if show_footer: render_footer()
        return
    if not setup:
        st.warning('Primero guarda las mediciones previas en P2.')
        if show_footer: render_footer()
        return

    m = float(setup['exp_mass_g'])/1000
    stretch = (float(setup['exp_stretched_cm'])-float(setup['exp_natural_cm']))/100
    if m <= 0 or stretch <= 0:
        st.error('Revisa en P2 la masa y las longitudes de la liga.')
        return
    k_p1 = st.session_state.get('kart_spring_k')
    # P1 stores its spring constant under kart_k (verify with installed P1).
    if k_p1 is None:
        k_p1 = st.session_state.get('kart_k')
    if k_p1 is None:
        k_p1 = st.session_state.get('kart_spring_constant')
    st.markdown('### 4.1. Magnitudes iniciales')
    col1,col2,col3 = st.columns(3)
    col1.metric('Masa medida',_fmt(m,'kg',3))
    col2.metric('Deformación inicial',_fmt(stretch,'m',3))
    if k_p1 is None:
        st.info('Indica la constante elástica k utilizada en P1; no se encontró una clave compatible en la sesión.')
        k = st.number_input('Constante elástica k (N/m)', min_value=0.001, value=10.0, step=0.5, key='p4_k_manual')
    else:
        k = float(k_p1)
        st.caption(f'Constante elástica recuperada de P1: k = {k:.3f} N/m.')
    elastic_initial = 0.5*k*stretch**2
    col3.metric('Energía elástica inicial',_fmt(elastic_initial,'J'))
    st.caption('Se supone que la liga se aproxima mediante Eₑ = ½k(ΔL)². La masa y la deformación proceden de P2.')

    st.markdown('### 4.2. Instantes que se compararán')
    st.write('Consulta el video y anota el instante aproximado en que la liga deja de actuar. No necesitas encontrar un fotograma exacto.')
    c1,c2 = st.columns(2)
    with c1:
        start_video = st.number_input('Inicio del movimiento en el video (s)',min_value=0.0,value=float(fits['actuando']['time_origin_video_s']),step=0.05,format='%.3f',key='p4_start_video')
    with c2:
        transition_video = st.number_input('Fin de la acción de la liga en el video (s)',min_value=0.0,value=max(float(fits['liberada']['time_origin_video_s']),start_video+0.1),step=0.05,format='%.3f',key='p4_transition_video')
    if transition_video <= start_video:
        st.error('El fin de la acción de la liga debe ser posterior al inicio del movimiento.')
        return
    fit_with,fit_without = fits['actuando'],fits['liberada']
    v_start = _fit_velocity(fit_with,start_video)
    v_end_with = _fit_velocity(fit_with,transition_video)
    v_end_without = _fit_velocity(fit_without,transition_video)
    a_start = _fit_acceleration(fit_with,start_video)
    a_after = _fit_acceleration(fit_without,transition_video)
    st.markdown('### 4.3. Velocidades y aceleraciones obtenidas de FizziQ')
    st.dataframe([
        {'Magnitud':'Velocidad inicial (con liga)','Resultado':_fmt(v_start,'m/s')},
        {'Magnitud':'Velocidad al final (extrapolación con liga)','Resultado':_fmt(v_end_with,'m/s')},
        {'Magnitud':'Velocidad al inicio del tramo sin liga','Resultado':_fmt(v_end_without,'m/s')},
        {'Magnitud':'Aceleración inicial con liga','Resultado':_fmt(a_start,'m/s²')},
        {'Magnitud':'Aceleración inicial sin liga','Resultado':_fmt(a_after,'m/s²')},
    ],hide_index=True,use_container_width=True)
    st.caption('Los valores se calculan a partir de los coeficientes registrados en P3; no son nuevas mediciones.')
    st.warning('Si el instante seleccionado está fuera del tramo ajustado, el resultado es una extrapolación. Comprueba que el valor sea compatible con el video.')

    st.markdown('### 4.4. Balance energético experimental')
    initial_kinetic = 0.5*m*v_start**2
    initial_total = elastic_initial+initial_kinetic
    final_kinetic = 0.5*m*v_end_without**2
    diff = initial_total-final_kinetic
    c1,c2 = st.columns(2)
    c1.metric('Energía mecánica inicial estimada',_fmt(initial_total,'J'))
    c2.metric('Energía cinética tras la liga',_fmt(final_kinetic,'J'))
    st.bar_chart([{'Estado': 'Inicial', 'Energía (J)': initial_total}, {'Estado': 'Tras liberarse la liga', 'Energía (J)': final_kinetic}], x='Estado', y='Energía (J)')
    st.metric('Diferencia del balance energético',_fmt(diff,'J'))
    if initial_total > 0:
        st.metric('Fracción no recuperada como energía cinética',f'{100*diff/initial_total:.1f} %')
    st.caption('La diferencia NO es automáticamente trabajo de fricción: también puede incluir pérdidas en ruedas, rotación, deformaciones, sonido y errores de medición. Se supone altura constante y que la liga ya no almacena energía al final.')
    if diff < -1e-8:
        st.warning('La energía cinética estimada supera la energía mecánica inicial: revisa ajustes, tiempos, unidades y supuestos del modelo.')
    st.markdown('### 4.5. Contraste con la predicción de P1')
    v_pred = st.number_input('Velocidad predicha por P1 al finalizar la acción de la liga (m/s)',value=0.0,step=0.01,format='%.3f',key='p4_predicted_transition_velocity',help='Lee el valor de la simulación de P1 en el instante de transición. No lo confundas con la velocidad final del video.')
    if abs(v_pred)>1e-12:
        err = _metric_error(v_pred,v_end_without)
        st.metric('Error relativo de velocidad',f'{err:.1f} %')
        k_pred = 0.5*m*v_pred**2
        st.metric('Energía cinética predicha en transición',_fmt(k_pred,'J'))
        err_energy = _metric_error(k_pred,final_kinetic)
        if err_energy is not None:
            st.metric('Error relativo de energía cinética',f'{err_energy:.1f} %')
    else:
        st.info('Introduce la velocidad predicha en P1 para calcular los errores. No se calcula error porcentual respecto de cero.')
    st.markdown('### 4.6. Interpretación')
    st.text_area('¿Qué diferencias observas y qué podría explicarlas?',key='p4_interpretation',height=100,placeholder='Compara los valores y considera las condiciones del experimento.')
    st.caption('Los datos se mantienen en esta sesión; no se modifica el modelo ni los controles de P1/P2.')
    if show_footer: render_footer()

if __name__ == '__main__':
    render_comparison(True,True,True)
