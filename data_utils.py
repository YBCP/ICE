"""
Utilidades para el manejo de datos del Dashboard ICE - Compatible con Google Sheets
"""

import pandas as pd
import os
import streamlit as st
from config import COLUMN_MAPPING, DEFAULT_META, CSV_SEPARATOR, CSV_FILENAME, EXCEL_FILENAME
import openpyxl  # Para leer archivos Excel
from google_sheets_manager import GoogleSheetsManager

class DataLoader:
    """Clase para cargar y procesar datos - COMPATIBLE CON GOOGLE SHEETS Y CSV"""
    
    def __init__(self, use_google_sheets=True):
        self.df = None
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(self.script_dir, CSV_FILENAME)
        self.use_google_sheets = use_google_sheets
        self.sheets_manager = GoogleSheetsManager() if use_google_sheets else None
    
    def load_data(self):
        """Cargar datos desde Google Sheets o CSV como fallback"""
        try:
            # Intentar cargar desde Google Sheets primero
            if self.use_google_sheets and self.sheets_manager:
                st.info("🔄 Intentando cargar desde Google Sheets...")
                df_sheets = self._load_from_google_sheets()
                
                if df_sheets is not None:
                    self.df = df_sheets
                    return self.df
                else:
                    st.warning("⚠️ Google Sheets no disponible, usando CSV como fallback")
            
            # Fallback a CSV
            st.info("🔄 Cargando desde archivo CSV...")
            df_csv = self._load_from_csv()
            
            if df_csv is not None:
                self.df = df_csv
                return self.df
            else:
                st.error("❌ No se pudieron cargar datos desde ninguna fuente")
                return None
                
        except Exception as e:
            st.error(f"❌ Error crítico en load_data: {e}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    def _load_from_google_sheets(self):
        """Cargar datos desde Google Sheets"""
        try:
            df = self.sheets_manager.load_data()
            
            if df is None or df.empty:
                return None
            
            # Procesar datos igual que CSV
            self._process_dataframe(df)
            
            # Verificar y limpiar
            if self._verify_and_clean_dataframe(df):
                st.success(f"✅ Datos cargados desde Google Sheets: {len(df)} registros")
                return df
            else:
                return None
                
        except Exception as e:
            st.warning(f"⚠️ Error al cargar desde Google Sheets: {e}")
            return None
    
    def _load_from_csv(self):
        """Cargar datos desde CSV (método original mantenido)"""
        try:
            # Código original del CSV
            self.df = pd.read_csv(self.csv_path, sep=CSV_SEPARATOR)
            
            # Debug info
            with st.expander("🔧 Debug: CSV cargado", expanded=False):
                st.write(f"**Archivo:** {self.csv_path}")
                st.write(f"**Shape:** {self.df.shape}")
                st.write(f"**Columnas:** {list(self.df.columns)}")
                if not self.df.empty:
                    st.dataframe(self.df.head(3))
            
            # Procesar datos
            self._process_dataframe(self.df)
            
            # Verificar y limpiar
            if self._verify_and_clean_dataframe(self.df):
                st.success(f"✅ Datos cargados desde CSV: {len(self.df)} registros")
                return self.df
            else:
                return None
                
        except Exception as e:
            st.error(f"❌ Error al cargar CSV: {e}")
            return None
    
    def _process_dataframe(self, df):
        """Procesar DataFrame (común para Google Sheets y CSV)"""
        try:
            # Renombrar columnas
            for original, nuevo in COLUMN_MAPPING.items():
                if original in df.columns:
                    df.rename(columns={original: nuevo}, inplace=True)
            
            # Procesar fechas
            self._process_dates(df)
            
            # Procesar valores
            self._process_values(df)
            
            # Añadir columnas por defecto
            self._add_default_columns(df)
            
        except Exception as e:
            st.error(f"Error al procesar DataFrame: {e}")
    
    def _verify_and_clean_dataframe(self, df):
        """Verificar y limpiar DataFrame"""
        try:
            # Verificar columnas esenciales
            required_columns = ['Codigo', 'Fecha', 'Valor', 'Componente', 'Categoria', 'Indicador']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Faltan columnas: {missing_columns}")
                st.write("**Columnas disponibles:**", list(df.columns))
                return False
            
            # Limpiar datos problemáticos
            df.dropna(subset=['Codigo', 'Fecha', 'Valor'], inplace=True)
            
            if df.empty:
                st.error("❌ No hay datos válidos después de la limpieza")
                return False
            
            return True
            
        except Exception as e:
            st.error(f"Error en verificación: {e}")
            return False
    
    def _process_dates(self, df):
        """Procesar fechas (método original mantenido)"""
        try:
            date_formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', 
                '%Y/%m/%d', '%m/%d/%Y', '%d.%m.%Y'
            ]
            
            fechas_convertidas = None
            
            for formato in date_formats:
                try:
                    fechas_convertidas = pd.to_datetime(df['Fecha'], format=formato, errors='coerce')
                    porcentaje_validas = (fechas_convertidas.notna().sum() / len(fechas_convertidas)) * 100
                    
                    if porcentaje_validas >= 50:
                        break
                except ValueError:
                    continue
            
            if fechas_convertidas is None:
                fechas_convertidas = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True)
            
            df['Fecha'] = fechas_convertidas
            
            # Filtrar fechas inválidas si son muchas
            fechas_invalidas = df['Fecha'].isna().sum()
            if fechas_invalidas > 5:
                df.dropna(subset=['Fecha'], inplace=True)
                st.warning(f"⚠️ Excluidas {fechas_invalidas} filas con fechas inválidas")
                
        except Exception as e:
            st.warning(f"Error al procesar fechas: {e}")
    
    def _process_values(self, df):
        """Procesar valores numéricos"""
        try:
            if df['Valor'].dtype == 'object':
                df['Valor'] = pd.to_numeric(
                    df['Valor'].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                )
        except Exception as e:
            st.warning(f"Error al procesar valores: {e}")
    
    def _add_default_columns(self, df):
        """Añadir columnas por defecto"""
        if 'Meta' not in df.columns:
            df['Meta'] = DEFAULT_META
        if 'Peso' not in df.columns:
            df['Peso'] = 1.0
    
    def get_data_source_info(self):
        """Obtener información sobre la fuente de datos"""
        if self.use_google_sheets and self.sheets_manager:
            return {
                'source': 'Google Sheets',
                'connection_info': self.sheets_manager.get_connection_info()
            }
        else:
            return {
                'source': 'CSV',
                'csv_path': self.csv_path
            }

