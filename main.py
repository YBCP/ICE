"""
Dashboard ICE - Archivo Principal
Sistema de monitoreo y seguimiento de indicadores de la Infraestructura de Conocimiento Espacial
"""

import streamlit as st
import pandas as pd
import os
from config import configure_page, apply_dark_theme, CSV_FILENAME
from data_utils import DataLoader
from tabs import TabManager

def main():
    """Función principal del dashboard"""
    
    # Configurar página
    configure_page()
    apply_dark_theme()
    
    # Título principal con estilo corporativo
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                border-radius: 10px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin: 0;">🏢 Dashboard ICE</h1>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Sistema de Monitoreo - Infraestructura de Conocimiento Espacial
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    data_loader = DataLoader()
    df = data_loader.load_data()
    
    if df is not None:
        try:
            # IMPORTANTE: No filtrar por fecha aquí - dejar que cada función maneje sus propios filtros
            # El cálculo de componentes y general siempre usa valores más recientes
            df_completo = df.copy()
            
            # Crear filtros simples (solo para referencia, no para filtrado directo)
            filters = create_simple_filters(df)
            
            # Renderizar pestañas - pasar datos completos
            tab_manager = TabManager(df_completo, data_loader.csv_path)
            tab_manager.render_tabs(df_completo, filters)
            
        except Exception as e:
            st.error(f"Error al procesar datos: {e}")
            st.info("Verifica que el archivo CSV contenga todas las columnas requeridas")
            # Mostrar traceback para debug
            import traceback
            with st.expander("Detalles del error (para desarrolladores)"):
                st.code(traceback.format_exc())
    
    else:
        show_error_message()

def create_simple_filters(df):
    """Crear selector de fecha para referencia (no afecta cálculos principales)"""
    st.markdown("### 📅 Fecha de Referencia")
    
    # Mostrar información explicativa
    st.info("""
    ℹ️ **Nota importante:** Los cálculos de componentes y puntaje general siempre usan 
    el **valor más reciente** de cada indicador. Esta fecha es solo para visualizaciones específicas.
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        try:
            # Filtrar solo fechas válidas (no NaT)
            fechas_validas = df['Fecha'].dropna().unique()
            if len(fechas_validas) > 0:
                fechas = sorted(fechas_validas)
                fecha_seleccionada = st.selectbox(
                    "Seleccionar fecha (solo para visualizaciones específicas)", 
                    fechas, 
                    index=len(fechas) - 1,
                    help="Esta fecha se usa solo en algunas visualizaciones. Los cálculos principales usan valores más recientes."
                )
                return {'fecha': fecha_seleccionada}
            else:
                st.warning("No se encontraron fechas válidas en los datos")
                return {'fecha': None}
        except Exception as e:
            st.warning(f"Error al procesar fechas: {e}")
            return {'fecha': None}

def show_error_message():
    """Mostrar mensaje de error cuando no se puede cargar el archivo"""
    st.error(f"""
    ### ❌ Error al cargar el archivo de indicadores

    No se pudo encontrar o abrir el archivo "{CSV_FILENAME}". 

    **Solución:**
    1. Asegúrate de que el archivo "{CSV_FILENAME}" existe en el mismo directorio donde estás ejecutando esta aplicación.
    2. Verifica que el nombre del archivo sea exactamente "{CSV_FILENAME}" (respetando mayúsculas y minúsculas).
    3. Comprueba que el archivo utiliza punto y coma (;) como separador de columnas.
    4. Asegúrate de que tienes permisos de lectura para el archivo.

    Si sigues teniendo problemas, intenta crear una copia del archivo CSV y guárdala con el nombre "{CSV_FILENAME}" en el mismo directorio que este script.
    """)

    # Mostrar información de diagnóstico
    try:
        current_dir = os.getcwd()
        files_in_dir = os.listdir(current_dir)
        st.info(f"""
        **Información de diagnóstico:**
        - Directorio de trabajo actual: {current_dir}
        - Archivos en el directorio actual: {', '.join(files_in_dir)}
        """)
    except Exception as e:
        st.warning(f"No se pudo obtener información del directorio: {e}")

if __name__ == "__main__":
    main()
