"""P5 ePhiKart: síntesis y PDF de la sesión P1–P4 (versión provisional)."""
from __future__ import annotations
from datetime import datetime
from io import BytesIO
import math
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from components.footer import render_footer
from components.header import render_header
from components.top_navigation import render_top_navigation

BLUE = colors.HexColor('#075A9E')


def _num(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def _fmt(v, unit='', digits=4):
    n = _num(v)
    return f'{n:.{digits}f} {unit}'.strip() if n is not None else 'No registrado'


def _velocity(fit, video_time):
    if not isinstance(fit, dict):
        return None
    t0 = _num(fit.get('time_origin_video_s'))
    coeff = fit.get('coefficients') or {}
    a, b, c = (_num(coeff.get(k)) for k in ('A', 'B', 'C'))
    if None in (t0, a, b):
        return None
    tau = video_time - t0
    quad = fit.get('model') == 'Cuadrático'
    if fit.get('variable') == 'Posición x(t)':
        return 2*a*tau+b if quad else a
    return a*tau*tau+b*tau+(c or 0.0) if quad else a*tau+b


def _snapshot():
    ss = st.session_state
    p1 = {label: ss.get(key) for label, key in (
        ('Masa predicha (kg)', 'kart_mass'),
        ('Constante elástica (N/m)', 'kart_spring_constant'),
        ('Longitud natural (m)', 'kart_natural_length'),
        ('Longitud inicial (m)', 'kart_initial_length'),
        ('Posición inicial (m)', 'kart_initial_position'),
        ('Velocidad inicial (m/s)', 'kart_initial_velocity'),
        ('Fricción (parámetro P1)', 'kart_friction'),
        ('Duración simulada (s)', 'kart_duration'),
    ) if ss.get(key) is not None}
    setup = dict(ss.get('exp_saved_snapshot') or {})
    measurement = dict(ss.get('exp_measurement_snapshot') or {})
    fits = {k: dict(v) for k, v in (ss.get('fizziq_fits') or {}).items() if isinstance(v, dict)}
    m = _num(setup.get('exp_mass_g'))
    l0 = _num(setup.get('exp_natural_cm'))
    li = _num(setup.get('exp_stretched_cm'))
    k = _num(ss.get('kart_spring_k')) or _num(ss.get('kart_k')) or _num(ss.get('kart_spring_constant')) or _num(ss.get('p4_k_manual'))
    mkg = m / 1000 if m is not None else None
    stretch = (li-l0)/100 if li is not None and l0 is not None else None
    tstart = _num(ss.get('p4_start_video'))
    tend = _num(ss.get('p4_transition_video'))
    if tstart is None and 'actuando' in fits:
        tstart = _num(fits['actuando'].get('time_origin_video_s'))
    if tend is None and 'liberada' in fits:
        tend = _num(fits['liberada'].get('time_origin_video_s'))
    vi = _velocity(fits.get('actuando'), tstart) if tstart is not None else None
    vf = _velocity(fits.get('liberada'), tend) if tend is not None else None
    e0 = 0.5*k*stretch**2 + 0.5*mkg*vi**2 if None not in (k, stretch, mkg, vi) and k > 0 and mkg > 0 and stretch > 0 else None
    ef = 0.5*mkg*vf**2 if mkg is not None and mkg > 0 and vf is not None else None
    vpred = _num(ss.get('p4_predicted_transition_velocity'))
    epred = 0.5*mkg*vpred**2 if mkg is not None and mkg > 0 and vpred is not None else None
    errv = 100*abs(vf-vpred)/abs(vpred) if vf is not None and vpred is not None and abs(vpred)>1e-12 else None
    erre = 100*abs(ef-epred)/abs(epred) if ef is not None and epred is not None and epred>1e-12 else None
    return dict(p1=p1, setup=setup, measurement=measurement, fits=fits,
                k=k, mkg=mkg, stretch=stretch, tstart=tstart, tend=tend,
                vi=vi, vf=vf, e0=e0, ef=ef, vpred=vpred,
                errv=errv, erre=erre, interpretation=ss.get('p4_interpretation', ''),
                conclusion=ss.get('p5_conclusion', ''), student=ss.get('p5_student',''),
                group=ss.get('p5_group',''), date=datetime.now().strftime('%Y-%m-%d %H:%M'))


def _pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(21*cm,29.7*cm), leftMargin=1.8*cm,
                            rightMargin=1.8*cm, topMargin=1.7*cm, bottomMargin=1.7*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='MainE', parent=styles['Title'], fontSize=17, textColor=BLUE, alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name='HeadE', parent=styles['Heading2'], fontSize=11, textColor=BLUE, spaceBefore=13, spaceAfter=6))
    styles.add(ParagraphStyle(name='SmallE', parent=styles['BodyText'], fontSize=8.4, leading=12))
    story = [Paragraph('ePhiKart | Informe experimental',styles['MainE']),
             Paragraph('Documento generado a partir de los registros disponibles en la sesión de la aplicación.', styles['SmallE']), Spacer(1,8)]
    def paragraph(txt):
        from xml.sax.saxutils import escape
        return Paragraph(escape(str(txt)).replace('\n','<br/>'),styles['SmallE'])
    def section(title, rows):
        story.append(Paragraph(title,styles['HeadE']))
        if not rows:
            story.append(paragraph('Sin datos guardados en esta sesión.'))
            return
        content = [[paragraph('Campo'),paragraph('Valor')]] + [[paragraph(k),paragraph(v)] for k,v in rows]
        table = Table(content, colWidths=[6.1*cm,11.0*cm], hAlign='LEFT', repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6EFF8')),
                                   ('GRID',(0,0),(-1,-1),0.25,colors.HexColor('#D3DBE3')),
                                   ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
                                   ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),
                                   ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(table)
    section('Identificación', [('Estudiante',data['student'] or 'No indicado'),('Equipo / paralelo',data['group'] or 'No indicado'),('Generado',data['date'])])
    section('P1. Predicción matemática', [(k,_fmt(v)) for k,v in data['p1'].items()])
    section('P2. Mediciones previas', [(k,_fmt(v) if isinstance(v,(int,float)) else str(v)) for k,v in data['setup'].items()])
    section('P2. Registro experimental manual', [(k,_fmt(v) if isinstance(v,(int,float)) else str(v)) for k,v in data['measurement'].items()])
    fitrows=[]
    for key, title in [('actuando','Liga actuando'),('liberada','Liga liberada')]:
        fit=data['fits'].get(key)
        if not fit: continue
        coeff=fit.get('coefficients') or {}
        fitrows.extend([(title, f"{fit.get('variable','?')} | {fit.get('model','?')}"),
                        ('Coeficientes',', '.join(f'{k}={v}' for k,v in coeff.items())),
                        ('Origen de tiempo video',_fmt(fit.get('time_origin_video_s'),'s')),
                        ('R²',_fmt(fit.get('r2')))])
    section('P3. Ajustes registrados en FizziQ',fitrows)
    section('P4. Contraste físico y energético',[
        ('Constante elástica k',_fmt(data['k'],'N/m')),
        ('Masa medida',_fmt(data['mkg'],'kg')),
        ('Deformación inicial',_fmt(data['stretch'],'m')),
        ('Inicio del movimiento (video)',_fmt(data['tstart'],'s')),
        ('Fin de la acción de la liga (video)',_fmt(data['tend'],'s')),
        ('Velocidad inicial estimada',_fmt(data['vi'],'m/s')),
        ('Velocidad posterior estimada',_fmt(data['vf'],'m/s')),
        ('Energía mecánica inicial estimada',_fmt(data['e0'],'J')),
        ('Energía cinética posterior estimada',_fmt(data['ef'],'J')),
        ('Diferencia energética',_fmt(data['e0']-data['ef'],'J') if data['e0'] is not None and data['ef'] is not None else 'No disponible'),
        ('Velocidad predicha (P4)',_fmt(data['vpred'],'m/s')),
        ('Error relativo de velocidad',_fmt(data['errv'],'%')),
        ('Error relativo de energía cinética',_fmt(data['erre'],'%'))])
    story.extend([Paragraph('P4. Interpretación',styles['HeadE']), paragraph(data['interpretation'] or 'Sin interpretación registrada.'),
                  Paragraph('P5. Conclusiones del equipo',styles['HeadE']),paragraph(data['conclusion'] or 'Sin conclusión registrada.'),
                  Spacer(1,12), paragraph('Notas: resultados estimados con los coeficientes registrados; una diferencia de energía no demuestra por sí sola trabajo de fricción. Las magnitudes faltantes no se reemplazan por datos inventados. La extrapolación de ajustes fuera del tramo medido debe verificarse con el video.')])
    def page(canvas, document):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(1.8*cm,1.05*cm,'ePhiKart | Informe provisional')
        canvas.drawRightString(19.2*cm,1.05*cm,f'Página {document.page}')
    doc.build(story,onFirstPage=page,onLaterPages=page)
    return buffer.getvalue()


