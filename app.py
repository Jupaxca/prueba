import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io
import numpy as np

# 1. Configuración de la página (Debe ser la primera instrucción)
st.set_page_config(
    page_title="Dashboard Gerencial - Aduanas",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de CSS Premium
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"], [class*="st-"] {
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
        
        /* Ocultar solo footer, NO el header para mantener el botón lateral */
        footer {visibility: hidden;}
        
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
        
        /* Asegurar que los números no salten de línea */
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
            padding: 1.25rem 1rem;
            text-align: left;
            border-bottom: 1px solid #334155;
            font-weight: 600;
        }
        .custom-table td {
            padding: 1.25rem 1rem;
            border-bottom: 1px solid #1e293b;
        }
        .custom-table tr:hover {
            background-color: rgba(30, 41, 59, 0.4);
        }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 0.35rem 0.65rem; border-radius: 0.35rem; font-weight: 600; font-size: 0.75rem; white-space: nowrap;}
        .badge-red { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 0.35rem 0.65rem; border-radius: 0.35rem; font-weight: 600; font-size: 0.75rem; white-space: nowrap;}
        
        .stPlotlyChart { margin-top: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# 3. Función de conexión a datos (Apuntando directo a la hoja principal)
@st.cache_data(ttl=300)
def load_data(url):
    try:
        if "/d/" in url:
            doc_id = url.split("/d/")[1].split("/")[0]
        else:
            return None, "URL inválida"
        
        # Exporta por defecto la pestaña activa/primera
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
        df, error = load_data(default_url)
        
        df_filtered = None
        if df is not None and not df.empty:
            estados = ['Todos'] + list(df['CUMPLIMIENTO'].dropna().unique())
            filtro_estado = st.selectbox("Estado del KPI", estados, index=0)
            filtro_texto = st.text_input("Buscar (ej. Flete)...", "")
            
            df_filtered = df.copy()
            if filtro_estado != 'Todos':
                df_filtered = df_filtered[df_filtered['CUMPLIMIENTO'] == filtro_estado]
            if filtro_texto:
                df_filtered = df_filtered[df_filtered['INDICADOR'].str.contains(filtro_texto, case=False, na=False)]
        
        st.markdown("---")
        st.markdown('<p style="color:#94a3b8; font-size:0.85rem;">Conexión a Datos En Vivo</p>', unsafe_allow_html=True)
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
    if error:
        st.error(error)
        return
    if df is None or df.empty or df_filtered is None or df_filtered.empty:
        st.warning("No hay datos para mostrar con los filtros actuales.")
        return

    # --- MOTOR ANALÍTICO ---
    total_kpis = len(df_filtered)
    cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'cumple'])
    no_cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'no cumple'])
    salud_pct = (cumplen / total_kpis * 100) if total_kpis > 0 else 0

    df_tiempos = df_filtered[df_filtered['MEDIDA'].str.contains('dia|día', case=False, na=False)]
    retraso_dias = sum([row['MEDICION REAL'] - row['MEDICION ESPERADA'] for _, row in df_tiempos.iterrows() if (row['MEDICION REAL'] - row['MEDICION ESPERADA']) > 0])

    fuga_costos = 0
    df_finanzas = df_filtered[df_filtered['INDICADOR'].str.contains('Facturacion|flete', case=False, na=False)]
    
    if not df_finanzas.empty:
        rec_esperado = df_finanzas[df_finanzas['INDICADOR'].str.contains('reconcimiento|reconocimiento', case=False, na=False)]['MEDICION ESPERADA'].sum()
        rec_real = df_finanzas[df_finanzas['INDICADOR'].str.contains('reconcimiento|reconocimiento', case=False, na=False)]['MEDICION REAL'].sum()
        fuga_costos += (rec_real - rec_esperado)
        
        flete_esperado = df_finanzas[df_finanzas['INDICADOR'].str.contains('flete', case=False, na=False)]['MEDICION ESPERADA'].sum()
        flete_real = df_finanzas[df_finanzas['INDICADOR'].str.contains('flete', case=False, na=False)]['MEDICION REAL'].sum()
        fuga_costos -= (flete_esperado - flete_real)

    # --- HEADER / TÍTULO DINÁMICO ---
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown('<h1 style="color: #60a5fa; font-weight: 700; margin-bottom: 0; font-size: 2.5rem;">🚢 Command Center Operativo</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #94a3b8; font-size: 1rem; margin-top: 0.25rem;">Control de Indicadores de Aduana y Logística - Corte Actual</p>', unsafe_allow_html=True)
    with col_t2:
        if no_cumplen > 0:
            html_estado = '<span style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; white-space: nowrap; display: inline-block; margin-bottom: 0.5rem;">⚠️ Estado: Atención Requerida</span>'
        else:
            html_estado = '<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.6rem 1.2rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; white-space: nowrap; display: inline-block; margin-bottom: 0.5rem;">🟢 Estado: Óptimo</span>'
            
        st.markdown(f'<div style="text-align: right; padding-top: 1rem;">{html_estado}</div>', unsafe_allow_html=True)
        
        st.markdown("""
            <div style="text-align: right; margin-top: 0.5rem;">
                <button onclick="window.print()" style="background-color: #3b82f6; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 500; cursor: pointer; transition: background-color 0.3s;">
                    🖨️ Guardar Reporte PDF
                </button>
            </div>
            <style>
                @media print {
                    section[data-testid="stSidebar"] { display: none !important; }
                    .stDeployButton { display: none !important; }
                    header[data-testid="stHeader"] { display: none !important; }
                    button[onclick="window.print()"] { display: none !important; }
                    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
                }
            </style>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 1. SCORECARDS ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        color_salud = "text-red" if salud_pct < 50 else ("text-orange" if salud_pct < 80 else "text-green")
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Salud de la Operación <span style="float:right; opacity:0.3; font-size:1.5rem;">❤️‍🩹</span></div>
                <div class="metric-value {color_salud}">{salud_pct:.1f}%</div>
                <div style="font-size:0.85rem; color:#94a3b8; margin-top:0.75rem;">{cumplen} de {total_kpis} metas logradas</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        border_alerta = "border: 1px solid rgba(239, 68, 68, 0.3);" if no_cumplen > 0 else ""
        color_alerta = "text-red" if no_cumplen > 0 else "text-green"
        st.markdown(f"""
            <div class="glass-card" style="{border_alerta}">
                <div class="metric-title">Alertas Activas <span style="float:right; opacity:0.3; font-size:1.5rem;">🚨</span></div>
                <div class="metric-value {color_alerta}">{no_cumplen}</div>
                <div style="font-size:0.85rem; color:#94a3b8; margin-top:0.75rem;">Procesos fuera de meta</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        color_retraso = "text-orange" if retraso_dias > 0 else "text-green"
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Desviación en Tiempos <span style="float:right; opacity:0.3; font-size:1.5rem;">⏱️</span></div>
                <div class="metric-value {color_retraso}">+{int(retraso_dias)} Días</div>
                <div style="font-size:0.85rem; color:#94a3b8; margin-top:0.75rem;">Retraso operativo acumulado</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c4:
        signo = "+" if fuga_costos > 0 else ""
        color_fuga = "text-red" if fuga_costos > 0 else "text-green"
        texto_fuga = "Sobrecosto" if fuga_costos > 0 else "Ahorro/En Presupuesto"
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Impacto Financiero <span style="float:right; opacity:0.3; font-size:1.5rem;">💰</span></div>
                <div class="metric-value {color_fuga}">{signo}${abs(fuga_costos):,.0f}</div>
                <div style="font-size:0.85rem; color:#94a3b8; margin-top:0.75rem;">{texto_fuga} vs Cotización</div>
            </div>
        """, unsafe_allow_html=True)

    # --- 2. GRÁFICOS PRINCIPALES ---
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">⏱️ Eje Tiempos (SLA)</h3>', unsafe_allow_html=True)
        if not df_tiempos.empty:
            nombres_cortos = [str(x)[:18] + '...' if len(str(x)) > 18 else str(x) for x in df_tiempos['INDICADOR']]
            nombres_completos = df_tiempos['INDICADOR'].tolist()
            
            esperado = df_tiempos['MEDICION ESPERADA']
            real = df_tiempos['MEDICION REAL']
            colores_real = ['#10b981' if r <= e else '#ef4444' for r, e in zip(real, esperado)]
            
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=nombres_cortos, y=esperado, name='Meta (Días)', marker_color='#3b82f6', opacity=0.8, hovertext=nombres_completos, hoverinfo="text+y"))
            fig1.add_trace(go.Bar(x=nombres_cortos, y=real, name='Real (Días)', marker_color=colores_real, hovertext=nombres_completos, hoverinfo="text+y"))
            
            fig1.update_layout(
                barmode='group', height=320, 
                margin=dict(l=20, r=20, t=20, b=90),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(tickangle=-40, tickfont=dict(size=11)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sin datos de tiempos.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">💰 Eje Financiero (Cotizado vs Facturado)</h3>', unsafe_allow_html=True)
        if not df_finanzas.empty:
            # Gráfico de Barras Agrupadas para Finanzas
            nombres_finanzas = ['Flete Internacional' if 'flete' in str(x).lower() else ('Reconocimiento' if 'reconocimiento' in str(x).lower() else str(x)[:15]) for x in df_finanzas['INDICADOR']]
            esp_fin = df_finanzas['MEDICION ESPERADA']
            real_fin = df_finanzas['MEDICION REAL']
            
            # Colores: Verde si el gasto real es menor o igual al cotizado, Rojo si hay sobrecosto
            colores_fin_real = ['#10b981' if r <= e else '#ef4444' for r, e in zip(real_fin, esp_fin)]

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=nombres_finanzas, y=esp_fin, name='Cotizado ($)', marker_color='#3b82f6', opacity=0.8))
            fig2.add_trace(go.Bar(x=nombres_finanzas, y=real_fin, name='Facturado ($)', marker_color=colores_fin_real))
            
            fig2.update_layout(
                barmode='group', height=320, 
                margin=dict(l=20, r=20, t=20, b=50),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig2.update_yaxes(tickprefix="$", tickformat=",.0f")
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos financieros.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. DIAGNÓSTICO PROFUNDO ---
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">🎯 Distribución de Cumplimiento</h3>', unsafe_allow_html=True)
        fig3 = go.Figure(data=[go.Pie(
            labels=['Procesos que Cumplen', 'Procesos Fuera de Meta'], 
            values=[cumplen, no_cumplen],
            hole=0.6,
            marker_colors=['#10b981', '#ef4444'],
            textinfo='percent+value',
            hoverinfo='label+value'
        )])
        fig3.update_layout(
            height=280, margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc', family='Inter'),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_g4:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:0.5rem; font-weight:600;">🚨 Top Cuellos de Botella (Días de Retraso)</h3>', unsafe_allow_html=True)
        df_retrasos = df_tiempos[df_tiempos['MEDICION REAL'] > df_tiempos['MEDICION ESPERADA']].copy()
        if not df_retrasos.empty:
            df_retrasos['DESVIACION'] = df_retrasos['MEDICION REAL'] - df_retrasos['MEDICION ESPERADA']
            df_retrasos = df_retrasos.sort_values('DESVIACION', ascending=True).tail(5) 
            
            nombres_retrasos = [str(x)[:22] + '...' if len(str(x)) > 22 else str(x) for x in df_retrasos['INDICADOR']]
            
            fig4 = go.Figure(go.Bar(
                x=df_retrasos['DESVIACION'],
                y=nombres_retrasos,
                orientation='h',
                marker_color='#f97316',
                text=df_retrasos['DESVIACION'],
                textposition='auto',
                hovertext=df_retrasos['INDICADOR'], hoverinfo="text+x"
            ))
            fig4.update_layout(
                height=280, margin=dict(l=10, r=20, t=20, b=10),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8', family='Inter'),
                xaxis=dict(title='Días de retraso acumulado')
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.markdown("<p style='color:#10b981; text-align:center; padding: 4rem 0; font-size: 1.2rem; font-weight:600;'>¡Excelente! No hay retrasos operativos actualmente. 🎉</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. TABLA E INSIGHTS ---
    col_b1, col_b2 = st.columns([2.2, 1])
    
    with col_b1:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:1rem; font-weight:600;">📊 Matriz Detallada de Rendimiento</h3>', unsafe_allow_html=True)
        
        tabla_html = "<div style='overflow-x:auto;'><table class='custom-table'><thead><tr><th>Indicador</th><th>Meta</th><th>Esperado</th><th>Real</th><th>Estado</th></tr></thead><tbody>"
        for _, row in df_filtered.iterrows():
            indicador = str(row['INDICADOR'])[:45] + "..." if len(str(row['INDICADOR'])) > 45 else row['INDICADOR
