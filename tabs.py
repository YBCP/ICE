"""
Interfaces de usuario para las pestañas del Dashboard ICE - SOLO GOOGLE SHEETS
VERSIÓN CORREGIDA: Persistencia completa de pestañas en todas las operaciones
"""

import streamlit as st
import pandas as pd
import time
from charts import ChartGenerator, MetricsDisplay
from data_utils import DataProcessor, DataEditor
from filters import EvolutionFilters
from datetime import datetime

class GeneralSummaryTab:
    """Pestaña de resumen general"""
    
    @staticmethod
    def render(df, fecha_seleccionada):
        """Renderizar la pestaña de resumen general"""
        st.header("📊 Resumen General")
        
        try:
            # Verificación previa de datos
            if df.empty:
                st.info("📋 Google Sheets está vacío. Puedes agregar datos en la pestaña 'Gestión de Datos'")
                st.markdown("""
                ### 🚀 Primeros pasos:
                1. Ve a la pestaña **"Gestión de Datos"**
                2. Selecciona un código de indicador (o crea uno nuevo)
                3. Agrega algunos registros con valores y fechas
                4. Los datos se guardarán automáticamente en Google Sheets
                5. Regresa aquí para ver los análisis
                """)
                return
                
            required_cols = ['Codigo', 'Fecha', 'Valor', 'Componente', 'Categoria']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                st.error(f"❌ Faltan columnas esenciales en Google Sheets: {missing_cols}")
                st.write("**Columnas disponibles:**", list(df.columns))
                return
            
            # Verificar que hay datos válidos
            datos_validos = df.dropna(subset=['Codigo', 'Fecha', 'Valor'])
            if datos_validos.empty:
                st.info("📋 Los datos en Google Sheets están vacíos o incompletos")
                return
            
            # Calcular puntajes
            puntajes_componente, puntajes_categoria, puntaje_general = DataProcessor.calculate_scores(df)
            
            # Verificar que los cálculos fueron exitosos
            if puntajes_componente.empty and puntajes_categoria.empty and puntaje_general == 0:
                st.info("📊 Agregando más datos podrás ver los puntajes y análisis")
                return
            
            # Mostrar información sobre qué datos se están usando
            st.info("""
            📊 **Cálculos basados en valores más recientes desde Google Sheets:** Los puntajes se calculan 
            usando el valor más reciente de cada indicador, asegurando consistencia.
            """)
            
            # Mostrar métricas generales
            MetricsDisplay.show_general_metrics(puntaje_general, puntajes_componente)
            
            # Crear layout con velocímetro y radar
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Gráfico de velocímetro
                try:
                    st.plotly_chart(
                        ChartGenerator.gauge_chart(puntaje_general), 
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error en velocímetro: {e}")
            
            with col2:
                # Gráfico de radar
                try:
                    st.plotly_chart(
                        ChartGenerator.radar_chart(df, None),
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error en gráfico radar: {e}")
            
            # Puntajes por componente
            st.subheader("📈 Puntajes por Componente")
            if not puntajes_componente.empty:
                try:
                    fig_comp = ChartGenerator.component_bar_chart(puntajes_componente)
                    st.plotly_chart(fig_comp, use_container_width=True)
                except Exception as e:
                    st.error(f"Error en gráfico de componentes: {e}")
                    st.dataframe(puntajes_componente, use_container_width=True)
            else:
                st.info("Agrega más datos a Google Sheets para ver puntajes por componente")
        
        except Exception as e:
            st.error(f"❌ Error al calcular puntajes desde Google Sheets: {e}")
            import traceback
            with st.expander("🔧 Detalles del error"):
                st.code(traceback.format_exc())
        
        # Mostrar tabla de datos más recientes
        with st.expander("📋 Ver datos más recientes por indicador (desde Google Sheets)"):
            try:
                df_latest = DataProcessor._get_latest_values_by_indicator(df)
                if not df_latest.empty:
                    st.dataframe(
                        df_latest[['Codigo', 'Indicador', 'Componente', 'Categoria', 'Valor', 'Fecha']], 
                        use_container_width=True
                    )
                else:
                    st.info("No hay datos para mostrar")
            except Exception as e:
                st.error(f"Error al mostrar datos: {e}")

class ComponentSummaryTab:
    """Pestaña de resumen por componente"""
    
    @staticmethod
    def render(df, filters):
        """Renderizar la pestaña de resumen por componente"""
        st.header("🏗️ Resumen por Componente")
        
        if df.empty:
            st.info("📋 No hay datos disponibles en Google Sheets para análisis por componente")
            return
        
        # Selector de componente específico para esta vista
        componentes = sorted(df['Componente'].unique())
        if not componentes:
            st.info("📋 No hay componentes disponibles en Google Sheets")
            return
            
        componente_analisis = st.selectbox(
            "Seleccionar componente para análisis detallado", 
            componentes,
            key="comp_analysis"
        )
        
        # Obtener valores más recientes y filtrar por componente
        df_latest = DataProcessor._get_latest_values_by_indicator(df)
        df_componente = df_latest[df_latest['Componente'] == componente_analisis]
        
        if not df_componente.empty:
            # Información sobre los datos que se están usando
            st.info(f"""
            📊 **Análisis de {componente_analisis}:** Basado en los valores más recientes 
            de cada indicador de este componente desde Google Sheets.
            """)
            
            # Métricas del componente
            col1, col2, col3 = st.columns(3)
            
            with col1:
                valor_promedio = df_componente['Valor'].mean()
                st.metric("Valor Promedio", f"{valor_promedio:.3f}")
            
            with col2:
                total_indicadores = df_componente['Indicador'].nunique()
                st.metric("Total Indicadores", total_indicadores)
            
            with col3:
                ultima_medicion = df_componente['Fecha'].max()
                if pd.notna(ultima_medicion):
                    try:
                        fecha_str = pd.to_datetime(ultima_medicion).strftime('%d/%m/%Y')
                        st.metric("Última Medición", fecha_str)
                    except:
                        st.metric("Última Medición", "No disponible")
                else:
                    st.metric("Última Medición", "No disponible")
            
            # Tabla de categorías
            try:
                ChartGenerator.show_category_table_simple(df, componente_analisis)
            except Exception as e:
                st.error(f"Error al mostrar categorías: {e}")
            
            # Layout con gráficos lado a lado
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                # Gráfico de evolución del componente
                df_componente_historico = df[df['Componente'] == componente_analisis]
                fig_evol = ChartGenerator.evolution_chart(df_componente_historico, componente=componente_analisis)
                st.plotly_chart(fig_evol, use_container_width=True)
            
            with col_der:
                # Gráfico de radar por categorías
                fig_radar_cat = ChartGenerator.radar_chart_categories(
                    df, componente_analisis, None
                )
                st.plotly_chart(fig_radar_cat, use_container_width=True)
            
            # Tabla de indicadores del componente
            st.subheader(f"📊 Indicadores Más Recientes de {componente_analisis}")
            st.dataframe(
                df_componente[['Indicador', 'Categoria', 'Valor', 'Fecha']].sort_values('Valor', ascending=False),
                use_container_width=True
            )
        else:
            st.warning("No hay datos para el componente seleccionado en Google Sheets")

class EvolutionTab:
    """Pestaña de evolución"""
    
    @staticmethod
    def render(df, filters):
        """Renderizar la pestaña de evolución"""
        st.header("📈 Evolución Temporal de Indicadores")
        
        try:
            if df.empty:
                st.info("📋 No hay datos disponibles en Google Sheets para mostrar evolución")
                return
            
            # Información sobre los datos disponibles
            st.info(f"""
            📊 **Datos desde Google Sheets:** {len(df)} registros de {df['Codigo'].nunique()} indicadores únicos
            📅 **Rango de fechas:** {df['Fecha'].min().strftime('%d/%m/%Y')} - {df['Fecha'].max().strftime('%d/%m/%Y')}
            """)
            
            # Crear filtros específicos de evolución
            evolution_filters = EvolutionFilters.create_evolution_filters(df)
            
            # Mostrar información del filtro seleccionado
            if evolution_filters['indicador']:
                st.success(f"**📊 Indicador seleccionado:** {evolution_filters['indicador']}")
                
                # Mostrar datos específicos del indicador
                datos_indicador = df[df['Codigo'] == evolution_filters['codigo']].sort_values('Fecha')
                
                if not datos_indicador.empty:
                    st.write(f"**Registros históricos encontrados:** {len(datos_indicador)}")
                    
                    # Mostrar tabla de datos del indicador
                    with st.expander("📋 Ver datos históricos del indicador"):
                        st.dataframe(
                            datos_indicador[['Fecha', 'Valor', 'Componente', 'Categoria']], 
                            use_container_width=True
                        )
                else:
                    st.warning("No se encontraron datos históricos para este indicador en Google Sheets")
                    return
            else:
                st.info("**📊 Vista general:** Mostrando evolución promedio de todos los indicadores")
            
            # Generar gráfico de evolución
            try:
                fig = ChartGenerator.evolution_chart(
                    df,
                    indicador=evolution_filters['indicador'],
                    componente=None,
                    tipo_grafico=evolution_filters['tipo_grafico'],
                    mostrar_meta=evolution_filters['mostrar_meta']
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error al generar gráfico: {e}")
                import traceback
                with st.expander("Detalles del error"):
                    st.code(traceback.format_exc())
            
            # Mostrar análisis adicional si hay un indicador seleccionado
            if evolution_filters['codigo'] and evolution_filters['indicador']:
                st.subheader(f"📊 Análisis Detallado: {evolution_filters['indicador']}")
                
                datos_indicador = df[df['Codigo'] == evolution_filters['codigo']].sort_values('Fecha')
                
                if len(datos_indicador) > 1:
                    # Métricas de evolución
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        valor_inicial = datos_indicador.iloc[0]['Valor']
                        st.metric("Valor Inicial", f"{valor_inicial:.3f}")
                    
                    with col2:
                        valor_actual = datos_indicador.iloc[-1]['Valor']
                        st.metric("Valor Actual", f"{valor_actual:.3f}")
                    
                    with col3:
                        cambio = valor_actual - valor_inicial
                        st.metric("Cambio Total", f"{cambio:+.3f}")
                    
                    with col4:
                        if valor_inicial != 0:
                            cambio_pct = (cambio / valor_inicial) * 100
                            st.metric("Cambio %", f"{cambio_pct:+.1f}%")
                        else:
                            st.metric("Cambio %", "N/A")
                
                # Tabla de datos históricos
                st.dataframe(
                    datos_indicador[['Fecha', 'Valor', 'Componente', 'Categoria']], 
                    use_container_width=True
                )
        
        except Exception as e:
            st.error(f"Error crítico en pestaña de evolución: {e}")
            import traceback
            with st.expander("🔧 Debug: Detalles del error"):
                st.code(traceback.format_exc())

class EditTab:
    """Pestaña de edición - SOLO GOOGLE SHEETS CON PDF CORREGIDO"""
    
    @staticmethod
    def render(df, csv_path, excel_data=None):
        """Renderizar la pestaña de edición con Google Sheets"""
        st.header("⚙️ Gestión de Indicadores")
        st.caption("📊 Conectado a Google Sheets")
        
        try:
            # Verificar que Google Sheets esté disponible
            from data_utils import GOOGLE_SHEETS_AVAILABLE
            if not GOOGLE_SHEETS_AVAILABLE:
                st.error("❌ **Google Sheets no disponible.** Instala las dependencias: `pip install gspread google-auth`")
                return
            
            # Inicializar session state para preservar selecciones
            if 'selected_codigo' not in st.session_state:
                st.session_state.selected_codigo = None
            
            # Obtener códigos disponibles
            if df.empty:
                st.info("📋 Google Sheets está vacío. Puedes crear un nuevo indicador.")
                codigos_disponibles = []
            else:
                codigos_disponibles = sorted(df['Codigo'].dropna().unique())
            
            # Agregar opción para crear nuevo código
            opciones_codigo = ["➕ Crear nuevo código"] + list(codigos_disponibles)
            
            # Seleccionar código (mantener selección si es posible)
            index_actual = 0
            if st.session_state.selected_codigo and st.session_state.selected_codigo in codigos_disponibles:
                try:
                    index_actual = opciones_codigo.index(st.session_state.selected_codigo)
                except ValueError:
                    index_actual = 0
            
            codigo_editar = st.selectbox(
                "Seleccionar Código de Indicador", 
                opciones_codigo,
                index=index_actual,
                key="codigo_editar",
                help="Los datos se guardan automáticamente en Google Sheets"
            )
            
            # Actualizar session state
            if codigo_editar != "➕ Crear nuevo código":
                st.session_state.selected_codigo = codigo_editar
            
            # Manejar creación de nuevo código
            if codigo_editar == "➕ Crear nuevo código":
                EditTab._render_new_indicator_form(df)
                return
            
            # Validar que el código seleccionado existe en los datos
            datos_indicador = df[df['Codigo'] == codigo_editar] if not df.empty else pd.DataFrame()
            
            if datos_indicador.empty and not df.empty:
                st.error(f"No se encontraron datos para el código {codigo_editar} en Google Sheets")
                return
            elif not df.empty:
                # Mostrar información del indicador
                try:
                    nombre_indicador = datos_indicador['Indicador'].iloc[0]
                    componente_indicador = datos_indicador['Componente'].iloc[0]
                    categoria_indicador = datos_indicador['Categoria'].iloc[0]
                    
                    # Card con información del indicador
                    st.markdown(f"""
                    <div style="background: linear-gradient(45deg, #4472C4 0%, #5B9BD5 100%); 
                               padding: 1rem; border-radius: 10px; margin: 1rem 0; color: white;">
                        <h4 style="color: white; margin: 0;">📊 {nombre_indicador}</h4>
                        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                            <strong>Componente:</strong> {componente_indicador}<br>
                            <strong>Categoría:</strong> {categoria_indicador}<br>
                            <strong>Código:</strong> {codigo_editar}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except IndexError:
                    st.error(f"Error al obtener información del indicador {codigo_editar}")
                    return
            
            # Botones para funcionalidades metodológicas (CORRECCIÓN APLICADA)
            EditTab._render_metodological_section(codigo_editar, excel_data)
            
            # Obtener registros existentes del indicador
            if not df.empty and not datos_indicador.empty:
                registros_indicador = datos_indicador.sort_values('Fecha', ascending=False)
            else:
                registros_indicador = pd.DataFrame()
            
            # Crear pestañas para diferentes acciones
            tab_ver, tab_agregar, tab_editar, tab_eliminar = st.tabs([
                "📋 Ver Registros", 
                "➕ Agregar Nuevo", 
                "✏️ Editar Existente", 
                "🗑️ Eliminar Registro"
            ])
            
            with tab_ver:
                EditTab._render_view_records(registros_indicador)
            
            with tab_agregar:
                EditTab._render_add_form(df, codigo_editar)
            
            with tab_editar:
                EditTab._render_edit_form(df, codigo_editar, registros_indicador)
            
            with tab_eliminar:
                EditTab._render_delete_form(df, codigo_editar, registros_indicador)
        
        except Exception as e:
            st.error(f"Error en la gestión de indicadores: {e}")
            import traceback
            with st.expander("🔧 Detalles del error"):
                st.code(traceback.format_exc())
    
    @staticmethod
    def _render_metodological_section(codigo_editar, excel_data):
        """Renderizar sección de información metodológica"""
        st.subheader("📋 Información Metodológica")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            if st.button("📋 Ver Ficha", key=f"view_sheet_{codigo_editar}", use_container_width=True):
                st.session_state.show_ficha = True
        
        with col3:
            # Verificar disponibilidad de PDF
            try:
                import reportlab
                reportlab_available = True
            except ImportError:
                reportlab_available = False
            
            if reportlab_available and excel_data is not None and not excel_data.empty:
                codigo_existe = codigo_editar in excel_data['Codigo'].values
                
                if codigo_existe:
                    if st.button("📄 Generar PDF", key=f"generate_pdf_{codigo_editar}", use_container_width=True):
                        EditTab._generate_and_download_pdf(codigo_editar, excel_data)
                else:
                    st.button("❌ PDF (Sin datos)", key=f"pdf_no_data_{codigo_editar}", disabled=True, use_container_width=True)
                    st.warning(f"No hay datos metodológicos para {codigo_editar}")
                        
            elif not reportlab_available:
                st.button("❌ Instalar reportlab", key=f"pdf_disabled_{codigo_editar}", disabled=True, use_container_width=True)
                st.error("📦 `pip install reportlab`")
            else:
                st.button("❌ Falta archivo Excel", key=f"pdf_no_excel_{codigo_editar}", disabled=True, use_container_width=True)
                st.warning("📄 Necesitas 'Batería de indicadores.xlsx'")
        
        # Información de estado de funcionalidades
        with st.expander("ℹ️ Estado de funcionalidades metodológicas", expanded=False):
            # Verificar reportlab
            try:
                import reportlab
                st.success("✅ reportlab: Disponible")
            except ImportError:
                st.error("❌ reportlab: No instalado - `pip install reportlab`")
            
            # Verificar archivo Excel
            if excel_data is not None and not excel_data.empty:
                st.success("✅ Archivo Excel: Cargado correctamente")
                st.info(f"📄 Total de indicadores metodológicos: {len(excel_data)}")
                
                if codigo_editar in excel_data['Codigo'].values:
                    st.success(f"✅ Código {codigo_editar}: Encontrado en Excel")
                else:
                    st.warning(f"⚠️ Código {codigo_editar}: No encontrado en Excel")
                    codigos_disponibles = excel_data['Codigo'].dropna().unique()[:5]
                    if len(codigos_disponibles) > 0:
                        st.info(f"💡 Códigos disponibles: {', '.join(map(str, codigos_disponibles))}")
            else:
                st.warning("⚠️ Archivo Excel: No disponible")
                st.info("📄 Coloca 'Batería de indicadores.xlsx' en el directorio del proyecto")
        
        # Mostrar ficha si se solicitó
        if st.session_state.get('show_ficha', False):
            EditTab._show_metodological_info_display(codigo_editar, excel_data)
    
    @staticmethod
    def _generate_and_download_pdf(codigo_editar, excel_data):
        """Generar y mostrar botón de descarga de PDF"""
        try:
            try:
                import reportlab
            except ImportError:
                st.error("📦 **Instalar reportlab:** `pip install reportlab`")
                return
            
            try:
                from pdf_generator import PDFGenerator
            except ImportError:
                st.error("❌ Archivo pdf_generator.py no encontrado")
                return
            
            pdf_generator = PDFGenerator()
            
            if not pdf_generator.is_available():
                st.error("📦 PDF no disponible. Instala: `pip install reportlab`")
                return
            
            with st.spinner("📄 Generando ficha metodológica en PDF..."):
                pdf_bytes = pdf_generator.generate_metodological_sheet(codigo_editar, excel_data)
                
                if pdf_bytes and len(pdf_bytes) > 0:
                    st.success("✅ PDF generado correctamente")
                    st.balloons()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Ficha_Metodologica_{codigo_editar}_{timestamp}.pdf"
                    
                    st.download_button(
                        label="📄 Descargar Ficha Metodológica PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        key=f"download_pdf_{codigo_editar}_{timestamp}",
                        use_container_width=True,
                        help=f"Descargar ficha metodológica de {codigo_editar}"
                    )
                else:
                    st.error("❌ No se pudo generar el PDF. Verifica los datos metodológicos.")
                    
        except Exception as e:
            st.error(f"❌ Error al generar PDF: {e}")
            import traceback
            with st.expander("🔧 Detalles del error"):
                st.code(traceback.format_exc())

    @staticmethod
    def _show_metodological_info_display(codigo_editar, excel_data):
        """Mostrar información metodológica en pantalla"""
        if excel_data is None or excel_data.empty:
            st.warning("No hay datos metodológicos disponibles")
            return
            
        # Buscar datos del indicador en Excel
        indicador_metodologico = excel_data[excel_data['Codigo'] == codigo_editar]
        
        if not indicador_metodologico.empty:
            st.markdown("---")
            st.subheader(f"📋 Ficha Metodológica: {codigo_editar}")
            
            metodologia = indicador_metodologico.iloc[0]
            
            # Función auxiliar para obtener valores seguros
            def safe_get(campo, default='N/A'):
                try:
                    valor = metodologia.get(campo, default)
                    if pd.isna(valor) or valor == '' or str(valor).strip() == '':
                        return default
                    return str(valor).strip()
                except:
                    return default
            
            # Mostrar información metodológica en pestañas
            tab1, tab2, tab3 = st.tabs(["📊 Información Básica", "🔬 Metodología", "📞 Contacto"])
            
            with tab1:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Nombre:** {safe_get('Nombre_Indicador')}")
                    st.write(f"**Área Temática:** {safe_get('Area_Tematica')}")
                    st.write(f"**Sector:** {safe_get('Sector')}")
                with col_b:
                    st.write(f"**Entidad:** {safe_get('Entidad')}")
                    st.write(f"**Dependencia:** {safe_get('Dependencia')}")
                    st.write(f"**Tema:** {safe_get('Tema')}")
                
                st.write("**Definición:**")
                st.write(safe_get('Definicion'))
                
                st.write("**Objetivo:**")
                st.write(safe_get('Objetivo'))
            
            with tab2:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Unidad de medida:** {safe_get('Unidad_Medida')}")
                    st.write(f"**Periodicidad:** {safe_get('Periodicidad')}")
                    st.write(f"**Tipo de indicador:** {safe_get('Tipo_Indicador')}")
                with col_b:
                    st.write(f"**Fuente de información:** {safe_get('Fuente_Informacion')}")
                    st.write(f"**Tipo de acumulación:** {safe_get('Tipo_Acumulacion')}")
                
                st.write("**Fórmula de cálculo:**")
                st.write(safe_get('Formula_Calculo'))
                
                st.write("**Variables:**")
                st.write(safe_get('Variables'))
                
                metodologia_calculo = safe_get('Metodologia_Calculo')
                if metodologia_calculo != 'N/A':
                    st.write("**Metodología de cálculo:**")
                    st.write(metodologia_calculo)
            
            with tab3:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Directivo Responsable:** {safe_get('Directivo_Responsable')}")
                    st.write(f"**Correo electrónico:** {safe_get('Correo_Directivo')}")
                    st.write(f"**Teléfono:** {safe_get('Telefono_Contacto')}")
                with col_b:
                    enlaces = safe_get('Enlaces_Web')
                    if enlaces != 'N/A':
                        st.write("**Enlaces web:**")
                        st.write(enlaces)
                    
                    soporte = safe_get('Soporte_Legal')
                    if soporte != 'N/A':
                        st.write("**Soporte legal:**")
                        st.write(soporte)
                
                observaciones = safe_get('Observaciones')
                if observaciones != 'N/A':
                    st.write("**Observaciones:**")
                    st.write(observaciones)
                
                limitaciones = safe_get('Limitaciones')
                if limitaciones != 'N/A':
                    st.write("**Limitaciones:**")
                    st.write(limitaciones)
            
            # Botón para ocultar ficha
            if st.button("🔼 Ocultar Ficha", key=f"hide_ficha_{codigo_editar}"):
                st.session_state.show_ficha = False
                st.rerun()
                
        else:
            st.warning(f"No se encontró información metodológica para {codigo_editar}")
            st.session_state.show_ficha = False
    
    @staticmethod
    def _render_view_records(registros_indicador):
        """Renderizar tabla de registros existentes"""
        st.subheader("📋 Registros Existentes en Google Sheets")
        if not registros_indicador.empty:
            st.dataframe(
                registros_indicador[['Fecha', 'Valor', 'Componente', 'Categoria']], 
                use_container_width=True
            )
        else:
            st.info("No hay registros para este indicador en Google Sheets")
    
    @staticmethod
    def _render_new_indicator_form(df):
        """Formulario para crear nuevo indicador en Google Sheets"""
        st.subheader("➕ Crear Nuevo Indicador en Google Sheets")
        
        with st.form("form_nuevo_indicador"):
            col1, col2 = st.columns(2)
            
            with col1:
                nuevo_codigo = st.text_input(
                    "Código del Indicador",
                    placeholder="Ej: D01-3",
                    help="Código único para identificar el indicador"
                )
                
                nuevo_indicador = st.text_input(
                    "Nombre del Indicador",
                    placeholder="Ej: Porcentaje de datos actualizados",
                    help="Nombre descriptivo del indicador"
                )
                
                nuevo_componente = st.selectbox(
                    "Componente",
                    ["Datos", "Seguridad e interoperabilidad", "Gobernanza y estratégia", 
                     "Herramientas técnicas y tecnológicas", "Aprovechamiento de datos"],
                    help="Componente al que pertenece el indicador"
                )
            
            with col2:
                nueva_categoria = st.text_input(
                    "Categoría",
                    placeholder="Ej: 01. Disponibilidad",
                    help="Categoría específica dentro del componente"
                )
                
                nueva_linea = st.text_input(
                    "Línea de Acción",
                    placeholder="Ej: LA.2.3.",
                    help="Línea de acción correspondiente (opcional)"
                )
                
                primer_valor = st.number_input(
                    "Valor Inicial",
                    value=0.5,
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    help="Primer valor del indicador"
                )
                
                primera_fecha = st.date_input(
                    "Fecha Inicial",
                    help="Fecha del primer registro"
                )
            
            submitted = st.form_submit_button("➕ Crear Indicador en Google Sheets", use_container_width=True)
            
            if submitted:
                # Validaciones
                if not nuevo_codigo.strip():
                    st.error("❌ El código es obligatorio")
                    return
                
                if not nuevo_indicador.strip():
                    st.error("❌ El nombre del indicador es obligatorio")
                    return
                
                if not nueva_categoria.strip():
                    st.error("❌ La categoría es obligatoria")
                    return
                
                # Verificar que el código no exista
                if not df.empty and nuevo_codigo in df['Codigo'].values:
                    st.error(f"❌ El código '{nuevo_codigo}' ya existe en Google Sheets")
                    return
                
                # ✅ CORRECCIÓN CRÍTICA: Preservar pestaña activa antes de crear
                st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                
                # Crear el nuevo registro en Google Sheets
                try:
                    from google_sheets_manager import GoogleSheetsManager
                    sheets_manager = GoogleSheetsManager()
                    
                    # Preparar datos para Google Sheets
                    data_dict = {
                        'LINEA DE ACCIÓN': nueva_linea.strip(),
                        'COMPONENTE PROPUESTO': nuevo_componente,
                        'CATEGORÍA': nueva_categoria.strip(),
                        'COD': nuevo_codigo.strip(),
                        'Nombre de indicador': nuevo_indicador.strip(),
                        'Valor': primer_valor,
                        'Fecha': primera_fecha.strftime('%d/%m/%Y')
                    }
                    
                    success = sheets_manager.add_record(data_dict)
                    
                    if success:
                        st.success(f"✅ Indicador '{nuevo_codigo}' creado correctamente en Google Sheets")
                        # Actualizar session state para seleccionar el nuevo código
                        st.session_state.selected_codigo = nuevo_codigo
                        # Limpiar cache
                        st.cache_data.clear()
                        st.session_state.data_timestamp = st.session_state.get('data_timestamp', 0) + 1
                        st.info("🔄 Los datos se actualizarán automáticamente desde Google Sheets en unos segundos")
                        
                        # Botón manual de actualización que preserva la pestaña
                        if st.button("🔄 Actualizar ahora", key="refresh_after_create"):
                            st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                            st.rerun()
                    else:
                        st.error("❌ Error al crear el indicador en Google Sheets")
                        
                except Exception as e:
                    st.error(f"❌ Error al crear indicador en Google Sheets: {e}")
    
    @staticmethod
    def _render_add_form(df, codigo_editar):
        """Formulario para agregar nuevo registro a Google Sheets"""
        st.subheader("➕ Agregar Nuevo Registro")
        
        with st.form("form_agregar"):
            col1, col2 = st.columns(2)
            
            with col1:
                nueva_fecha = st.date_input(
                    "Nueva Fecha",
                    help="Selecciona la fecha para el nuevo registro"
                )
            
            with col2:
                nuevo_valor = st.number_input(
                    "Nuevo Valor",
                    value=0.5,
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    help="Valor entre 0 y 1, donde 1 = 100% de cumplimiento"
                )
            
            submitted = st.form_submit_button("➕ Agregar a Google Sheets", use_container_width=True)
            
            if submitted:
                # Verificar si ya existe un registro para esa fecha
                fecha_dt = pd.to_datetime(nueva_fecha)
                
                if not df.empty:
                    registro_existente = df[(df['Codigo'] == codigo_editar) & (df['Fecha'] == fecha_dt)]
                    
                    if not registro_existente.empty:
                        st.warning(f"Ya existe un registro para la fecha {nueva_fecha.strftime('%d/%m/%Y')} en Google Sheets. Usa la pestaña 'Editar' para modificarlo.")
                        return
                
                # ✅ CORRECCIÓN CRÍTICA: Preservar pestaña activa antes de agregar
                st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                
                # Agregar registro a Google Sheets
                success = DataEditor.add_new_record(df, codigo_editar, fecha_dt, nuevo_valor, None)
                
                if success:
                    st.success("✅ Nuevo registro agregado correctamente a Google Sheets")
                    st.info("🔄 Los datos se actualizarán automáticamente en unos segundos")
                    
                    # Limpiar cache
                    st.cache_data.clear()
                    st.session_state.data_timestamp = st.session_state.get('data_timestamp', 0) + 1
                    
                    # Botón manual de actualización que preserva la pestaña
                    if st.button("🔄 Ver cambios ahora", key="refresh_after_add"):
                        st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                        st.rerun()
                else:
                    st.error("❌ Error al agregar el nuevo registro a Google Sheets")
    
    @staticmethod
    def _render_edit_form(df, codigo_editar, registros_indicador):
        """Formulario para editar registro existente en Google Sheets"""
        st.subheader("✏️ Editar Registro Existente")
        
        if registros_indicador.empty:
            st.info("No hay registros existentes para editar en Google Sheets")
            return
        
        # Seleccionar registro a editar
        fechas_disponibles = registros_indicador['Fecha'].dt.strftime('%d/%m/%Y (%A)').tolist()
        fecha_seleccionada_str = st.selectbox(
            "Seleccionar fecha a editar",
            fechas_disponibles,
            help="Selecciona el registro que deseas modificar en Google Sheets"
        )
        
        if fecha_seleccionada_str:
            # Obtener la fecha real
            idx_seleccionado = fechas_disponibles.index(fecha_seleccionada_str)
            fecha_real = registros_indicador.iloc[idx_seleccionado]['Fecha']
            valor_actual = registros_indicador.iloc[idx_seleccionado]['Valor']
            
            with st.form("form_editar"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"📅 Fecha: {fecha_real.strftime('%d/%m/%Y')}")
                    st.info(f"📊 Valor actual: {valor_actual:.3f}")
                
                with col2:
                    nuevo_valor = st.number_input(
                        "Nuevo Valor",
                        value=float(valor_actual),
                        min_value=0.0,
                        max_value=1.0,
                        step=0.01,
                        help="Nuevo valor para este registro en Google Sheets"
                    )
                
                submitted = st.form_submit_button("✏️ Actualizar en Google Sheets", use_container_width=True)
                
                if submitted:
                    # ✅ CORRECCIÓN CRÍTICA: Preservar pestaña activa antes de editar
                    st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                    
                    success = DataEditor.update_record(df, codigo_editar, fecha_real, nuevo_valor, None)
                    
                    if success:
                        st.success(f"✅ Registro del {fecha_real.strftime('%d/%m/%Y')} actualizado correctamente en Google Sheets")
                        st.balloons()
                        st.info("🔄 Los datos se actualizarán automáticamente desde Google Sheets en unos segundos")
                        
                        # Limpiar cache
                        st.cache_data.clear()
                        st.session_state.data_timestamp = st.session_state.get('data_timestamp', 0) + 1
                        
                        # Botón manual de actualización que preserva la pestaña
                        if st.button("🔄 Ver cambios ahora", key="refresh_after_edit"):
                            st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                            st.rerun()
                    else:
                        st.error("❌ Error al actualizar el registro en Google Sheets")
    
    @staticmethod
    def _render_delete_form(df, codigo_editar, registros_indicador):
        """Formulario para eliminar registro de Google Sheets"""
        st.subheader("🗑️ Eliminar Registro")
        
        if registros_indicador.empty:
            st.info("No hay registros existentes para eliminar en Google Sheets")
            return
        
        # Seleccionar registro a eliminar
        fechas_disponibles = registros_indicador['Fecha'].dt.strftime('%d/%m/%Y (%A)').tolist()
        fecha_seleccionada_str = st.selectbox(
            "Seleccionar fecha a eliminar",
            fechas_disponibles,
            help="⚠️ CUIDADO: Esta acción eliminará el registro de Google Sheets y no se puede deshacer"
        )
        
        if fecha_seleccionada_str:
            # Obtener la fecha real
            idx_seleccionado = fechas_disponibles.index(fecha_seleccionada_str)
            fecha_real = registros_indicador.iloc[idx_seleccionado]['Fecha']
            valor_actual = registros_indicador.iloc[idx_seleccionado]['Valor']
            
            st.warning(f"""
            ⚠️ **ATENCIÓN**: Estás a punto de eliminar el registro de Google Sheets:
            - **Fecha**: {fecha_real.strftime('%d/%m/%Y')}
            - **Valor**: {valor_actual:.3f}
            
            Esta acción **NO SE PUEDE DESHACER** y eliminará el registro permanentemente de Google Sheets.
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                confirmar = st.checkbox("Confirmo que quiero eliminar este registro de Google Sheets", key="confirm_delete")
            
            with col2:
                if confirmar:
                    if st.button("🗑️ ELIMINAR DE GOOGLE SHEETS", type="primary", use_container_width=True):
                        # ✅ CORRECCIÓN CRÍTICA: Preservar pestaña activa antes de eliminar
                        st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                        
                        success = DataEditor.delete_record(df, codigo_editar, fecha_real, None)
                        
                        if success:
                            st.success(f"✅ Registro del {fecha_real.strftime('%d/%m/%Y')} eliminado correctamente de Google Sheets")
                            st.balloons()
                            st.info("🔄 Los datos se actualizarán automáticamente desde Google Sheets en unos segundos")
                            
                            # Limpiar cache
                            st.cache_data.clear()
                            st.session_state.data_timestamp = st.session_state.get('data_timestamp', 0) + 1
                            
                            # Botón manual de actualización que preserva la pestaña
                            if st.button("🔄 Ver cambios ahora", key="refresh_after_delete"):
                                st.session_state.active_tab_index = 3  # Mantener en Gestión de Datos
                                st.rerun()
                        else:
                            st.error("❌ Error al eliminar el registro de Google Sheets")

class TabManager:
    """Gestor de pestañas del dashboard - CORRECCIÓN CRÍTICA: Persistencia de pestañas"""
    
    def __init__(self, df, csv_path, excel_data=None):
        self.df = df
        self.csv_path = None  # No usamos CSV
        self.excel_data = excel_data
        
        # ✅ CORRECCIÓN CRÍTICA: Inicializar pestaña activa en session_state
        if 'active_tab_index' not in st.session_state:
            st.session_state.active_tab_index = 0
    
    def render_tabs(self, df_filtrado, filters):
        """Renderizar todas las pestañas manteniendo el estado activo - VERSIÓN CORREGIDA"""
        
        # Nombres de las pestañas
        tab_names = [
            "📊 Resumen General", 
            "🏗️ Resumen por Componente", 
            "📈 Evolución", 
            "⚙️ Gestión de Datos"
        ]
        
        # ✅ CORRECCIÓN CRÍTICA: Mantener selector en sidebar pero SIN interferir con pestañas
        with st.sidebar:
            st.markdown("### 🧭 Navegación")
            st.info(f"📍 **Sección actual:** {tab_names[st.session_state.active_tab_index].replace('📊 ', '').replace('🏗️ ', '').replace('📈 ', '').replace('⚙️ ', '')}")
            
            # Botones de navegación que preservan el estado
            if st.button("🔄 Ir a Resumen General", use_container_width=True):
                st.session_state.active_tab_index = 0
                st.rerun()
            
            if st.button("🏗️ Ir a Componentes", use_container_width=True):
                st.session_state.active_tab_index = 1
                st.rerun()
            
            if st.button("📈 Ir a Evolución", use_container_width=True):
                st.session_state.active_tab_index = 2
                st.rerun()
            
            if st.button("⚙️ Ir a Gestión", use_container_width=True):
                st.session_state.active_tab_index = 3
                st.rerun()
        
        # ✅ CORRECCIÓN CRÍTICA: Crear las pestañas normalmente y renderizar TODAS
        tab1, tab2, tab3, tab4 = st.tabs(tab_names)
        
        # ✅ RENDERIZAR TODAS las pestañas pero marcar la activa
        with tab1:
            GeneralSummaryTab.render(df_filtrado, filters.get('fecha'))
        
        with tab2:
            ComponentSummaryTab.render(df_filtrado, filters)
        
        with tab3:
            EvolutionTab.render(self.df, filters)
        
        with tab4:
            EditTab.render(self.df, None, self.excel_data)
        
        # ✅ INFORMACIÓN DE ESTADO en sidebar
        st.sidebar.markdown("---")
        
        # ✅ INFORMACIÓN sobre funcionalidad PDF
        with st.sidebar.expander("📄 Estado PDF", expanded=False):
            st.markdown("### 📄 Fichas Metodológicas")
            
            # Verificar reportlab
            try:
                import reportlab
                st.success("✅ reportlab: Disponible")
                reportlab_ok = True
            except ImportError:
                st.error("❌ reportlab: No instalado")
                st.code("pip install reportlab")
                reportlab_ok = False
            
            # Verificar archivo Excel
            if self.excel_data is not None and not self.excel_data.empty:
                st.success("✅ Excel: Cargado")
                st.info(f"📊 {len(self.excel_data)} indicadores metodológicos")
                excel_ok = True
            else:
                st.warning("⚠️ Excel: No disponible")
                st.info("Coloca 'Batería de indicadores.xlsx'")
                excel_ok = False
            
            # Estado general
            if reportlab_ok and excel_ok:
                st.success("🎉 **PDF completamente funcional**")
            elif reportlab_ok:
                st.warning("⚠️ **PDF parcial** (falta Excel)")
            elif excel_ok:
                st.warning("⚠️ **PDF parcial** (falta reportlab)")
            else:
                st.error("❌ **PDF no disponible**")
