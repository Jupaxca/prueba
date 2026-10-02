```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import numpy as np
import streamlit.components.v1 as components
import time

# 1. Configuración de la página
st.set_page_config(
    page_title="Dashboard Gerencial - Aduanas",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de CSS Premium (Corregida para NO romper la UI nativa)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Aplicar Inter de forma segura, solo a elementos de texto principales */
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6 {
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
        
        /* Ocultar footer pero DEJAR el header visible para las opciones */
        footer {visibility: hidden;}
        header[data-testid="stHeader"] { background-color: transparent !important; }
        
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.25rem;
            padding: 1.75rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
            margin-bottom: 1.25rem;
            height: 100%;
        }
        
        .metric-title {
            color: #94a3b8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-value {
            font-size: 2.2rem; 
            font-weight: 700;
            margin-top: 0.5rem;
            line-height: 1.1;
            white-space: nowrap !important;
            display: inline-block;
        }
        
        .text-green { color: #10b981; }
        .text-red { color: #ef4444; }
        .text-blue { color: #3b82f6; }
        .text-orange { color: #f97316; }
        
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            color: #e2e8f0;
        }
        .custom-table th {
            background-color: rgba(15, 23, 42, 0.5);
            color: #94a3b8;
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #334155;
            font-weight: 600;
        }
        .custom-table td {
            padding: 1rem;
            border-bottom: 1px solid #1e293b;
        }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-weight: 600; font-size: 0.7rem; white-space: nowrap;}
        .badge-red { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-weight: 600; font-size: 0.7rem; white-space: nowrap;}
        
        /* ESTILOS PARA IMPRESIÓN (PDF) */
        @media print {
            body { background-color: white !important; color: black !important; }
            .stApp { background-color: white !important; }
            section[data-testid="stSidebar"] { display: none !important; }
            .stDeployButton { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }
            .glass-card { background: white !important; border: 1px solid #ccc !important; box-shadow: none !important; color: black !important; break-inside: avoid; }
            .metric-title { color: #555 !important; }
            .metric-value { color: #000 !important; }
            .text-white { color: black !important; }
            h1, h2, h3, h4, p { color: black !important; }
            .custom-table th { background-color: #eee !important; color: black !important; }
            .custom-table td, .custom-table th { border-bottom: 1px solid #ddd !important; }
            /* Ocultar botones de Streamlit al imprimir */
            .stButton { display: none !important; }
            .print-hide { display: none !important; }
        }
    </style>
""", unsafe_allow_html=True)

# 3. Función de conexión a datos
@st.cache_data(ttl=300)
def load_data(url):
    try:
        if "/d/" in url:
            doc_id = url.split("/d/")[1].split("/")[0]
        else:
            return None, "URL inválida"
        
        csv_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
        response = requests.get(csv_url)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        if 'CUMPLIMIENTO' in df.columns:
            df['CUMPLIMIENTO'] = df['CUMPLIMIENTO'].astype(str).str.lower().str.strip()
            
        for col in ['MEDICION ESPERADA', 'MEDICION REAL']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df, None
    except Exception as e:
        return None, f"Error de conexión: {str(e)}"

def main():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown('<h2 style="color:white; font-weight: 600;">🔎 Filtros</h2>', unsafe_allow_html=True)
        default_url = "https://docs.google.com/spreadsheets/d/1l5rXqFgHcUyNSQB_s82UTrHxVlpV6GHb4Yobegd-t2g/edit?usp=drivesdk"
        
        # El expander nativo funciona bien ahora que el CSS se corrigió
        with st.expander("⚙️ Origen de Datos", expanded=False):
            url_input = st.text_input("URL de Google Sheets", default_url, key="sheet_url")
            
        df, error = load_data(url_input)
        
        df_filtered = None
        if df is not None and not df.empty:
            estados = ['Todos'] + list(df['CUMPLIMIENTO'].dropna().unique())
            filtro_estado = st.selectbox("Estado del KPI", estados, index=0)
            filtro_texto = st.text_input("Buscar...", "")
            
            df_filtered = df.copy()
            if filtro_estado != 'Todos':
                df_filtered = df_filtered[df_filtered['CUMPLIMIENTO'] == filtro_estado]
            if filtro_texto:
                df_filtered = df_filtered[df_filtered['INDICADOR'].str.contains(filtro_texto, case=False, na=False)]
        
        st.markdown("---")
        # Botón de refrescar corregido con un pequeño delay para feedback visual
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            with st.spinner('Actualizando...'):
                st.cache_data.clear()
                time.sleep(0.5)
            st.rerun()
            
    if error:
        st.error(error)
        return
    if df is None or df.empty or df_filtered is None or df_filtered.empty:
        st.warning("No hay datos para mostrar.")
        return

    # --- MOTOR ANALÍTICO ---
    total_kpis = len(df_filtered)
    cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'cumple'])
    no_cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'no cumple'])
    salud_pct = (cumplen / total_kpis * 100) if total_kpis > 0 else 0

    df_tiempos = df_filtered[df_filtered['MEDIDA'].str.contains('dia|día', case=False, na=False)]
    retraso_dias = sum([row['MEDICION REAL'] - row['MEDICION ESPERADA'] for _, row in df_tiempos.iterrows() if (row['MEDICION REAL'] - row['MEDICION ESPERADA']) > 0])

    df_finanzas = df_filtered[df_filtered['INDICADOR'].str.contains('Facturacion|flete', case=False, na=False)]
    fuga_costos = 0
    if not df_finanzas.empty:
        fuga_costos = df_finanzas['MEDICION REAL'].sum() - df_finanzas['MEDICION ESPERADA'].sum()

    # --- HEADER / TÍTULO DINÁMICO ---
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown('<h1 style="color: #60a5fa; font-weight: 700; margin-bottom: 0; font-size: 2.5rem;">🚢 Command Center Operativo</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #94a3b8; font-size: 1rem; margin-top: 0.25rem;">Control de Indicadores de Aduana y Logística</p>', unsafe_allow_html=True)
    with col_t2:
        if no_cumplen > 0:
            html_estado = '<span style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-block;">⚠️ Atención Requerida</span>'
        else:
            html_estado = '<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-block;">🟢 Óptimo</span>'
            
        st.markdown(f'<div style="text-align: right; padding-top: 1rem;">{html_estado}</div>', unsafe_allow_html=True)
        
        # Nueva instrucción para PDF amigable (Opción A refinada)
        st.markdown("""
            <div class="print-hide" style="text-align: right; margin-top: 0.8rem; font-size: 0.85rem; color: #64748b; background: rgba(30, 41, 59, 0.5); padding: 0.5rem; border-radius: 0.5rem; border: 1px dashed #334155;">
                💡 Para exportar a PDF presiona <br><b>Ctrl + P</b> (Windows) o <b>Cmd + P</b> (Mac)
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 1. SCORECARDS ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        color_salud = "text-red" if salud_pct < 50 else ("text-orange" if salud_pct < 80 else "text-green")
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Salud Operación <span style="float:right; opacity:0.3; font-size:1.5rem;">❤️‍🩹</span></div>
                <div class="metric-value {color_salud}">{salud_pct:.1f}%</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">{cumplen} de {total_kpis} logradas</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        border_alerta = "border: 1px solid rgba(239, 68, 68, 0.3);" if no_cumplen > 0 else ""
        color_alerta = "text-red" if no_cumplen > 0 else "text-green"
        st.markdown(f"""
            <div class="glass-card" style="{border_alerta}">
                <div class="metric-title">Alertas Activas <span style="float:right; opacity:0.3; font-size:1.5rem;">🚨</span></div>
                <div class="metric-value {color_alerta}">{no_cumplen}</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">Procesos fuera de meta</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        color_retraso = "text-orange" if retraso_dias > 0 else "text-green"
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Desvío Tiempos <span style="float:right; opacity:0.3; font-size:1.5rem;">⏱️</span></div>
                <div class="metric-value {color_retraso}">+{int(retraso_dias)} Días</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">Retraso acumulado</div>
            </div>
        """, unsafe_allow_html=True)
        
    # --- 2. GRÁFICOS (Corregidos) ---
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">⏱️ Brecha de Tiempos (Esperado vs Real)</h3>', unsafe_allow_html=True)
        if not df_tiempos.empty:
            df_t = df_tiempos.sort_values('MEDICION ESPERADA', ascending=True)
            nombres = [str(x)[:20] + '...' if len(str(x)) > 20 else str(x) for x in df_t['INDICADOR']]
            
            fig1 = go.Figure()
            
            # Cuadrícula de fondo ligera para guiar el ojo
            fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', zeroline=False)
            fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', zeroline=False)

            # Línea conectora más delgada
            for i in range(len(df_t)):
                esp = df_t['MEDICION ESPERADA'].iloc[i]
                real = df_t['MEDICION REAL'].iloc[i]
                # Si cumple es gris (sin alerta), si no cumple es rojo
                color_linea = 'rgba(239, 68, 68, 0.5)' if real > esp else 'rgba(148, 163, 184, 0.2)' 
                fig1.add_trace(go.Scatter(
                    x=[esp, real], y=[nombres[i], nombres[i]],
                    mode='lines', line=dict(color=color_linea, width=2),
                    showlegend=False, hoverinfo='skip'
                ))
            
            # Puntos Esperados (Meta)
            fig1.add_trace(go.Scatter(
                x=df_t['MEDICION ESPERADA'], y=nombres,
                mode='markers', name='Meta',
                marker=dict(color='#3b82f6', size=10, symbol='square'), # Cuadrado azul para meta
                hovertext=df_t['INDICADOR'], hoverinfo='text+x'
            ))
            
            # Puntos Reales
            colores_real = ['#ef4444' if r > e else '#10b981' for r, e in zip(df_t['MEDICION REAL'], df_t['MEDICION ESPERADA'])]
            fig1.add_trace(go.Scatter(
                x=df_t['MEDICION REAL'], y=nombres,
                mode='markers', name='Real',
                marker=dict(color=colores_real, size=12, symbol='circle', line=dict(color='#0f172a', width=2)),
                hovertext=df_t['INDICADOR'], hoverinfo='text+x'
            ))
            
            fig1.update_layout(
                height=320, margin=dict(l=10, r=20, t=30, b=30),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter'),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=10)),
                xaxis_title="Días"
            )
            fig1.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False}) # Oculta la barra de herramientas ruidosa
        else:
            st.info("Sin datos de tiempos.")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_g2:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">💰 Indicadores Financieros ($)</h3>', unsafe_allow_html=True)
        if not df_finanzas.empty:
            # Acortar nombres para que entren bien
            nombres_finanzas = [str(x)[:15] + '...' if len(str(x)) > 15 else str(x) for x in df_finanzas['INDICADOR']]
            esp_fin = df_finanzas['MEDICION ESPERADA']
            real_fin = df_finanzas['MEDICION REAL']
            
            colores_fin_real = ['#10b981' if r <= e else '#ef4444' for r, e in zip(real_fin, esp_fin)]

            fig2 = go.Figure()
            # Usar barras ligeramente más delgadas
            fig2.add_trace(go.Bar(x=nombres_finanzas, y=esp_fin, name='Cotizado/Esp.', marker_color='rgba(59, 130, 246, 0.7)', width=0.35))
            fig2.add_trace(go.Bar(x=nombres_finanzas, y=real_fin, name='Real', marker_color=colores_fin_real, width=0.35))
            
            fig2.update_layout(
                barmode='group', height=320, 
                margin=dict(l=10, r=10, t=30, b=30),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter'),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=10)),
                bargap=0.15 # Espacio entre grupos
            )
            
            # Configurar el eje Y para que se adapte mejor si los valores son muy diferentes (escala logarítmica opcional, pero aquí usaremos lineal ajustada)
            fig2.update_yaxes(tickprefix="$", tickformat=",.0f", showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
            fig2.update_xaxes(tickangle=-45) # Rotar etiquetas para que no se corten
            
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sin datos financieros.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DIAGNÓSTICO ---
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">🎯 Cumplimiento Global</h3>', unsafe_allow_html=True)
        fig3 = go.Figure(data=[go.Pie(
            labels=['Cumplen', 'Fuera de Meta'], 
            values=[cumplen, no_cumplen],
            hole=0.6,
            marker_colors=['#10b981', '#ef4444'],
            textinfo='percent+value'
        )])
        fig3.update_layout(
            height=250, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc', family='Inter'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_g4:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">🚨 Top Cuellos de Botella</h3>', unsafe_allow_html=True)
        df_retrasos = df_tiempos[df_tiempos['MEDICION REAL'] > df_tiempos['MEDICION ESPERADA']].copy()
        if not df_retrasos.empty:
            df_retrasos['DESVIACION'] = df_retrasos['MEDICION REAL'] - df_retrasos['MEDICION ESPERADA']
            df_retrasos = df_retrasos.sort_values('DESVIACION', ascending=True).tail(5) 
            
            nombres_retrasos = [str(x)[:22] + '...' if len(str(x)) > 22 else str(x) for x in df_retrasos['INDICADOR']]
            
            fig4 = go.Figure(go.Bar(
                x=df_retrasos['DESVIACION'], y=nombres_retrasos, orientation='h',
                marker_color='#f97316', text=df_retrasos['DESVIACION'], textposition='auto'
            ))
            fig4.update_layout(
                height=250, margin=dict(l=10, r=20, t=10, b=30),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(title='Días de retraso')
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.markdown("<p style='color:#10b981; text-align:center; padding: 3rem 0; font-size: 1.1rem;'>No hay retrasos operativos. 🎉</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. TABLA E INSIGHTS ---
    col_b1, col_b2 = st.columns([2.2, 1])
    
    with col_b1:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:1rem; font-weight:600;">📊 Matriz de Rendimiento</h3>', unsafe_allow_html=True)
        
        tabla_html = "<div style='overflow-x:auto;'><table class='custom-table'><thead><tr><th>Indicador</th><th>Meta</th><th>Esperado</th><th>Real</th><th>Estado</th></tr></thead><tbody>"
        for _, row in df_filtered.iterrows():
            indicador = str(row['INDICADOR'])[:45] + "..." if len(str(row['INDICADOR'])) > 45 else row['INDICADOR']
            meta = row['META'] if 'META' in df_filtered.columns else '-'
            esp = row['MEDICION ESPERADA']
            real = row['MEDICION REAL']
            estado = row['CUMPLIMIENTO']
            
            badge = f"<span class='badge-green'>CUMPLE</span>" if estado == 'cumple' else f"<span class='badge-red'>NO CUMPLE</span>"
            color_row = "color: #ef4444; font-weight:600;" if estado == 'no cumple' else "color: #10b981; font-weight:600;"
            
            tabla_html += f"<tr><td>{indicador}</td><td>{meta}</td><td>{esp}</td><td style='{color_row}'>{real}</td><td>{badge}</td></tr>"
        
        tabla_html += "</tbody></table></div>"
        st.markdown(tabla_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_b2:
        st.markdown('<div class="glass-card" style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(59, 130, 246, 0.3);"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:1rem; font-weight:600;">💡 Insights</h3>', unsafe_allow_html=True)
        
        if no_cumplen > 0:
            peor_desfase_tiempo = df_tiempos[df_tiempos['CUMPLIMIENTO'] == 'no cumple'].sort_values(by='MEDICION REAL', ascending=False).head(1)
            
            if not peor_desfase_tiempo.empty:
                nombre_peor = peor_desfase_tiempo.iloc[0]['INDICADOR']
                real_peor = peor_desfase_tiempo.iloc[0]['MEDICION REAL']
                esp_peor = peor_desfase_tiempo.iloc[0]['MEDICION ESPERADA']
                pct_retraso = ((real_peor - esp_peor) / esp_peor) * 100 if esp_peor > 0 else 0
                
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #ef4444; margin-bottom: 0.8rem;">
                    <h4 style="color: white; margin: 0 0 0.25rem 0; font-size: 0.9rem;">🔴 Mayor Retraso</h4>
                    <p style="color: #cbd5e1; font-size: 0.8rem; margin: 0;"><strong>"{nombre_peor}"</strong> tarda {pct_retraso:.0f}% más de lo esperado.</p>
                </div>
                """, unsafe_allow_html=True)
                
            if fuga_costos > 0:
                st.markdown(f"""
                <div style="background: rgba(249, 115, 22, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #f97316; margin-bottom: 0.8rem;">
                    <h4 style="color: white; margin: 0 0 0.25rem 0; font-size: 0.9rem;">🟠 Alerta Financiera</h4>
                    <p style="color: #cbd5e1; font-size: 0.8rem; margin: 0;">Sobrecosto total de <strong>${fuga_costos:,.0f}</strong> vs lo esperado.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
             st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #10b981; margin-bottom: 0.8rem;">
                    <h4 style="color: white; margin: 0 0 0.25rem 0; font-size: 0.9rem;">🟢 Todo Óptimo</h4>
                    <p style="color: #cbd5e1; font-size: 0.8rem; margin: 0;">Todos los indicadores cumplen sus metas.</p>
                </div>
                """, unsafe_allow_html=True)

        if fuga_costos < 0:
            st.markdown(f"""
            <div style="background: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #3b82f6;">
                <h4 style="color: white; margin: 0 0 0.25rem 0; font-size: 0.9rem;">🔵 Ahorro</h4>
                <p style="color: #cbd5e1; font-size: 0.8rem; margin: 0;">Gestión eficiente: ahorro de <strong>${abs(fuga_costos):,.0f}</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
```
