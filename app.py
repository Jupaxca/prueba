import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# 1. Configuración de la página
st.set_page_config(
    page_title="Dashboard Gerencial - Aduanas",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de CSS Premium (Corregida para preservar íconos de Streamlit)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Aplicar Inter SOLO a elementos de texto para no romper iconos nativos (.stIcon, material-icons, etc) */
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .stMarkdown li, .stMarkdown span:not(.stIcon):not([class*="icon"]):not(.material-icons) {
            font-family: 'Inter', sans-serif !important;
        }

        .stApp {
            background-color: #0f172a;
            color: #f8fafc;
        }
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
            max-width: 96% !important;
        }
        
        /* Ocultar footer y botón deploy, pero DEJAR el header para no ocultar el menú de 3 líneas */
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        header[data-testid="stHeader"] { background-color: transparent !important; }
        
        .glass-card {
            background: #111827; /* Fondo más oscuro similar a la imagen */
            border: 1px solid #1f2937;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 1rem;
            height: 100%;
        }
        
        .metric-title {
            color: #9ca3af;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2.5rem; 
            font-weight: 700;
            line-height: 1;
            white-space: nowrap !important;
            display: inline-block;
        }
        
        .text-green { color: #34d399; }
        .text-red { color: #f87171; }
        .text-blue { color: #60a5fa; }
        .text-orange { color: #fb923c; }
        
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            color: #d1d5db;
        }
        .custom-table th {
            background-color: transparent;
            color: #9ca3af;
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid #374151;
            font-weight: 500;
        }
        .custom-table td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #1f2937;
            vertical-align: middle;
        }
        .badge-green { border: 1px solid #059669; color: #34d399; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-weight: 600; font-size: 0.7rem; letter-spacing: 0.05em; }
        .badge-red { border: 1px solid #dc2626; color: #f87171; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-weight: 600; font-size: 0.7rem; letter-spacing: 0.05em; }
        
        .insight-card-red {
            background-color: #2a161f;
            border-left: 4px solid #ef4444;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .insight-card-green {
            background-color: #132724;
            border-left: 4px solid #10b981;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .insight-card-orange {
            background-color: #2c1f16;
            border-left: 4px solid #f97316;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .insight-title {
            color: white;
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .insight-text {
            color: #cbd5e1;
            font-size: 0.85rem;
            line-height: 1.5;
            margin: 0;
        }

        /* ESTILOS PARA IMPRESIÓN (PDF) MEJORADOS */
        @media print {
            body, .stApp { background-color: white !important; color: black !important; }
            section[data-testid="stSidebar"], .stDeployButton, header[data-testid="stHeader"] { display: none !important; }
            .glass-card { background: white !important; border: 1px solid #ccc !important; box-shadow: none !important; color: black !important; break-inside: avoid; }
            .metric-title { color: #555 !important; }
            .metric-value { color: #000 !important; }
            .text-white { color: black !important; }
            h1, h2, h3, h4, p, td, th { color: black !important; }
            .custom-table th { background-color: #f1f5f9 !important; border-bottom: 2px solid #cbd5e1 !important; }
            .custom-table td { border-bottom: 1px solid #e2e8f0 !important; }
            .badge-green { border: 1px solid #10b981 !important; color: #059669 !important; }
            .badge-red { border: 1px solid #ef4444 !important; color: #dc2626 !important; }
            .print-hide, .stButton { display: none !important; }
            /* Forzar a mantener colores de fondo si el navegador lo permite */
            * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        }
    </style>
""", unsafe_allow_html=True)

# 3. Función de conexión a datos (Directo desde Google Sheets)
@st.cache_data(ttl=600)
def load_data(url):
    try:
        if "docs.google.com/spreadsheets/d/" in url:
            doc_id = url.split("/d/")[1].split("/")[0]
            # Por defecto exporta la primera hoja visible (suele ser el Tablero)
            csv_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
        else:
            return None, "URL inválida. Asegúrate de usar un enlace de Google Sheets."
        
        df = pd.read_csv(csv_url)
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        if 'CUMPLIMIENTO' in df.columns:
            df['CUMPLIMIENTO'] = df['CUMPLIMIENTO'].astype(str).str.lower().str.strip()
            
        for col in ['MEDICION ESPERADA', 'MEDICION REAL']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df, None
    except Exception as e:
        return None, f"Error al conectar con Google Sheets: Verifique que el enlace sea público (Cualquier persona con el enlace puede leer). Detalle del error: {str(e)}"

def main():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown('<h2 style="color:white; font-weight: 600; margin-bottom:1.5rem;">🔎 Filtros</h2>', unsafe_allow_html=True)
        
        default_url = "https://docs.google.com/spreadsheets/d/1l5rXqFgHcUyNSQB_s82UTrHxVlpV6GHb4Yobegd-t2g/edit?usp=drivesdk"
        
        # Filtros de Análisis
        estados = ['Todos', 'cumple', 'no cumple']
        filtro_estado = st.selectbox("Estado del KPI", estados, index=0)
        filtro_texto = st.text_input("Buscar...", "", placeholder="ej. Flete, Tiempo...")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Configuración movida abajo y dentro de expander para no ensuciar
        with st.expander("⚙️ Configuración de Datos", expanded=False):
            url_input = st.text_input("URL de Google Sheets", default_url, key="sheet_url")
            st.markdown("<p style='font-size:0.75rem; color:#94a3b8;'>El documento debe estar configurado como 'Cualquier persona con el enlace puede leer'.</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Botón de refrescar
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            with st.spinner('Actualizando desde la nube...'):
                st.cache_data.clear()
                time.sleep(0.8)
            st.rerun()

    # Cargar datos
    df, error = load_data(default_url if 'url_input' not in locals() else url_input)
    
    if error:
        st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 1.5rem; border-radius: 1rem; margin: 2rem 0;">
                <h3 style="color: #ef4444; margin-top:0;">Error de Conexión</h3>
                <p style="color: #cbd5e1;">{error}</p>
            </div>
        """, unsafe_allow_html=True)
        return
        
    if df is None or df.empty:
        st.warning("No hay datos para mostrar.")
        return

    # Aplicar filtros
    df_filtered = df.copy()
    if filtro_estado != 'Todos':
        df_filtered = df_filtered[df_filtered['CUMPLIMIENTO'] == filtro_estado]
    if filtro_texto:
        df_filtered = df_filtered[df_filtered['INDICADOR'].str.contains(filtro_texto, case=False, na=False)]

    if df_filtered.empty:
        st.warning("No hay indicadores que coincidan con la búsqueda.")
        return

    # --- MOTOR ANALÍTICO ---
    total_kpis = len(df_filtered)
    cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'cumple'])
    no_cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'no cumple'])
    salud_pct = (cumplen / total_kpis * 100) if total_kpis > 0 else 0

    # Identificar métricas financieras para excluirlas del gráfico de tiempos
    df_finanzas = df_filtered[df_filtered['INDICADOR'].astype(str).str.contains('Facturacion|flete|reconocimiento', case=False, na=False)]
    
    # El resto se consideran tiempos/procesos
    df_tiempos = df_filtered[~df_filtered['INDICADOR'].isin(df_finanzas['INDICADOR'])]

    retraso_dias = sum([row['MEDICION REAL'] - row['MEDICION ESPERADA'] for _, row in df_tiempos.iterrows() if (row['MEDICION REAL'] - row['MEDICION ESPERADA']) > 0])

    fuga_costos = 0
    if not df_finanzas.empty:
        # Sumar la diferencia neta (Real - Esperado) para ver el impacto financiero global
        fuga_costos = df_finanzas['MEDICION REAL'].sum() - df_finanzas['MEDICION ESPERADA'].sum()

    # --- HEADER / TÍTULO DINÁMICO ---
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown('<h1 style="color: #60a5fa; font-weight: 700; margin-bottom: 0; font-size: 2.2rem; display: flex; align-items: center; gap: 0.5rem;">🚢 Command Center Operativo</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-size: 0.9rem; margin-top: 0.25rem;">Control de Indicadores de Aduana y Logística</p>', unsafe_allow_html=True)
    with col_t2:
        # Lógica de Estado Mejorada (0-25, 26-50, 51-75, 76-100)
        if salud_pct <= 25:
            html_estado = '<span style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-block; white-space: nowrap;">🔴 Estado: Crítico</span>'
        elif salud_pct <= 50:
            html_estado = '<span style="background: rgba(249, 115, 22, 0.15); color: #f97316; border: 1px solid rgba(249, 115, 22, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-block; white-space: nowrap;">🟠 Estado: Malo</span>'
        elif salud_pct <= 75:
            html_estado = '<span style="background: rgba(234, 179, 8, 0.15); color: #eab308; border: 1px solid rgba(234, 179, 8, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-block; white-space: nowrap;">🟡 Estado: Medio Bueno</span>'
        else:
            html_estado = '<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-block; white-space: nowrap;">🟢 Estado: Bueno</span>'
            
        st.markdown(f'<div style="text-align: right; padding-top: 1rem;">{html_estado}</div>', unsafe_allow_html=True)
        
        # Instrucción para PDF (Nativo)
        st.markdown("""
            <div class="print-hide" style="text-align: right; margin-top: 0.8rem; font-size: 0.8rem; color: #cbd5e1; background: rgba(30, 41, 59, 0.6); padding: 0.5rem 0.75rem; border-radius: 0.5rem; border: 1px dashed #475569; display: inline-block; float: right;">
                💡 Para exportar a PDF presiona <br><b>Ctrl + P</b> (Win) o <b>Cmd + P</b> (Mac)
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><div style='clear:both;'></div>", unsafe_allow_html=True)

    # --- 1. SCORECARDS ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        color_salud = "text-red" if salud_pct <= 50 else ("text-orange" if salud_pct <= 75 else "text-orange") # Ajuste color según imagen
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">SALUD OPERACIÓN <span style="float:right; font-size:1.2rem;">❤️‍🩹</span></div>
                <div class="metric-value {color_salud}">{salud_pct:.1f}%</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:0.5rem;">{cumplen} de {total_kpis} logradas</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        border_alerta = "border: 1px solid rgba(239, 68, 68, 0.3);" if no_cumplen > 0 else ""
        color_alerta = "text-red" if no_cumplen > 0 else "text-green"
        st.markdown(f"""
            <div class="glass-card" style="{border_alerta}">
                <div class="metric-title">ALERTAS ACTIVAS <span style="float:right; font-size:1.2rem;">🚨</span></div>
                <div class="metric-value {color_alerta}">{no_cumplen}</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:0.5rem;">Procesos fuera de meta</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        color_retraso = "text-orange" if retraso_dias > 0 else "text-green"
        signo_r = "+" if retraso_dias > 0 else ""
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">DESVÍO TIEMPOS <span style="float:right; font-size:1.2rem;">⏱️</span></div>
                <div class="metric-value {color_retraso}">{signo_r}{int(retraso_dias)} Días</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:0.5rem;">Retraso acumulado</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c4:
        color_finanzas = "text-red" if fuga_costos > 0 else "text-green"
        signo_f = "+" if fuga_costos > 0 else ""
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">IMPACTO FINANCIERO <span style="float:right; font-size:1.2rem;">💰</span></div>
                <div class="metric-value {color_finanzas}">{signo_f}${abs(fuga_costos):,.0f}</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:0.5rem;">{'Sobrecosto' if fuga_costos > 0 else 'Ahorro / En meta'}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. GRÁFICO DE TIEMPOS (Brecha / Dumbbell) Y CUMPLIMIENTO GLOBAL ---
    # Redistribuimos el espacio porque quitamos el gráfico financiero
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1rem; margin-bottom:1rem; font-weight:600;">⏱️ Brecha de Tiempos (Esperado vs Real)</h3>', unsafe_allow_html=True)
        if not df_tiempos.empty:
            df_t = df_tiempos.copy() # No ordenar para mantener orden de la tabla original si se desea, o ordenar por expected
            nombres = [str(x)[:30] + '...' if len(str(x)) > 30 else str(x) for x in df_t['INDICADOR']]
            
            fig1 = go.Figure()
            fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', zeroline=False)
            fig1.update_yaxes(showgrid=False, zeroline=False) # Quitar grid horizontal para mayor limpieza

            # Líneas conectoras
            for i in range(len(df_t)):
                esp = df_t['MEDICION ESPERADA'].iloc[i]
                real = df_t['MEDICION REAL'].iloc[i]
                color_linea = '#ef4444' if real > esp else 'rgba(148, 163, 184, 0.2)' 
                fig1.add_trace(go.Scatter(
                    x=[esp, real], y=[nombres[i], nombres[i]],
                    mode='lines', line=dict(color=color_linea, width=2),
                    showlegend=False, hoverinfo='skip'
                ))
            
            # Puntos Meta (Cuadrado Azul)
            fig1.add_trace(go.Scatter(
                x=df_t['MEDICION ESPERADA'], y=nombres,
                mode='markers', name='Meta',
                marker=dict(color='#3b82f6', size=8, symbol='square'),
                hovertext=df_t['INDICADOR'], hoverinfo='text+x'
            ))
            
            # Puntos Real (Círculo Verde o Rojo)
            colores_real = ['#ef4444' if r > e else '#10b981' for r, e in zip(df_t['MEDICION REAL'], df_t['MEDICION ESPERADA'])]
            fig1.add_trace(go.Scatter(
                x=df_t['MEDICION REAL'], y=nombres,
                mode='markers', name='Real',
                marker=dict(color=colores_real, size=8, symbol='circle'),
                hovertext=df_t['INDICADOR'], hoverinfo='text+x'
            ))
            
            fig1.update_layout(
                height=350, margin=dict(l=10, r=20, t=10, b=30),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter', size=11),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=11), itemwidth=30)
            )
            fig1.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sin datos de tiempos en la vista actual.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1rem; margin-bottom:0.5rem; font-weight:600;">🎯 Distribución de Cumplimiento</h3>', unsafe_allow_html=True)
        fig3 = go.Figure(data=[go.Pie(
            labels=['Cumplen', 'Fuera de Meta'], 
            values=[cumplen, no_cumplen],
            hole=0.6,
            marker_colors=['#10b981', '#ef4444'],
            textinfo='percent+value',
            textfont=dict(color='white')
        )])
        fig3.update_layout(
            height=300, margin=dict(l=10, r=10, t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9ca3af', family='Inter'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            showlegend=True
        )
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)


    # --- 3. MATRIZ DE RENDIMIENTO E INSIGHTS COMPLETOS ---
    # Layout redistribuido: 70% Tabla, 30% Insights
    col_b1, col_b2 = st.columns([2.5, 1])
    
    with col_b1:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1rem; margin-bottom:1rem; font-weight:600;">📊 Matriz de Rendimiento de Procesos</h3>', unsafe_allow_html=True)
        
        tabla_html = "<div style='overflow-x:auto;'><table class='custom-table'><thead><tr><th>Indicador</th><th>Meta</th><th>Esperado</th><th>Real</th><th>Estado</th></tr></thead><tbody>"
        for _, row in df_filtered.iterrows():
            # Truncar un poco menos para mejor lectura
            indicador = str(row['INDICADOR'])[:60] + "..." if len(str(row['INDICADOR'])) > 60 else row['INDICADOR']
            meta = row['META'] if 'META' in df_filtered.columns else '-'
            esp = row['MEDICION ESPERADA']
            real = row['MEDICION REAL']
            estado = row['CUMPLIMIENTO']
            
            badge = f"<span class='badge-green'>CUMPLE</span>" if estado == 'cumple' else f"<span class='badge-red'>NO CUMPLE</span>"
            color_real = "color: #ef4444; font-weight:600;" if estado == 'no cumple' else "color: #10b981; font-weight:600;"
            
            # Formatear números si son enteros para que no salgan .0 si no es necesario
            esp_str = f"{int(esp)}" if esp % 1 == 0 else f"{esp}"
            real_str = f"{int(real)}" if real % 1 == 0 else f"{real}"
            
            tabla_html += f"<tr><td>{indicador}</td><td>{meta}</td><td>{esp_str}</td><td style='{color_real}'>{real_str}</td><td>{badge}</td></tr>"
        
        tabla_html += "</tbody></table></div>"
        st.markdown(tabla_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_b2:
        st.markdown('<div style="margin-top: 0.5rem;"><h3 class="text-white" style="font-size:1rem; margin-bottom:1rem; font-weight:600;">💡 Insights y Diagnóstico</h3>', unsafe_allow_html=True)
        
        # 1. Analizar Cuellos de Botella (Lo Malo)
        peor_desfase_tiempo = df_tiempos[df_tiempos['CUMPLIMIENTO'] == 'no cumple'].copy()
        if not peor_desfase_tiempo.empty:
            peor_desfase_tiempo['DESV'] = peor_desfase_tiempo['MEDICION REAL'] - peor_desfase_tiempo['MEDICION ESPERADA']
            peor_desfase_tiempo = peor_desfase_tiempo.sort_values(by='DESV', ascending=False).head(1)
            nombre_peor = peor_desfase_tiempo.iloc[0]['INDICADOR']
            real_peor = peor_desfase_tiempo.iloc[0]['MEDICION REAL']
            esp_peor = peor_desfase_tiempo.iloc[0]['MEDICION ESPERADA']
            pct_retraso = ((real_peor - esp_peor) / esp_peor) * 100 if esp_peor > 0 else 0
            
            st.markdown(f"""
            <div class="insight-card-red">
                <div class="insight-title">
                    <span style="color:#ef4444; font-size:1.2rem;">🔴</span> Mayor Retraso
                </div>
                <p class="insight-text">El proceso <strong>"{nombre_peor}"</strong> está tardando un {pct_retraso:.0f}% más de lo estipulado ({int(real_peor)} vs {int(esp_peor)} días).</p>
            </div>
            """, unsafe_allow_html=True)
            
        # 2. Analizar Sobrecostos (Lo Malo)
        if fuga_costos > 0:
            st.markdown(f"""
            <div class="insight-card-orange">
                <div class="insight-title">
                    <span style="color:#f97316; font-size:1.2rem;">🟠</span> Alerta Financiera
                </div>
                <p class="insight-text">Las desviaciones están generando un sobrecosto acumulado de <strong>${fuga_costos:,.0f}</strong> frente a lo cotizado.</p>
            </div>
            """, unsafe_allow_html=True)

        # 3. Analizar Aciertos de Tiempos (Lo Bueno)
        mejores_tiempos = df_tiempos[df_tiempos['CUMPLIMIENTO'] == 'cumple'].copy()
        if not mejores_tiempos.empty:
            num_aciertos = len(mejores_tiempos)
            st.markdown(f"""
            <div class="insight-card-green">
                <div class="insight-title">
                    <span style="color:#10b981; font-size:1.2rem;">🟢</span> Eficiencia Operativa
                </div>
                <p class="insight-text">Hay <strong>{num_aciertos} métricas de tiempo</strong> que se están cumpliendo a la perfección dentro del SLA esperado.</p>
            </div>
            """, unsafe_allow_html=True)

        # 4. Analizar Ahorros (Lo Bueno)
        if fuga_costos < 0:
            st.markdown(f"""
            <div class="insight-card-green" style="border-left-color: #3b82f6;">
                <div class="insight-title">
                    <span style="color:#3b82f6; font-size:1.2rem;">🔵</span> Ahorro Financiero
                </div>
                <p class="insight-text">Excelente gestión: se ha logrado un ahorro de <strong>${abs(fuga_costos):,.0f}</strong> respecto al presupuesto base.</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Mensaje de paz si no hay nada malo (Cero sobrecostos y cero retrasos)
        if no_cumplen == 0:
             st.markdown("""
                <div class="insight-card-green">
                    <div class="insight-title">🏆 Operación Excelente</div>
                    <p class="insight-text">No se detectan desviaciones ni cuellos de botella en la información actual.</p>
                </div>
                """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
