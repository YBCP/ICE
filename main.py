"""
Dashboard ICE - Archivo Principal - VERSIÓN CORREGIDA
CORRECCIÓN: Eliminación de bucles infinitos en caché y optimización de carga
"""

import streamlit as st
import pandas as pd
import os
import time
from config import (
    configure_page, apply_dark_theme, validate_google_sheets_config,
    show_setup_instructions
)
from data_utils import DataLoader, ExcelDataLoader
from tabs import TabManager

def main():
    """Función principal del dashboard - CORREGIDA"""
    
    # Configurar página
    configure_page()
    apply_dark_theme()
    
    # Inicializar session state - SIMPLIFICADO
    if 'active_tab_index' not in st.session_state:
        st.session_state.active_tab_index = 0
    if 'last_load_time' not in st.session_state:
        st.session_state.last_load_time = 0
    
    # Título principal
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #4472C4 0%, #5B9BD5 100%); 
                border-radius: 10px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin: 0;">Dashboard ICE</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Sistema de Monitoreo - Infraestructura de Conocimiento Espacial - IDECA
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar configuración de Google Sheets
    config_valid, config_message = validate_google_sheets_config()
    
    if not config_valid:
        st.error(f"❌ **Error en configuración de Google Sheets:** {config_message}")
        
        with st.expander("📋 Ver instrucciones de configuración", expanded=True):
            show_setup_instructions()
        
        st.stop()
    
    # CARGA DE DATOS SIMPLIFICADA - SIN CACHÉ PROBLEMÁTICO
    try:
        # Mostrar spinner mientras carga
        with st.spinner("🔄 Cargando datos desde Google Sheets..."):
            df, source_info, excel_data = load_data_simple()
        
        # Verificar si la carga fue exitosa
        if df is None:
            st.error("❌ Error al cargar datos desde Google Sheets")
            show_error_message()
            return
        
        # Mostrar información del sistema
        show_system_info(df, source_info)
        
        # Verificar estructura de datos
        if not verify_data_structure(df):
            return
            
        # Botón de recarga SIMPLIFICADO
        if st.button("🔄 Actualizar desde Google Sheets", help="Recarga los datos desde Google Sheets"):
            current_tab = st.session_state.get('active_tab_index', 0)
            st.session_state.last_load_time = time.time()
            st.session_state.active_tab_index = current_tab
            st.rerun()
        
        # Crear filtros simples
        filters = create_simple_filters(df)
        
        # Renderizar pestañas
        tab_manager = TabManager(df, None, excel_data)
        tab_manager.render_tabs(df, filters)
        
    except Exception as e:
        st.error(f"❌ Error crítico: {e}")
        
        # Mostrar detalles para debug
        with st.expander("🔧 Detalles del error"):
            import traceback
            st.code(traceback.format_exc())
        
        # Botón para reintentar
        if st.button("🔄 Reintentar"):
            current_tab = st.session_state.get('active_tab_index', 0)
            st.session_state.last_load_time = time.time()
            st.session_state.active_tab_index = current_tab
            st.rerun()

def load_data_simple():
    """Cargar datos SIN caché problemático"""
    try:
        # Cargar desde Google Sheets
        data_loader = DataLoader()
        df_loaded = data_loader.load_data()
        
        # Cargar datos del Excel
        excel_loader = ExcelDataLoader()
        excel_data = excel_loader.load_excel_data()
        
        # Obtener información de la fuente
        source_info = data_loader.get_data_source_info()
        
        return df_loaded, source_info, excel_data
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        # Retornar datos vacíos válidos
        empty_df = pd.DataFrame(columns=[
            'Linea_Accion', 'Componente', 'Categoria', 
            'Codigo', 'Indicador', 'Valor', 'Fecha', 'Meta', 'Peso', 'Tipo', 'Valor_Normalizado'
        ])
        return empty_df, {'source': 'Google Sheets (Error)', 'connection_info': {'connected': False}}, None

def show_system_info(df, source_info):
    """Mostrar información del sistema"""
    # Mostrar información de estado
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info(f"📊 **{len(df)}** registros")
    
    with col2:
        indicadores_unicos = df['Codigo'].nunique() if not df.empty else 0
        st.info(f"🔢 **{indicadores_unicos}** indicadores")
    
    with col3:
        if not df.empty and 'Fecha' in df.columns:
            fechas_disponibles = df['Fecha'].nunique()
            st.info(f"📅 **{fechas_disponibles}** fechas")
        else:
            st.info("📅 **0** fechas")
    
    with col4:
        # Mostrar estado de conexión
        connection_info = source_info.get('connection_info', {})
        if connection_info.get('connected', False):
            st.success("🌐 **Conectado**")
        else:
            st.error("❌ **Desconectado**")

def verify_data_structure(df):
    """Verificar estructura de datos"""
    if df.empty:
        st.info("📋 Google Sheets está vacío. Puedes agregar datos en la pestaña 'Gestión de Datos'")
        
        # Mostrar instrucciones
        with st.expander("🚀 Cómo empezar", expanded=True):
            st.markdown("""
            ### Primeros pasos:
            
            1. **Ve a la pestaña "Gestión de Datos"**
            2. **Selecciona "➕ Crear nuevo código"**
            3. **Llena la información del indicador**
            4. **Agrega registros con fechas y valores**
            5. **Los datos se guardan automáticamente en Google Sheets**
            
            ### Columnas requeridas en Google Sheets:
            - `LINEA DE ACCIÓN`
            - `COMPONENTE PROPUESTO`
            - `CATEGORÍA`
            - `COD`
            - `Nombre de indicador`
            - `Valor`
            - `Fecha`
            - `Tipo`
            """)
        return True
    
    # Verificar columnas esenciales
    required_columns = ['Codigo', 'Fecha', 'Valor', 'Componente', 'Categoria', 'Indicador']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"❌ **Error:** Faltan columnas esenciales en Google Sheets: {missing_columns}")
        st.error("**Verifica que tu Google Sheets tenga las columnas correctas**")
        st.write("**Columnas disponibles:**", list(df.columns))
        return False
    
    return True

def create_simple_filters(df):
    """Crear filtros simples"""
    st.markdown("### 📅 Fecha de Referencia")
    
    st.info("""
    ℹ️ **Nota:** Los cálculos siempre usan el **valor más reciente** de cada indicador.
    """)
    
    try:
        if df.empty or 'Fecha' not in df.columns:
            st.warning("No hay fechas disponibles en Google Sheets")
            return {'fecha': None}
            
        fechas_validas = df['Fecha'].dropna().unique()
        if len(fechas_validas) > 0:
            fechas = sorted(fechas_validas)
            fecha_seleccionada = st.selectbox(
                "Seleccionar fecha (para visualizaciones específicas)", 
                fechas, 
                index=len(fechas) - 1,
                help="Esta fecha se usa solo en algunas visualizaciones"
            )
            return {'fecha': fecha_seleccionada}
        else:
            st.warning("No se encontraron fechas válidas")
            return {'fecha': None}
    except Exception as e:
        st.warning(f"Error al procesar fechas: {e}")
        return {'fecha': None}

def show_error_message():
    """Mostrar mensaje de error"""
    st.error("""
    ### ❌ Error al cargar datos desde Google Sheets

    **Posibles causas:**
    1. **Configuración incorrecta:** Verifica `secrets.toml`
    2. **Permisos:** El Service Account debe tener acceso a la hoja
    3. **Estructura de datos:** La hoja debe tener las columnas correctas
    4. **Conectividad:** Verifica tu conexión a internet
    """)

if __name__ == "__main__":
    main()