# MANTENER TODAS LAS CLASES ORIGINALES SIN CAMBIOS
class DataProcessor:
    """Clase para procesar y calcular métricas de los datos"""
    
    @staticmethod
    def calculate_scores(df, fecha_filtro=None):
        """
        Calcular puntajes usando SIEMPRE el valor más reciente de cada indicador.
        CORREGIDO: Manejo robusto de errores y validaciones.
        """
        try:
            if df.empty:
                import streamlit as st
                st.warning("DataFrame vacío para cálculo de puntajes")
                return pd.DataFrame({'Componente': [], 'Puntaje_Ponderado': []}), \
                       pd.DataFrame({'Categoria': [], 'Puntaje_Ponderado': []}), 0

            # SIEMPRE usar el valor más reciente de cada indicador
            df_filtrado = DataProcessor._get_latest_values_by_indicator(df)

            if len(df_filtrado) == 0:
                import streamlit as st
                st.error("No se pudieron obtener valores más recientes de los indicadores")
                return pd.DataFrame({'Componente': [], 'Puntaje_Ponderado': []}), \
                       pd.DataFrame({'Categoria': [], 'Puntaje_Ponderado': []}), 0

            # Debug: Verificar estructura del DataFrame
            import streamlit as st
            with st.expander("🔧 Debug: Estructura de datos para cálculos", expanded=False):
                st.write(f"**Shape del DataFrame filtrado:** {df_filtrado.shape}")
                st.write(f"**Columnas disponibles:** {list(df_filtrado.columns)}")
                st.write(f"**Tipos de datos:**")
                st.write(df_filtrado.dtypes)
                if len(df_filtrado) > 0:
                    st.write("**Muestra de datos:**")
                    st.dataframe(df_filtrado.head())

            # Verificar columnas esenciales
            required_columns = ['Valor', 'Peso', 'Componente', 'Categoria']
            missing_columns = [col for col in required_columns if col not in df_filtrado.columns]
            if missing_columns:
                st.error(f"Faltan columnas esenciales: {missing_columns}")
                return pd.DataFrame({'Componente': [], 'Puntaje_Ponderado': []}), \
                       pd.DataFrame({'Categoria': [], 'Puntaje_Ponderado': []}), 0

            # Normalizar valores (0-1)
            df_filtrado['Valor_Normalizado'] = df_filtrado['Valor'].clip(0, 1)
            
            # Verificar que tenemos datos después de la normalización
            if df_filtrado['Valor_Normalizado'].isna().all():
                st.error("Todos los valores normalizados son NaN")
                return pd.DataFrame({'Componente': [], 'Puntaje_Ponderado': []}), \
                       pd.DataFrame({'Categoria': [], 'Puntaje_Ponderado': []}), 0
            
            # Calcular puntajes por componente
            try:
                puntajes_componente = DataProcessor._calculate_weighted_average_by_group(
                    df_filtrado, 'Componente'
                )
            except Exception as e:
                st.error(f"Error al calcular puntajes por componente: {e}")
                puntajes_componente = pd.DataFrame({'Componente': [], 'Puntaje_Ponderado': []})
            
            # Calcular puntajes por categoría
            try:
                puntajes_categoria = DataProcessor._calculate_weighted_average_by_group(
                    df_filtrado, 'Categoria'
                )
            except Exception as e:
                st.error(f"Error al calcular puntajes por categoría: {e}")
                puntajes_categoria = pd.DataFrame({'Categoria': [], 'Puntaje_Ponderado': []})
            
            # Calcular puntaje general
            try:
                peso_total = df_filtrado['Peso'].sum()
                if peso_total > 0:
                    puntaje_general = (df_filtrado['Valor_Normalizado'] * df_filtrado['Peso']).sum() / peso_total
                else:
                    puntaje_general = df_filtrado['Valor_Normalizado'].mean()
                
                # Verificar que el puntaje general es válido
                if pd.isna(puntaje_general):
                    puntaje_general = 0.0
                    
            except Exception as e:
                st.error(f"Error al calcular puntaje general: {e}")
                puntaje_general = 0.0

            return puntajes_componente, puntajes_categoria, puntaje_general
            
        except Exception as e:
            import streamlit as st
            st.error(f"Error crítico en calculate_scores: {e}")
            import traceback
            st.code(traceback.format_exc())
            return pd.DataFrame({'Componente': [], 'Puntaje_Ponderado': []}), \
                   pd.DataFrame({'Categoria': [], 'Puntaje_Ponderado': []}), 0
    
    @staticmethod
    def _get_latest_values_by_indicator(df):
        """
        Obtener el valor más reciente de cada indicador.
        CORREGIDO: Evita problemas de estructura multidimensional.
        """
        try:
            if df.empty:
                return df
            
            # Verificar que tenemos las columnas necesarias
            required_columns = ['Codigo', 'Fecha', 'Valor']
            if not all(col in df.columns for col in required_columns):
                import streamlit as st
                st.error(f"Faltan columnas requeridas: {required_columns}")
                return df
            
            # Remover filas con valores NaN en columnas críticas
            df_clean = df.dropna(subset=['Codigo', 'Fecha', 'Valor']).copy()
            
            if df_clean.empty:
                import streamlit as st
                st.warning("No hay datos válidos después de limpiar valores NaN")
                return df
            
            # MÉTODO CORREGIDO: Usar sort_values y drop_duplicates
            # Esto evita problemas con groupby().apply()
            df_latest = (df_clean
                        .sort_values(['Codigo', 'Fecha'])  # Ordenar por código y fecha
                        .groupby('Codigo', as_index=False)  # Agrupar por código
                        .last()  # Tomar el último registro de cada grupo
                        .reset_index(drop=True))  # Resetear índice
            
            import streamlit as st
            # Mostrar información de debug solo si hay problemas
            debug_info = len(df_clean['Codigo'].unique()) != len(df_latest)
            if debug_info:
                with st.expander("🔍 Debug: Valores más recientes por indicador", expanded=False):
                    st.write(f"**Total indicadores únicos en datos originales:** {df_clean['Codigo'].nunique()}")
                    st.write(f"**Registros después de filtrar:** {len(df_latest)}")
                    st.write(f"**Estructura del DataFrame resultante:** {df_latest.shape}")
                    st.dataframe(df_latest[['Codigo', 'Indicador', 'Valor', 'Fecha', 'Componente']].sort_values('Fecha'))
            
            return df_latest
            
        except Exception as e:
            import streamlit as st
            st.error(f"Error crítico al obtener valores más recientes: {e}")
            import traceback
            st.code(traceback.format_exc())
            # En caso de error, retornar DataFrame original como fallback
            return df
    
    @staticmethod
    def _calculate_weighted_average_by_group(df, group_column):
        """Calcular promedio ponderado por grupo - CORREGIDO para evitar errores dimensionales"""
        try:
            # Verificar que el DataFrame y la columna de agrupación son válidos
            if df.empty:
                return pd.DataFrame(columns=[group_column, 'Puntaje_Ponderado'])
            
            if group_column not in df.columns:
                import streamlit as st
                st.error(f"La columna '{group_column}' no existe en los datos")
                return pd.DataFrame(columns=[group_column, 'Puntaje_Ponderado'])
            
            # Verificar que tenemos las columnas necesarias
            required_cols = ['Valor_Normalizado', 'Peso']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                import streamlit as st
                st.error(f"Faltan columnas necesarias: {missing_cols}")
                return pd.DataFrame(columns=[group_column, 'Puntaje_Ponderado'])
            
            # Función para calcular promedio ponderado
            def weighted_avg(valores, pesos):
                """Calcular promedio ponderado de forma segura"""
                # Filtrar valores no nulos
                mask = pd.notna(valores) & pd.notna(pesos)
                if not mask.any():
                    return 0.0
                
                valores_clean = valores[mask]
                pesos_clean = pesos[mask]
                peso_total = pesos_clean.sum()
                
                if peso_total > 0:
                    return (valores_clean * pesos_clean).sum() / peso_total
                else:
                    return valores_clean.mean() if len(valores_clean) > 0 else 0.0
            
            # Calcular promedio ponderado por grupo usando agg()
            result = df.groupby(group_column).agg({
                'Valor_Normalizado': list,
                'Peso': list
            }).reset_index()
            
            # Aplicar la función de promedio ponderado
            result['Puntaje_Ponderado'] = result.apply(
                lambda row: weighted_avg(
                    pd.Series(row['Valor_Normalizado']), 
                    pd.Series(row['Peso'])
                ), axis=1
            )
            
            # Mantener solo las columnas necesarias
            result = result[[group_column, 'Puntaje_Ponderado']]
            
            return result
            
        except Exception as e:
            import streamlit as st
            st.error(f"Error en cálculo ponderado por {group_column}: {e}")
            import traceback
            st.code(traceback.format_exc())
            # Retornar DataFrame vacío pero con estructura correcta
            return pd.DataFrame(columns=[group_column, 'Puntaje_Ponderado'])
    
    @staticmethod
    def create_pivot_table(df, fecha=None, filas='Categoria', columnas='Componente', valores='Valor'):
        """Crear tabla dinámica (función legacy - ya no se usa)"""
        return pd.DataFrame()  # Función deshabilitada

