import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Dashboard Gerencial - Aduanas y Logística",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (UI/UX corporativo oscuro y tipografía compacta)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main, *, p, span, div, th, td {
            font-family: 'Inter', sans-serif !important;
        }
        .main {
            background-color: #0f172a;
            color: #f8fafc;
        }
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 1.25rem;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        .kpi-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 1.25rem;
            padding: 1rem;
            position: relative;
            overflow: hidden;
        }
        .insight-card-red {
            background-color: #2a161f;
            border-left: 4px solid #ef4444;
            border-radius: 0.5rem;
            padding: 0.4rem 0.6rem;
            margin-bottom: 0.4rem;
        }
        .insight-card-green {
            background-color: #132724;
            border-left: 4px solid #10b981;
            border-radius: 0.5rem;
            padding: 0.4rem 0.6rem;
            margin-bottom: 0.4rem;
        }
        .insight-title {
            color: white;
            font-size: 0.7rem;
            font-weight: 600;
            margin-bottom: 0.1rem;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }
        .insight-text {
            color: #cbd5e1;
            font-size: 0.65rem;
            line-height: 1.2;
            margin: 0;
        }
        @media print {
            .stButton {display: none;}
            .sidebar {display: none;}
        }
    </style>
""", unsafe_allow_html=True)

DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/1l5rXqFgHcUyNSQB_s82UTrHxVlpV6GHb4Yobegd-t2g/edit?usp=drivesdk"

def convertir_url_gsheets(url):
    if "spreadsheets/d/" in url:
        try:
            base_id = url.split("/spreadsheets/d/")[1].split("/")[0]
            export_url = f"https://docs.google.com/spreadsheets/d/{base_id}/export?format=csv"
            return export_url
        except Exception:
            return url
    return url

@st.cache_data(ttl=60)
def cargar_datos_gsheets(url):
    try:
        csv_url = convertir_url_gsheets(url)
        df = pd.read_csv(csv_url)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        data = [
            {"INDICADOR": "Cumplimiento de Itinerario (Transito origen - destino )", "DEFINICION OPERACIÓN": "Embarques...", "MEDIDA": "dias - %", "META": "≥ 90%", "MEDICION ESPERADA": 2, "MEDICION REAL": 2, "%": 100, "CUMPLIMIENTO": "cumple"},
            {"INDICADOR": "Tiempo de Respuesta en Cotización", "DEFINICION OPERACIÓN": "Tiempo...", "MEDIDA": "dias - %", "META": "≤ 2 dia", "MEDICION ESPERADA": 5, "MEDICION REAL": 5, "%": 100, "CUMPLIMIENTO": "cumple"},
            {"INDICADOR": "Cotizacion flete internacional Vs Facturacion del proceso", "DEFINICION OPERACIÓN": "Costo...", "MEDIDA": "%", "META": "(=) 0", "MEDICION ESPERADA": 2, "MEDICION REAL": 2, "%": 100, "CUMPLIMIENTO": "cumple"},
            {"INDICADOR": "Tiempo cierre documental", "DEFINICION OPERACIÓN": "Días...", "MEDIDA": "dias - %", "META": "≤ 3 días", "MEDICION ESPERADA": 4, "MEDICION REAL": 9, "%": 44.4, "CUMPLIMIENTO": "no cumple"},
            {"INDICADOR": "Tiempo de Disposición en Depósito", "DEFINICION OPERACIÓN": "Días...", "MEDIDA": "dias - %", "META": "≤ 4 días", "MEDICION ESPERADA": 5, "MEDICION REAL": 7, "%": 71.4, "CUMPLIMIENTO": "no cumple"},
            {"INDICADOR": "Eficiencia reconocimiento", "DEFINICION OPERACIÓN": "Cantidad...", "MEDIDA": "%", "META": "(=) 0", "MEDICION ESPERADA": 6, "MEDICION REAL": 4, "%": 100, "CUMPLIMIENTO": "cumple"},
            {"INDICADOR": "Reporte novedades e inconsistencias reconocimiento", "DEFINICION OPERACIÓN": "Tiempo...", "MEDIDA": "dias", "META": "≤ 2 dia", "MEDICION ESPERADA": 6, "MEDICION REAL": 8, "%": 75, "CUMPLIMIENTO": "no cumple"},
            {"INDICADOR": "Facturacion reconcimiento Vs cotizacion proveedor", "DEFINICION OPERACIÓN": "Costo...", "MEDIDA": "%", "META": "(=) 0", "MEDICION ESPERADA": 700, "MEDICION REAL": 800, "%": 87.5, "CUMPLIMIENTO": "no cumple"}
        ]
        return pd.DataFrame(data)

def main():
    st.sidebar.markdown("## 🔍 Filtros")
    
    with st.sidebar.expander("⚙️ Configuración de Datos", expanded=False):
        gsheet_url = st.text_input("URL de Google Sheets", value=DEFAULT_GSHEET_URL)
    
    if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
        with st.spinner("Actualizando conexión en vivo..."):
            time.sleep(0.5)
            st.cache_data.clear()
            st.rerun()

    df = cargar_datos_gsheets(gsheet_url)

    for col in ['MEDICION ESPERADA', 'MEDICION REAL']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.sidebar.markdown("---")
    estado_filtro = st.sidebar.selectbox("Estado del KPI", ["Todos", "cumple", "no cumple"])
    busqueda_texto = st.sidebar.text_input("Buscar...", placeholder="ej. Flete, Tiempo...")

    df_filtrado = df.copy()
    if estado_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['CUMPLIMIENTO'].astype(str).str.lower() == estado_filtro.lower()]
    if busqueda_texto:
        df_filtrado = df_filtrado[df_filtrado['INDICADOR'].astype(str).str.contains(busqueda_texto, case=False, na=False)]

    total_kpis = len(df)
    cumplen = len(df[df['CUMPLIMIENTO'].astype(str).str.lower() == 'cumple'])
    no_cumplen = len(df[df['CUMPLIMIENTO'].astype(str).str.lower() == 'no cumple'])
    salud_pct = (cumplen / total_kpis * 100) if total_kpis > 0 else 0

    # Lógica de estados según tus rangos solicitados
    if salud_pct <= 25:
        estado_badge = "🔴 ESTADO CRÍTICO: Acción Inmediata Requerida"
        badge_bg = "rgba(239, 68, 68, 0.2)"
        badge_color = "#f87171"
    elif salud_pct <= 50:
        estado_badge = "🟠 ESTADO MALO: Atención Urgente Requerida"
        badge_bg = "rgba(249, 115, 22, 0.2)"
        badge_color = "#fb923c"
    elif salud_pct <= 75:
        estado_badge = "🟡 ESTADO MEDIO BUENO: Requiere Ajustes Operativos"
        badge_bg = "rgba(234, 179, 8, 0.2)"
        badge_color = "#facc15"
    else:
        estado_badge = "🟢 ESTADO BUENO: Operación Óptima"
        badge_bg = "rgba(16, 185, 129, 0.2)"
        badge_color = "#34d399"

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1 style="font-size: 1.8rem; font-weight: 700; background: linear-gradient(to right, #60a5fa, #34d399); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                    🚢 Command Center Operativo
                </h1>
                <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.2rem;">Control Integral de Indicadores de Aduana y Logística</p>
            </div>
            <div>
                <span style="background: {badge_bg}; color: {badge_color}; border: 1px solid {badge_color}; padding: 0.4rem 1rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; white-space: nowrap;">
                    {estado_badge}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    retraso_dias = 0
    fuga_costos = 0
    
    for _, row in df.iterrows():
        ind_upper = str(row['INDICADOR']).upper()
        esp = row['MEDICION ESPERADA']
        real = row['MEDICION REAL']
        if "FACTURACION" in ind_upper or "FLETE" in ind_upper or "COSTO" in ind_upper:
            diff = real - esp
            if diff > 0:
                fuga_costos += diff
        else:
            if real > esp:
                retraso_dias += (real - esp)

    # Tarjetas KPI superiores
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Salud Operación</span>
            <div style="font-size: 1.8rem; font-weight: 700; color: white; margin-top: 0.3rem;">{salud_pct:.1f}%</div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.3rem;">{cumplen} de {total_kpis} logradas</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: rgba(239,68,68,0.3);">
            <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Alertas Activas</span>
            <div style="font-size: 1.8rem; font-weight: 700; color: #ef4444; margin-top: 0.3rem;">{no_cumplen}</div>
            <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 0.3rem;">Procesos fuera de meta</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Desvío Tiempos</span>
            <div style="font-size: 1.8rem; font-weight: 700; color: #f97316; margin-top: 0.3rem;">+{retraso_dias} Días</div>
            <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 0.3rem;">Retraso acumulado</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        color_costo = "#ef4444" if fuga_costos > 0 else "#10b981"
        texto_costo = f"${fuga_costos:,.0f}" if fuga_costos > 0 else "$0 (En meta)"
        st.markdown(f"""
        <div class="kpi-card">
            <span style="color: #94a3b8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Impacto Financiero</span>
            <div style="font-size: 1.8rem; font-weight: 700; color: {color_costo}; margin-top: 0.3rem;">{texto_costo}</div>
            <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 0.3rem;">Sobrecosto / Desvío</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1rem; margin-bottom:0.5rem; font-weight:600;">⏱️ Brecha de los 7 Parámetros Operativos (Esperado vs Real)</h3>', unsafe_allow_html=True)
        
        nombres_operativos = [
            "Cumplimiento de Itinerario (Transito origen - destino )",
            "Tiempo de Respuesta en Cotización",
            "Cotizacion flete internacional Vs Facturacion del proceso",
            "Tiempo cierre documental",
            "Tiempo de Disposición en Depósito",
            "Eficiencia reconocimiento",
            "Reporte novedades e inconsistencias reconocimiento"
        ]
        
        df_ops = df[df['INDICADOR'].astype(str).str.strip().isin([n.strip() for n in nombres_operativos])]
        if df_ops.empty:
            df_ops = df.head(7)

        nombres_cortos = [str(x)[:22] + '...' if len(str(x)) > 22 else str(x) for x in df_ops['INDICADOR']]

        fig1 = go.Figure()
        fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', zeroline=False)
        fig1.update_yaxes(showgrid=False, zeroline=False)

        for i in range(len(df_ops)):
            esp = df_ops['MEDICION ESPERADA'].iloc[i]
            real = df_ops['MEDICION REAL'].iloc[i]
            color_linea = '#ef4444' if real > esp else 'rgba(148, 163, 184, 0.2)'
            fig1.add_trace(go.Scatter(
                x=[esp, real], y=[nombres_cortos[i], nombres_cortos[i]],
                mode='lines', line=dict(color=color_linea, width=2.5),
                showlegend=False, hoverinfo='skip'
            ))
        
        fig1.add_trace(go.Scatter(
            x=df_ops['MEDICION ESPERADA'], y=nombres_cortos,
            mode='markers', name='Esperado',
            marker=dict(color='#3b82f6', size=8, symbol='square'),
            hovertext=df_ops['INDICADOR'], hoverinfo='text+x'
        ))
        
        colores_real = ['#ef4444' if r > e else '#10b981' for r, e in zip(df_ops['MEDICION REAL'], df_ops['MEDICION ESPERADA'])]
        fig1.add_trace(go.Scatter(
            x=df_ops['MEDICION REAL'], y=nombres_cortos,
            mode='markers', name='Real',
            marker=dict(color=colores_real, size=8, symbol='circle'),
            hovertext=df_ops['INDICADOR'], hoverinfo='text+x'
        ))
        
        fig1.update_layout(
            height=320, margin=dict(l=10, r=20, t=10, b=20),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8', family='Inter', size=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=10))
        )
        fig1.update_yaxes(autorange="reversed")
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1rem; margin-bottom:0.5rem; font-weight:600;">🎯 Distribución General</h3>', unsafe_allow_html=True)
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Cumplen', 'Fuera de Meta'],
            values=[cumplen, no_cumplen],
            hole=.6,
            marker=dict(colors=['#10b981', '#ef4444']),
            textinfo='label+percent',
            textfont=dict(color='white', size=11)
        )])
        fig_donut.update_layout(
            height=320, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1.5, 1])

    with col_t1:
        st.markdown('<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:1rem; font-weight:600;">📋 Matriz de Rendimiento de Procesos</h3>', unsafe_allow_html=True)
        
        # Uso seguro de dataframe de Streamlit para evitar escape de HTML en crudo
        df_display = df_filtrado[['INDICADOR', 'META', 'MEDICION ESPERADA', 'MEDICION REAL', 'CUMPLIMIENTO']].copy()
        df_display.columns = ['Indicador', 'Meta', 'Esperado', 'Real', 'Estado']
        
        def color_estado(val):
            color = '#34d399' if str(val).lower() == 'cumple' else '#f87171'
            return f'color: {color}; font-weight: bold;'
            
        st.dataframe(
            df_display.style.applymap(color_estado, subset=['Estado']),
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_t2:
        st.markdown(f'<div class="glass-card"><h3 class="text-white" style="font-size:1.1rem; margin-bottom:1rem; font-weight:600;">💡 Diagnóstico Detallado ({len(df_filtrado)} Apartados)</h3>', unsafe_allow_html=True)
        
        for _, row in df_filtrado.iterrows():
            ind = str(row['INDICADOR'])
            esp = row['MEDICION ESPERADA']
            real = row['MEDICION REAL']
            estado = str(row['CUMPLIMIENTO']).lower()
            
            ind_upper = ind.upper()
            es_financiero = "FACTURACION" in ind_upper or "FLETE" in ind_upper or "COSTO" in ind_upper

            if estado == 'cumple':
                card_class = "insight-card-green"
                icon = "🟢"
                if es_financiero:
                    msg = f"Se cumple al 100% en control financiero (Esperado: ${esp:,.0f}, Real: ${real:,.0f}). Sin desvíos."
                else:
                    msg = f"Se cumple al 100% en el indicador (Esperado: {esp}, Real: {real}). Operación eficiente."
            else:
                card_class = "insight-card-red"
                icon = "🔴"
                if es_financiero:
                    pct_sobrecosto = ((real - esp) / esp * 100) if esp > 0 else 100
                    msg = f"Presenta sobrecosto monetario un {pct_sobrecosto:.0f}% de lo esperado (Esp: ${esp:,.0f}, Real:${real:,.0f})."
                else:
                    pct_demora = ((real - esp) / esp * 100) if esp > 0 else 100
                    msg = f"Presenta retraso o demora un {pct_demora:.0f}% de lo esperado (Esp: {esp}, Real: {real})."

            st.markdown(f"""
            <div class="{card_class}">
                <div class="insight-title">
                    <span>{icon}</span> {ind}
                </div>
                <p class="insight-text">{msg}</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
