```python
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

# 2. Inyección de CSS Premium (Simulando el diseño web original)
st.markdown("""
    <style>
        /* Fondo oscuro y tipografía */
        .stApp {
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Inter', sans-serif;
        }
        
        /* Ocultar elementos predeterminados molestos de Streamlit */
        header {visibility: hidden;}
        .css-15zrgzn {display: none;}
        
        /* Estilos para las tarjetas (Cards) */
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        
        /* Textos destacados */
        .metric-title {
            color: #94a3b8;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-value {
            font-size: 2.25rem;
            font-weight: 700;
            margin-top: 0.5rem;
        }
        .text-green { color: #10b981; }
        .text-red { color: #ef4444; }
        .text-blue { color: #3b82f6; }
        .text-orange { color: #f97316; }
        .text-white { color: #ffffff; }
        
        /* Tabla personalizada */
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            color: #e2e8f0;
        }
        .custom-table th {
            background-color: rgba(30, 41, 59, 0.9);
            color: #94a3b8;
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #334155;
        }
        .custom-table td {
            padding: 1rem;
            border-bottom: 1px solid #1e293b;
        }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-weight: bold; font-size: 0.75rem; }
        .badge-red { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-weight: bold; font-size: 0.75rem; }
    </style>
""", unsafe_allow_html=True)

# 3. Función de conexión a datos
@st.cache_data(ttl=300) # Cache por 5 minutos
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
        
        # Limpieza de estados
        if 'CUMPLIMIENTO' in df.columns:
            df['CUMPLIMIENTO'] = df['CUMPLIMIENTO'].astype(str).str.lower().str.strip()
            
        # Asegurar tipos numéricos para las métricas
        for col in ['MEDICION ESPERADA', 'MEDICION REAL']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df, None
    except Exception as e:
        return None, str(e)

def main():
    # --- HEADER / TÍTULO ---
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown('<h1 style="color: #60a5fa; font-weight: 700; margin-bottom: 0;">🚢 Command Center Operativo</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #94a3b8; font-size: 0.9rem;">Control de Indicadores de Aduana y Logística - Corte Actual</p>', unsafe_allow_html=True)
    with col_t2:
        st.markdown('<div style="text-align: right; padding-top: 1rem;"><span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.5rem 1rem; border-radius: 9999px; font-weight: 600; font-size: 0.8rem;">⚠️ Estado: Atención Requerida</span></div>', unsafe_allow_html=True)
    st.markdown("---")

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown('<h2 style="color:white;">🔎 Filtros</h2>', unsafe_allow_html=True)
        
        # Variables de estado y datos por defecto
        df = None
        default_url = "https://docs.google.com/spreadsheets/d/1l5rXqFgHcUyNSQB_s82UTrHxVlpV6GHb4Yobegd-t2g/edit?usp=drivesdk"
        
        # Ocultamos la configuración técnica en un expander
        with st.expander("⚙️ Configuración de Datos", expanded=False):
            gsheet_url = st.text_input("URL de Google Sheets", value=default_url)
            if st.button("🔄 Forzar Actualización"):
                st.cache_data.clear()
                st.rerun()
        
        # Cargar datos
        if gsheet_url:
            df, error = load_data(gsheet_url)
            if error:
                st.error(f"Error: {error}")
                return
        
        # Filtros Dinámicos
        if df is not None and not df.empty:
            estados = ['Todos'] + list(df['CUMPLIMIENTO'].dropna().unique())
            filtro_estado = st.selectbox("Estado del KPI", estados, index=0)
            filtro_texto = st.text_input("Buscar (ej. Flete)...", "")
            
            # Aplicar filtros
            df_filtered = df.copy()
            if filtro_estado != 'Todos':
                df_filtered = df_filtered[df_filtered['CUMPLIMIENTO'] == filtro_estado]
            if filtro_texto:
                df_filtered = df_filtered[df_filtered['INDICADOR'].str.contains(filtro_texto, case=False, na=False)]
    
    if df_filtered is None or df_filtered.empty:
        st.warning("No hay datos para mostrar con los filtros actuales.")
        return

    # --- MOTOR ANALÍTICO (Cálculo de KPIs desde el Excel) ---
    total_kpis = len(df_filtered)
    cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'cumple'])
    no_cumplen = len(df_filtered[df_filtered['CUMPLIMIENTO'] == 'no cumple'])
    salud_pct = (cumplen / total_kpis * 100) if total_kpis > 0 else 0

    # Retraso en tiempo (Solo filas que contengan 'dias' en la medida)
    df_tiempos = df_filtered[df_filtered['MEDIDA'].str.contains('dia|día', case=False, na=False)]
    retraso_dias = 0
    for _, row in df_tiempos.iterrows():
        desviacion = row['MEDICION REAL'] - row['MEDICION ESPERADA']
        if desviacion > 0:
            retraso_dias += desviacion

    # Fuga de Costos (Lógica específica para facturación)
    fuga_costos = 0
    df_finanzas = df_filtered[df_filtered['INDICADOR'].str.contains('Facturacion|flete', case=False, na=False)]
    
    # Costo reconocimiento (Si real > esperado = Pérdida)
    rec_esperado = df_finanzas[df_finanzas['INDICADOR'].str.contains('reconcimiento|reconocimiento', case=False, na=False)]['MEDICION ESPERADA'].sum()
    rec_real = df_finanzas[df_finanzas['INDICADOR'].str.contains('reconcimiento|reconocimiento', case=False, na=False)]['MEDICION REAL'].sum()
    fuga_costos += (rec_real - rec_esperado)
    
    # Flete (Si real < esperado = Ahorro / Si real > esperado = Pérdida)
    flete_esperado = df_finanzas[df_finanzas['INDICADOR'].str.contains('flete', case=False, na=False)]['MEDICION ESPERADA'].sum()
    flete_real = df_finanzas[df_finanzas['INDICADOR'].str.contains('flete', case=False, na=False)]['MEDICION REAL'].sum()
    fuga_costos -= (flete_esperado - flete_real) # Restamos porque un flete real menor es un ahorro (positivo para nosotros)

    # --- 1. SECCIÓN DE SCORECARDS ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        color_salud = "text-red" if salud_pct < 50 else ("text-orange" if salud_pct < 80 else "text-green")
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Salud de la Operación</div>
                <div class="metric-value {color_salud}">{salud_pct:.1f}%</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">{cumplen} de {total_kpis} metas logradas</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
            <div class="glass-card" style="border-color: rgba(239, 68, 68, 0.3);">
                <div class="metric-title">Alertas Activas</div>
                <div class="metric-value text-red">{no_cumplen}</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">Procesos fuera de meta</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Desviación en Tiempos</div>
                <div class="metric-value text-orange">+{int(retraso_dias)} Días</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">Retraso operativo acumulado</div>
            </div>
        """, unsafe_allow_html=True)
        
    with c4:
        signo = "+" if fuga_costos > 0 else ""
        color_fuga = "text-red" if fuga_costos > 0 else "text-green"
        texto_fuga = "Sobrecosto" if fuga_costos > 0 else "Ahorro"
        st.markdown(f"""
            <div class="glass-card">
                <div class="metric-title">Impacto Financiero (Desviación)</div>
                <div class="metric-value {color_fuga}">{signo}${abs(fuga_costos):,.0f}</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:0.5rem;">{texto_fuga} vs Cotización</div>
            </div>
        """, unsafe_allow_html=True)

    # --- 2. SECCIÓN DE GRÁFICOS (PLOTLY AVANZADO) ---
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:1rem;">⏱️ Eje Tiempos (SLA)</h3>', unsafe_allow_html=True)
        if not df_tiempos.empty:
            nombres_cortos = [str(x)[:20] + '...' for x in df_tiempos['INDICADOR']]
            esperado = df_tiempos['MEDICION ESPERADA']
            real = df_tiempos['MEDICION REAL']
            
            # Lógica de colores (verde si cumple, rojo si se pasa)
            colores_real = ['#10b981' if r <= e else '#ef4444' for r, e in zip(real, esperado)]
            
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=nombres_cortos, y=esperado, name='Meta (Días)', marker_color='#3b82f6', opacity=0.8))
            fig1.add_trace(go.Bar(x=nombres_cortos, y=real, name='Real (Días)', marker_color=colores_real))
            
            fig1.update_layout(
                barmode='group', height=300, margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sin datos de tiempos.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:1rem;">💰 Eje Financiero</h3>', unsafe_allow_html=True)
        if not df_finanzas.empty:
            nombres = ['Flete Intl.' if 'flete' in str(x).lower() else 'Reconocimiento' for x in df_finanzas['INDICADOR']]
            esperado = df_finanzas['MEDICION ESPERADA']
            real = df_finanzas['MEDICION REAL']
            
            # Lógica de colores: Para flete, rojo si es mayor. Para reconocimiento, rojo si es mayor.
            colores_real2 = ['#ef4444' if r > e else '#10b981' for r, e in zip(real, esperado)]
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=nombres, y=esperado, name='Cotizado ($)', marker_color='#3b82f6', opacity=0.8))
            fig2.add_trace(go.Bar(x=nombres, y=real, name='Facturado ($)', marker_color=colores_real2))
            
            fig2.update_layout(
                barmode='group', height=300, margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin datos financieros.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. SECCIÓN INFERIOR: TABLA E INSIGHTS ---
    col_b1, col_b2 = st.columns([2, 1])
    
    with col_b1:
        st.markdown('<div class="glass-card"><h3 style="color:white; font-size:1.1rem; margin-bottom:1rem;">📊 Matriz de Rendimiento de Procesos</h3>', unsafe_allow_html=True)
        
        # Generar tabla HTML personalizada basada en los datos
        tabla_html = "<table class='custom-table'><thead><tr><th>Indicador</th><th>Meta</th><th>Esperado</th><th>Real</th><th>Estado</th></tr></thead><tbody>"
        for _, row in df_filtered.iterrows():
            indicador = str(row['INDICADOR'])[:40] + "..." if len(str(row['INDICADOR'])) > 40 else row['INDICADOR']
            meta = row['META'] if 'META' in df_filtered.columns else '-'
            esp = row['MEDICION ESPERADA']
            real = row['MEDICION REAL']
            estado = row['CUMPLIMIENTO']
            
            badge = f"<span class='badge-green'>CUMPLE</span>" if estado == 'cumple' else f"<span class='badge-red'>NO CUMPLE</span>"
            color_row = "color: #ef4444; font-weight:bold;" if estado == 'no cumple' else "color: #10b981; font-weight:bold;"
            
            tabla_html += f"<tr><td>{indicador}</td><td>{meta}</td><td>{esp}</td><td style='{color_row}'>{real}</td><td>{badge}</td></tr>"
        
        tabla_html += "</tbody></table>"
        st.markdown(tabla_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_b2:
        st.markdown('<div class="glass-card" style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9)); border-color: rgba(59, 130, 246, 0.3);"><h3 style="color:white; font-size:1.1rem; margin-bottom:1rem;">💡 Insights y Plan de Acción</h3>', unsafe_allow_html=True)
        
        # Motor Dinámico de Insights
        if no_cumplen > 0:
            peor_desfase_tiempo = df_tiempos[df_tiempos['CUMPLIMIENTO'] == 'no cumple'].sort_values(by='MEDICION REAL', ascending=False).head(1)
            
            if not peor_desfase_tiempo.empty:
                nombre_peor = peor_desfase_tiempo.iloc[0]['INDICADOR']
                real_peor = peor_desfase_tiempo.iloc[0]['MEDICION REAL']
                esp_peor = peor_desfase_tiempo.iloc[0]['MEDICION ESPERADA']
                pct_retraso = ((real_peor - esp_peor) / esp_peor) * 100
                
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ef4444; margin-bottom: 1rem;">
                    <h4 style="color: white; margin: 0 0 0.5rem 0; font-size: 0.9rem;">🔴 Cuello de Botella</h4>
                    <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">El indicador <strong>"{nombre_peor}"</strong> está tardando un {pct_retraso:.0f}% más de lo esperado ({real_peor} vs {esp_peor} días).</p>
                </div>
                """, unsafe_allow_html=True)
                
            if fuga_costos > 0:
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f97316; margin-bottom: 1rem;">
                    <h4 style="color: white; margin: 0 0 0.5rem 0; font-size: 0.9rem;">🟠 Alerta Financiera</h4>
                    <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">Las ineficiencias operativas están generando un sobrecosto total de <strong>${fuga_costos:,.0f}</strong> en facturación frente a la cotización base.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
             st.markdown("""
                <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #10b981; margin-bottom: 1rem;">
                    <h4 style="color: white; margin: 0 0 0.5rem 0; font-size: 0.9rem;">🟢 Operación Saludable</h4>
                    <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">Todos los indicadores seleccionados están cumpliendo sus metas. Buen control operativo.</p>
                </div>
                """, unsafe_allow_html=True)

        if flete_esperado > flete_real and 'cumple' in df_filtered['CUMPLIMIENTO'].values:
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #3b82f6; margin-bottom: 1rem;">
                <h4 style="color: white; margin: 0 0 0.5rem 0; font-size: 0.9rem;">🔵 Punto Fuerte</h4>
                <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">Buena gestión en Fletes Internacionales, generando un ahorro de ${flete_esperado - flete_real:,.0f} vs cotización.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('<button style="width: 100%; padding: 0.75rem; background-color: #334155; color: white; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: 600; margin-top: 1rem;">Agendar Comité de Revisión 📅</button>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
```
