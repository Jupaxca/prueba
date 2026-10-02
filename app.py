import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import io
import requests

# Configuración inicial de la página web
st.set_page_config(
    page_title="Dashboard Gerencial - Aduanas",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=600) # Cacheamos por 10 minutos para no saturar la red, pero permitir actualización
def load_data_from_gsheets(url):
    try:
        # Extraemos el ID del documento de la URL
        # La URL típica es: https://docs.google.com/spreadsheets/d/ID_DEL_DOC/edit...
        if "/d/" in url:
            doc_id = url.split("/d/")[1].split("/")[0]
        else:
            st.error("URL de Google Sheets no válida.")
            return None

        # Construimos la URL de exportación a CSV
        # Usamos sheet_name='TABLERO DE CONTROL' asumiendo que es la principal, 
        # Si la pestaña tiene otro GID (ID de hoja), normalmente se exporta la primera por defecto.
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid=111977114"
        
        # Leemos el CSV directamente con pandas
        # Usamos requests para manejar mejor los errores HTTP
        response = requests.get(csv_export_url)
        response.raise_for_status() # Verifica que no haya errores 404, 403, etc.
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Limpieza de seguridad (igual que antes)
        df.columns = [str(col).strip() for col in df.columns]
        
        cumplimiento_col = next((c for c in df.columns if 'cumplimiento' in c.lower()), None)
        
        if cumplimiento_col and df[cumplimiento_col].dtype == 'object':
             df[cumplimiento_col] = df[cumplimiento_col].astype(str).str.lower().str.strip()
             df['ESTADO_LIMPIO'] = df[cumplimiento_col].apply(lambda x: 'cumple' if 'no' not in x else 'no cumple')
             
        return df
        
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: Verifique que el enlace sea público (Cualquier persona con el enlace puede leer). Detalle del error: {e}")
        return None