def render_results(show_header=True,show_footer=True,show_top_navigation=False):
    if show_top_navigation: render_top_navigation()
    if show_header:
        render_header(eyebrow='e(Phi)Kart',title='Informe de resultados',
                      subtitle='Revisa tu trabajo y descarga el informe de la experiencia.',
                      badge='P5 · Informe provisional')
    st.markdown('## 5. Informe experimental')
    st.caption('Se incluyen los datos guardados durante esta sesión. Descarga el PDF antes de cerrar o actualizar la aplicación.')
    c1,c2=st.columns(2)
    with c1: st.text_input('Nombre del estudiante o integrantes',key='p5_student',placeholder='Integrantes del equipo')
    with c2: st.text_input('Equipo / paralelo',key='p5_group',placeholder='Ej.: Equipo 3')
    data=_snapshot()
    sections=[('P1 · Predicción',bool(data['p1'])),('P2 · Mediciones',bool(data['setup'])),
              ('P3 · FizziQ',len(data['fits'])==2),('P4 · Contraste',data['e0'] is not None and data['ef'] is not None)]
    st.markdown('### 5.1. Revisión de los registros')
    for label,ok in sections:
        st.write(('✅ ' if ok else '⚠️ ')+label+(' — disponible' if ok else ' — incompleto'))
    st.markdown('### 5.2. Síntesis energética')
    a,b=st.columns(2)
    a.metric('Energía mecánica inicial',_fmt(data['e0'],'J'))
    b.metric('Energía cinética posterior',_fmt(data['ef'],'J'))
    if data['e0'] is not None and data['ef'] is not None:
        st.metric('Diferencia energética',_fmt(data['e0']-data['ef'],'J'))
    if data['errv'] is not None or data['erre'] is not None:
        st.write(f"Error de velocidad: **{_fmt(data['errv'],'%')}** · Error de energía cinética: **{_fmt(data['erre'],'%')}**")
    st.markdown('### 5.3. Conclusión del equipo')
    st.text_area('¿Se cumplieron las predicciones? ¿Qué diferencias encontraste y qué las podría explicar?',
                 key='p5_conclusion',height=130,placeholder='Escribe tus conclusiones a partir de los resultados obtenidos.')
    st.markdown('### 5.4. Entrega del informe')
    if not all(ok for _,ok in sections):
        st.warning('Hay apartados incompletos. Puedes descargar un informe parcial, pero revisa los registros antes de entregarlo.')
    st.caption('El PDF incorpora los parámetros de P1, registros de P2, ajustes de P3, cálculos e interpretación de P4 y la conclusión de P5. No incluye capturas de las gráficas interactivas.')
    try:
        pdf=_pdf(_snapshot())
        st.download_button('📄 Generar y descargar informe PDF',data=pdf,
                           file_name=f"ePhiKart_informe_{datetime.now().strftime('%Y%m%d')}.pdf",
                           mime='application/pdf',type='primary',use_container_width=True)
    except Exception as exc:
        st.error(f'No se pudo generar el informe PDF: {exc}')
    if show_footer: render_footer()

if __name__=='__main__':
    render_results(True,True,True)