class DataEditor:
    """Clase para editar datos - COMPATIBLE CON GOOGLE SHEETS Y CSV"""
    
    def __init__(self, use_google_sheets=True):
        self.use_google_sheets = use_google_sheets
        self.sheets_manager = GoogleSheetsManager() if use_google_sheets else None
    
    @staticmethod
    def save_edit(df, codigo, fecha, nuevo_valor, csv_path):
        """Guardar edición de un indicador (función heredada para compatibilidad)"""
        return DataEditor.update_record(df, codigo, fecha, nuevo_valor, csv_path)
    
    @staticmethod
    def add_new_record(df, codigo, fecha, valor, csv_path):
        """Agregar un nuevo registro - COMPATIBLE CON GOOGLE SHEETS Y CSV"""
        try:
            # Determinar si usar Google Sheets o CSV
            use_sheets = DataEditor._should_use_google_sheets()
            
            if use_sheets:
                return DataEditor._add_record_google_sheets(df, codigo, fecha, valor)
            else:
                return DataEditor._add_record_csv(df, codigo, fecha, valor, csv_path)
                
        except Exception as e:
            st.error(f"❌ Error al agregar registro: {e}")
            return False
    
    @staticmethod
    def update_record(df, codigo, fecha, nuevo_valor, csv_path):
        """Actualizar un registro existente - COMPATIBLE CON GOOGLE SHEETS Y CSV"""
        try:
            # Determinar si usar Google Sheets o CSV
            use_sheets = DataEditor._should_use_google_sheets()
            
            if use_sheets:
                return DataEditor._update_record_google_sheets(codigo, fecha, nuevo_valor)
            else:
                return DataEditor._update_record_csv(df, codigo, fecha, nuevo_valor, csv_path)
                
        except Exception as e:
            st.error(f"❌ Error al actualizar registro: {e}")
            return False
    
    @staticmethod
    def delete_record(df, codigo, fecha, csv_path):
        """Eliminar un registro existente - COMPATIBLE CON GOOGLE SHEETS Y CSV"""
        try:
            # Determinar si usar Google Sheets o CSV
            use_sheets = DataEditor._should_use_google_sheets()
            
            if use_sheets:
                return DataEditor._delete_record_google_sheets(codigo, fecha)
            else:
                return DataEditor._delete_record_csv(df, codigo, fecha, csv_path)
                
        except Exception as e:
            st.error(f"❌ Error al eliminar registro: {e}")
            return False
    
    @staticmethod
    def _should_use_google_sheets():
        """Determinar si debe usar Google Sheets basado en la configuración"""
        try:
            # Verificar si Google Sheets está configurado
            return ("google_sheets" in st.secrets and 
                    "spreadsheet_url" in st.secrets["google_sheets"])
        except:
            return False
    
    @staticmethod
    def _add_record_google_sheets(df, codigo, fecha, valor):
        """Agregar registro a Google Sheets"""
        try:
            sheets_manager = GoogleSheetsManager()
            
            # Buscar información base del indicador
            indicador_existente = df[df['Codigo'] == codigo]
            if indicador_existente.empty:
                st.error(f"❌ No se encontró información base para el código {codigo}")
                return False
            
            indicador_base = indicador_existente.iloc[0]
            
            # Formatear fecha
            fecha_formateada = fecha.strftime('%d/%m/%Y') if hasattr(fecha, 'strftime') else pd.to_datetime(fecha).strftime('%d/%m/%Y')
            
            # Crear diccionario de datos
            data_dict = {
                'Linea_Accion': indicador_base.get('Linea_Accion', ''),
                'Componente': indicador_base.get('Componente', ''),
                'Categoria': indicador_base.get('Categoria', ''),
                'Codigo': codigo,
                'Indicador': indicador_base.get('Indicador', ''),
                'Valor': valor,
                'Fecha': fecha_formateada
            }
            
            # Agregar a Google Sheets
            success = sheets_manager.add_record(data_dict)
            
            if success:
                # Forzar recarga de cache
                st.cache_data.clear()
                if 'data_timestamp' not in st.session_state:
                    st.session_state.data_timestamp = 0
                st.session_state.data_timestamp += 1
            
            return success
            
        except Exception as e:
            st.error(f"❌ Error en Google Sheets: {e}")
            return False
    
    @staticmethod
    def _update_record_google_sheets(codigo, fecha, nuevo_valor):
        """Actualizar registro en Google Sheets"""
        try:
            sheets_manager = GoogleSheetsManager()
            success = sheets_manager.update_record(codigo, fecha, nuevo_valor)
            
            if success:
                # Forzar recarga de cache
                st.cache_data.clear()
                if 'data_timestamp' not in st.session_state:
                    st.session_state.data_timestamp = 0
                st.session_state.data_timestamp += 1
            
            return success
            
        except Exception as e:
            st.error(f"❌ Error en Google Sheets: {e}")
            return False
    
    @staticmethod
    def _delete_record_google_sheets(codigo, fecha):
        """Eliminar registro de Google Sheets"""
        try:
            sheets_manager = GoogleSheetsManager()
            success = sheets_manager.delete_record(codigo, fecha)
            
            if success:
                # Forzar recarga de cache
                st.cache_data.clear()
                if 'data_timestamp' not in st.session_state:
                    st.session_state.data_timestamp = 0
                st.session_state.data_timestamp += 1
            
            return success
            
        except Exception as e:
            st.error(f"❌ Error en Google Sheets: {e}")
            return False
    
    @staticmethod
    def _add_record_csv(df, codigo, fecha, valor, csv_path):
        """Agregar registro a CSV (método original mantenido)"""
        try:
            # Leer el CSV actual para mantener el formato original
            df_actual = pd.read_csv(csv_path, sep=CSV_SEPARATOR)
            
            # Debug: Ver formato de fechas existentes
            import streamlit as st
            with st.expander("🔧 Debug: Formato de fechas en CSV", expanded=False):
                st.write("**Fechas existentes en CSV:**")
                st.write(df_actual['Fecha'].head().tolist())
                st.write(f"**Fecha nueva a agregar:** {fecha}")
                st.write(f"**Tipo de fecha nueva:** {type(fecha)}")
            
            # Obtener información base del indicador desde df_actual
            codigo_col = None
            for col_name in ['COD', 'Codigo']:
                if col_name in df_actual.columns:
                    codigo_col = col_name
                    break
            
            if codigo_col is None:
                st.error("❌ No se encontró columna de código en el CSV")
                return False
            
            # Buscar información base del indicador
            indicadores_existentes = df_actual[df_actual[codigo_col] == codigo]
            if len(indicadores_existentes) == 0:
                st.error(f"❌ No se encontró información base para el código {codigo}")
                return False
                
            indicador_base = indicadores_existentes.iloc[0]
            
            # IMPORTANTE: Convertir fecha al formato correcto del CSV
            # Detectar formato de fechas existentes en el CSV
            sample_date = df_actual['Fecha'].dropna().iloc[0] if len(df_actual['Fecha'].dropna()) > 0 else None
            
            if sample_date:
                # Si las fechas existentes están en formato d/m/Y, usar ese formato
                if '/' in str(sample_date):
                    fecha_formateada = fecha.strftime('%d/%m/%Y') if hasattr(fecha, 'strftime') else pd.to_datetime(fecha).strftime('%d/%m/%Y')
                else:
                    # Si están en otro formato, usar ISO
                    fecha_formateada = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else pd.to_datetime(fecha).strftime('%Y-%m-%d')
            else:
                # Por defecto usar formato d/m/Y que es el esperado por el sistema
                fecha_formateada = fecha.strftime('%d/%m/%Y') if hasattr(fecha, 'strftime') else pd.to_datetime(fecha).strftime('%d/%m/%Y')
            
            # Debug: Mostrar formato final
            with st.expander("🔧 Debug: Fecha formateada", expanded=False):
                st.write(f"**Fecha original:** {fecha}")
                st.write(f"**Fecha formateada:** {fecha_formateada}")
                st.write(f"**Formato detectado en CSV:** {sample_date}")
            
            # Crear nueva fila manteniendo la estructura original del CSV
            nueva_fila = {}
            for col in df_actual.columns:
                if col == 'Fecha':
                    nueva_fila[col] = fecha_formateada  # Usar fecha formateada
                elif col == 'Valor':
                    nueva_fila[col] = valor
                else:
                    # Mantener el valor original de la primera fila del indicador
                    nueva_fila[col] = indicador_base[col]
            
            # Agregar nueva fila al DataFrame
            df_nuevo = pd.concat([df_actual, pd.DataFrame([nueva_fila])], ignore_index=True)
            
            # Guardar al CSV manteniendo el formato original
            df_nuevo.to_csv(csv_path, sep=CSV_SEPARATOR, index=False)
            
            # Debug: Verificar que se guardó correctamente
            with st.expander("🔧 Debug: Verificación de guardado", expanded=False):
                df_verificacion = pd.read_csv(csv_path, sep=CSV_SEPARATOR)
                st.write(f"**Registros totales después de guardar:** {len(df_verificacion)}")
                st.write("**Últimas 3 filas guardadas:**")
                st.dataframe(df_verificacion.tail(3))
            
            # FORZAR recarga completa del cache
            st.cache_data.clear()
            if 'data_timestamp' not in st.session_state:
                st.session_state.data_timestamp = 0
            st.session_state.data_timestamp += 1
            
            return True
            
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Error al agregar nuevo registro: {e}")
            import traceback
            st.code(traceback.format_exc())
            return False
    
    @staticmethod
    def _update_record_csv(df, codigo, fecha, nuevo_valor, csv_path):
        """Actualizar un registro existente en CSV (método original mantenido)"""
        try:
            # Leer el CSV actual con el mismo separador
            df_actual = pd.read_csv(csv_path, sep=CSV_SEPARATOR)
            
            # Procesar fechas si es necesario
            df_actual['Fecha'] = pd.to_datetime(df_actual['Fecha'], errors='coerce')
            
            # Determinar la columna de código correcta
            codigo_col = None
            for col_name in ['COD', 'Codigo']:
                if col_name in df_actual.columns:
                    codigo_col = col_name
                    break
            
            if codigo_col is None:
                import streamlit as st
                st.error("❌ No se encontró columna de código en el CSV (COD o Codigo)")
                return False
            
            # Encontrar el índice del registro a actualizar
            idx = df_actual[(df_actual[codigo_col] == codigo) & (df_actual['Fecha'] == fecha)].index
            
            if len(idx) > 0:
                # Actualizar el valor
                df_actual.loc[idx, 'Valor'] = nuevo_valor
                # Guardar al CSV manteniendo el formato original
                df_actual.to_csv(csv_path, sep=CSV_SEPARATOR, index=False)
                
                # Forzar recarga de datos en Streamlit
                import streamlit as st
                if 'data_timestamp' not in st.session_state:
                    st.session_state.data_timestamp = 0
                st.session_state.data_timestamp += 1
                
                return True
            else:
                import streamlit as st
                st.error(f"❌ No se encontró registro para código {codigo} en fecha {fecha.strftime('%d/%m/%Y')}")
                # Debug: mostrar registros disponibles para este código
                registros_codigo = df_actual[df_actual[codigo_col] == codigo]
                if not registros_codigo.empty:
                    st.write("**Registros disponibles para este código:**")
                    st.dataframe(registros_codigo[['Fecha', 'Valor']])
                return False
                
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Error al actualizar el registro: {e}")
            import traceback
            st.code(traceback.format_exc())
            return False
    
    @staticmethod
    def _delete_record_csv(df, codigo, fecha, csv_path):
        """Eliminar un registro existente de CSV (método original mantenido)"""
        try:
            # Leer el CSV actual
            df_actual = pd.read_csv(csv_path, sep=CSV_SEPARATOR)
            
            # Procesar fechas si es necesario
            df_actual['Fecha'] = pd.to_datetime(df_actual['Fecha'], errors='coerce')
            
            # Determinar la columna de código correcta
            codigo_col = None
            for col_name in ['COD', 'Codigo']:
                if col_name in df_actual.columns:
                    codigo_col = col_name
                    break
            
            if codigo_col is None:
                import streamlit as st
                st.error("❌ No se encontró columna de código en el CSV")
                return False
            
            # Encontrar el índice del registro a eliminar
            idx = df_actual[(df_actual[codigo_col] == codigo) & (df_actual['Fecha'] == fecha)].index
            
            if len(idx) > 0:
                # Eliminar la fila
                df_nuevo = df_actual.drop(idx).reset_index(drop=True)
                # Guardar al CSV
                df_nuevo.to_csv(csv_path, sep=CSV_SEPARATOR, index=False)
                
                # Forzar recarga de datos en Streamlit
                import streamlit as st
                if 'data_timestamp' not in st.session_state:
                    st.session_state.data_timestamp = 0
                st.session_state.data_timestamp += 1
                
                return True
            else:
                import streamlit as st
                st.error(f"❌ No se encontró registro para eliminar")
                return False
                
        except Exception as e:
            import streamlit as st
            st.error(f"❌ Error al eliminar el registro: {e}")
            import traceback
            st.code(traceback.format_exc())
            return False