def main():
    # Estilos CSS
    st.markdown("""
        <style>
        .stApp { background-color: #0f172a; color: #f8fafc; }
        .css-1d391kg, .css-12oz5g7 { padding-top: 2rem; }
        h1, h2, h3 { color: #f8fafc !important; }
        div[data-testid="stMetricValue"] { font-size: 2.5rem; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚢 Command Center Operativo")
    st.markdown("Análisis Exclusivo del Tablero de Control de Indicadores (Google Sheets en Vivo)")
    st.markdown("---")

    # URL por defecto (la proporcionada)
    default_url = "https://docs.google.com/spreadsheets/d/1l5rXqFgHcUyNSQB_s82UTrHxVlpV6GHb4Yobegd-t2g/edit?usp=drivesdk"

    # Área de Carga desde URL
    with st.sidebar:
        st.header("🌐 Conexión de Datos")
        st.info("Conectado a Google Sheets. Los datos se actualizan automáticamente.")
        gsheet_url = st.text_input("URL del Tablero de Control", value=default_url)
        
        if st.button("🔄 Forzar Actualización Ahora"):
            st.cache_data.clear()
            st.rerun()

    df = None
    if gsheet_url:
        with st.spinner('Conectando a Google Sheets...'):
            df = load_data_from_gsheets(gsheet_url)
            if df is not None:
                st.sidebar.success("✅ Conexión establecida exitosamente.")
    else:
        st.info("👆 Por favor, ingresa la URL de Google Sheets en la barra lateral izquierda.")

    if df is not None and not df.empty:
        # --- LÓGICA DE ANÁLISIS APLICADA A LA HOJA DE CONTROL ---
        total_kpis = len(df)
        
        col_estado = 'ESTADO_LIMPIO' if 'ESTADO_LIMPIO' in df.columns else 'CUMPLIMIENTO'
        
        cumplen = len(df[df[col_estado] == 'cumple']) if col_estado in df.columns else 0
        no_cumplen = len(df[df[col_estado] == 'no cumple']) if col_estado in df.columns else 0
        salud = (cumplen / total_kpis) * 100 if total_kpis > 0 else 0
        
        # Extracción Financiera de la hoja
        try:
            col_ind = next(c for c in df.columns if 'indicador' in c.lower())
            flete = df[df[col_ind].astype(str).str.contains('flete', case=False, na=False)].iloc[0]
            recon = df[df[col_ind].astype(str).str.contains('Facturacion|reconocimiento', case=False, na=False)].iloc[0]
            
            col_esperada = next(c for c in df.columns if 'esperada' in c.lower())
            col_real = next(c for c in df.columns if 'real' in c.lower())
            
            fuga_costo = (float(recon[col_real]) - float(recon[col_esperada])) - (float(flete[col_esperada]) - float(flete[col_real]))
        except:
            fuga_costo = 0 
            col_ind = df.columns[0] # Fallback si no encuentra la columna indicador
            col_esperada = df.columns[2] if len(df.columns) > 2 else df.columns[0]
            col_real = df.columns[3] if len(df.columns) > 3 else df.columns[0]

        # 1. SCORECARDS
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice de Salud", f"{salud:.1f}%", f"{cumplen} de {total_kpis} metas", "normal" if salud >= 80 else "off")
        with col2:
            st.metric("Alertas Críticas", no_cumplen, "Procesos fuera de meta", "inverse")
        with col3:
            try:
                col_meta = next(c for c in df.columns if 'meta' in c.lower())
                df_dias = df[df[col_meta].astype(str).str.contains('dia|día', case=False, na=False)]
                retraso = sum(max(0, float(row[col_real]) - float(row[col_esperada])) for _, row in df_dias.iterrows() if pd.notnull(row[col_real]) and pd.notnull(row[col_esperada]))
            except:
                retraso = 0
            st.metric("Desviación Acumulada", f"+{int(retraso)} Días", "Retraso operativo", "inverse")
        with col4:
            st.metric("Impacto Financiero", f"${fuga_costo:,.0f}", "vs Cotización", "inverse" if fuga_costo > 0 else "normal")

        st.markdown("---")

        # 2. GRÁFICOS SECTORIZADOS
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Eje Tiempos (SLA)")
            try:
                df_tiempo = df[df[col_meta].astype(str).str.contains('dia|día', case=False, na=False)]
                nombres = df_tiempo[col_ind].apply(lambda x: str(x)[:25] + '...')
                
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(x=nombres, y=df_tiempo[col_esperada], name='Meta', marker_color='#3b82f6'))
                colores = ['#ef4444' if float(row[col_real]) > float(row[col_esperada]) else '#10b981' for _, row in df_tiempo.iterrows()]
                fig1.add_trace(go.Bar(x=nombres, y=df_tiempo[col_real], name='Real', marker_color=colores))
                
                fig1.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig1, use_container_width=True)
            except Exception as e:
                st.info(f"Faltan datos para el gráfico de tiempos. ({e})")

        with c2:
            st.subheader("Eje Financiero ($)")
            try:
                df_fin = df[df[col_ind].str.contains('Facturacion|flete', case=False, na=False)]
                categorias = ['Flete Intl.' if 'flete' in str(x).lower() else 'Reconocimiento' for x in df_fin[col_ind]]
                
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=categorias, y=df_fin[col_esperada], name='Cotizado', marker_color='#3b82f6'))
                colores2 = ['#ef4444' if float(row[col_real]) > float(row[col_esperada]) else '#10b981' for _, row in df_fin.iterrows()]
                fig2.add_trace(go.Bar(x=categorias, y=df_fin[col_real], name='Facturado', marker_color=colores2))
                
                fig2.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.info(f"Faltan datos para el gráfico financiero. ({e})")

        # 3. TABLA Y ANÁLISIS
        st.markdown("---")
        t1, t2 = st.columns([2, 1])
        with t1:
            st.subheader("Datos en Vivo (Google Sheets)")
            # Intentamos mostrar las columnas clave si existen, si no, mostramos todo
            try:
                cols_mostrar = [col_ind, col_esperada, col_real, col_estado]
                st.dataframe(df[cols_mostrar], use_container_width=True)
            except:
                st.dataframe(df, use_container_width=True)
            
        with t2:
            st.subheader("💡 Análisis de Desviaciones")
            if no_cumplen > 0:
                st.error(f"Se detectaron **{no_cumplen} KPIs** incumpliendo metas establecidas en el tablero de control.")
                if fuga_costo > 0:
                    st.warning(f"Las ineficiencias están impactando la facturación en aproximadamente **${fuga_costo:,.0f}** sobre lo cotizado.")
            else:
                st.success("La operación cumple con todos los parámetros del tablero de control.")
    elif df is not None and df.empty:
        st.warning("El documento de Google Sheets se conectó, pero parece estar vacío o no contiene los datos esperados.")

if __name__ == "__main__":
    main()