# MANTENER CLASE ORIGINAL SIN CAMBIOS
class ExcelDataLoader:
    """Clase para cargar datos del archivo Excel con hojas metodológicas"""
    
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.excel_path = os.path.join(self.script_dir, "Batería de indicadores.xlsx")
        self.metodologicas_data = None
    
    def load_excel_data(self):
        """Cargar datos del Excel"""
        try:
            # Verificar que el archivo existe
            if not os.path.exists(self.excel_path):
                st.warning(f"Archivo Excel no encontrado: {self.excel_path}")
                return None
            
            # Leer la hoja metodológica
            df_metodologicas = pd.read_excel(
                self.excel_path, 
                sheet_name="Hoja metodológica indicadores",
                header=1  # La segunda fila contiene los headers
            )
            
            # Renombrar columnas para facilitar el acceso
            column_mapping = {
                'C1_ID': 'Codigo',
                'C2_Nombre indicador': 'Nombre_Indicador',
                'C3_Definición': 'Definicion',
                'C4_Objetivo': 'Objetivo',
                'C5_Área temática': 'Area_Tematica',
                'C6_Tema': 'Tema',
                'C7_Soporte Legal': 'Soporte_Legal',
                'C8_Fórmula de cálculo': 'Formula_Calculo',
                'C9_Variables': 'Variables',
                'C10_Unidad de medida': 'Unidad_Medida',
                'C11_Fuente de Información': 'Fuente_Informacion',
                'C12_Tipo de indicador': 'Tipo_Indicador',
                'C13_Periodicidad ': 'Periodicidad',
                'C14_Desagregación Geográfica': 'Desagregacion_Geografica',
                'Metodología de cálculo': 'Metodologia_Calculo',
                'C15_Desagregación poblacional-diferencial': 'Desagregacion_Poblacional',
                'C16_Observaciones / Notas Técnicas': 'Observaciones',
                'Clasificación según calidad': 'Clasificacion_Calidad',
                'Clasificación según nivel de intervención': 'Clasificacion_Intervencion',
                'Tipo de acumulación': 'Tipo_Acumulacion',
                'C17_Enlaces web relacionados': 'Enlaces_Web',
                'Interpretación': 'Interpretacion',
                'Limitaciones': 'Limitaciones',
                'C18_Sector': 'Sector',
                'C19_Entidad': 'Entidad',
                'C20_Dependencia': 'Dependencia',
                'C21_Directivo/a Responsable': 'Directivo_Responsable',
                'C22_Correo electrónico del directivo': 'Correo_Directivo',
                'C23_Teléfono de contacto': 'Telefono_Contacto'
            }
            
            # Renombrar columnas existentes
            for old_name, new_name in column_mapping.items():
                if old_name in df_metodologicas.columns:
                    df_metodologicas = df_metodologicas.rename(columns={old_name: new_name})
            
            # Limpiar datos vacíos
            df_metodologicas = df_metodologicas.dropna(subset=['Codigo'])
            
            self.metodologicas_data = df_metodologicas
            st.success(f"✅ Datos del Excel cargados: {len(df_metodologicas)} indicadores metodológicos")
            return df_metodologicas
            
        except Exception as e:
            st.error(f"Error al cargar datos del Excel: {e}")
            return None
    
    def get_indicator_data(self, codigo):
        """Obtener datos de un indicador específico por código"""
        if self.metodologicas_data is None:
            self.load_excel_data()
        
        if self.metodologicas_data is None:
            return None
        
        try:
            # Buscar el indicador por código
            indicator_data = self.metodologicas_data[
                self.metodologicas_data['Codigo'] == codigo
            ]
            
            if len(indicator_data) > 0:
                return indicator_data.iloc[0].to_dict()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error al obtener datos del indicador {codigo}: {e}")
            return None
