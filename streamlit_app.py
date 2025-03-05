import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib

# Configurar matplotlib para usar una fuente que soporte caracteres especiales
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

# Configuración de la página
st.set_page_config(
    page_title="Establecimientos de Salud en Chile",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración para caracteres especiales en Streamlit
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Función para cargar los datos
@st.cache_data
def load_data():
    try:
        # Intentar primero con UTF-8
        try:
            df = pd.read_csv('data/establecimientos_20250225.csv', sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            # Si falla, intentar con latin1
            df = pd.read_csv('data/establecimientos_20250225.csv', sep=';', encoding='latin1')
            
        # Asegurarse de que las columnas de texto estén correctamente codificadas
        for col in df.select_dtypes(include=['object']).columns:
            try:
                # Intentar convertir explícitamente a unicode si es necesario
                df[col] = df[col].astype('unicode_escape').str.encode('latin1').str.decode('utf-8', errors='replace')
            except:
                pass
                
        return df, None
    except Exception as e:
        return None, str(e)

# Barra lateral con controles
st.sidebar.title("Configuración")

# Cargar todos los datos
df, error = load_data()

# Verificar si hubo error al cargar los datos
if error:
    st.error(f"Error al cargar los datos: {error}")
    st.stop()

# Añadir información sobre los datos en la barra lateral
st.sidebar.markdown("### Información del Dataset")
st.sidebar.info(f"""
- **Registros totales:** {len(df)}
- **Fuente:** Ministerio de Salud de Chile
""")

# Añadir filtros útiles si hay suficientes datos
if len(df) > 0:
    st.sidebar.markdown("### Filtros")
    
    # Botón de reinicio de filtros
    if st.sidebar.button("🔄 Reiniciar Filtros"):
        st.session_state['regiones_seleccionadas'] = []
        st.session_state['tipos_seleccionados'] = []
        st.session_state['sistemas_seleccionados'] = []
        st.session_state['estados_seleccionados'] = []
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Filtro por región (multiselección)
    if "RegionGlosa" in df.columns:
        regiones = sorted(df["RegionGlosa"].unique().tolist())
        regiones_seleccionadas = st.sidebar.multiselect(
            "Regiones",
            options=regiones,
            default=st.session_state.get('regiones_seleccionadas', []),
            help="Seleccione una o más regiones",
            key='regiones_seleccionadas'
        )
    
    # Filtro por tipo de establecimiento
    if "TipoEstablecimientoGlosa" in df.columns:
        tipos_establecimiento = sorted(df["TipoEstablecimientoGlosa"].unique().tolist())
        tipos_seleccionados = st.sidebar.multiselect(
            "Tipos de Establecimiento",
            options=tipos_establecimiento,
            default=st.session_state.get('tipos_seleccionados', []),
            help="Seleccione uno o más tipos de establecimiento",
            key='tipos_seleccionados'
        )
    
    # Filtro por sistema de salud
    if "TipoSistemaSaludGlosa" in df.columns:
        sistemas_salud = sorted(df["TipoSistemaSaludGlosa"].unique().tolist())
        sistemas_seleccionados = st.sidebar.multiselect(
            "Sistema de Salud",
            options=sistemas_salud,
            default=st.session_state.get('sistemas_seleccionados', []),
            help="Seleccione uno o más sistemas de salud",
            key='sistemas_seleccionados'
        )
    
    # Filtro por estado de funcionamiento
    if "EstadoFuncionamiento" in df.columns:
        estados = sorted(df["EstadoFuncionamiento"].unique().tolist())
        estados_seleccionados = st.sidebar.multiselect(
            "Estado de Funcionamiento",
            options=estados,
            default=st.session_state.get('estados_seleccionados', []),
            help="Seleccione uno o más estados de funcionamiento",
            key='estados_seleccionados'
        )
    
    # Aplicar todos los filtros seleccionados
    df_filtered = df.copy()
    
    if regiones_seleccionadas:
        df_filtered = df_filtered[df_filtered["RegionGlosa"].isin(regiones_seleccionadas)]
    
    if tipos_seleccionados:
        df_filtered = df_filtered[df_filtered["TipoEstablecimientoGlosa"].isin(tipos_seleccionados)]
    
    if sistemas_seleccionados:
        df_filtered = df_filtered[df_filtered["TipoSistemaSaludGlosa"].isin(sistemas_seleccionados)]
    
    if estados_seleccionados:
        df_filtered = df_filtered[df_filtered["EstadoFuncionamiento"].isin(estados_seleccionados)]
    
    # Mostrar conteo de establecimientos filtrados
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Establecimientos filtrados:** {len(df_filtered)}")
else:
    df_filtered = df

# Título principal
st.title("Análisis de Establecimientos de Salud en Chile")
st.markdown("Explore datos sobre establecimientos de salud en Chile.")

# Mostrar información básica
st.header("Información General")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Establecimientos", f"{len(df_filtered)}")

with col2:
    urgencia_count = df_filtered["TieneServicioUrgencia"].value_counts().get("SI", 0)
    st.metric("Con Servicio de Urgencia", f"{urgencia_count} ({urgencia_count/len(df_filtered)*100:.1f}%)")

with col3:
    # Comprobar si existe la columna TipoSistemaSaludGlosa para el cálculo
    if "TipoSistemaSaludGlosa" in df_filtered.columns:
        public_count = df_filtered[df_filtered["TipoSistemaSaludGlosa"] == "Público"].shape[0]
        st.metric("Sistema Público", f"{public_count} ({public_count/len(df_filtered)*100:.1f}%)")
    else:
        st.metric("Columnas Disponibles", f"{len(df_filtered.columns)}")

# Pestañas para organizar el contenido
tab1, tab2, tab3, tab4 = st.tabs(["Distribución Geográfica", "Tipos de Establecimientos", 
                                "Niveles de Atención", "Datos Brutos"])

# Tab 1: Distribución Geográfica
with tab1:
    st.subheader("Distribución por Región")
    
    if "RegionGlosa" in df_filtered.columns:
        # Contar establecimientos por región
        region_counts = df_filtered['RegionGlosa'].value_counts().reset_index()
        region_counts.columns = ['Región', 'Cantidad']
        region_counts['Porcentaje'] = (region_counts['Cantidad'] / len(df_filtered) * 100).round(1)
        
        # Mostrar gráfico y tabla lado a lado
        col1, col2 = st.columns([3, 2])
        
        with col1:
            fig, ax = plt.subplots(figsize=(10, 8))
            # Configurar el gráfico para mostrar correctamente los acentos
            plt.rcParams['font.family'] = 'DejaVu Sans'
            sns.barplot(x='Cantidad', y='Región', data=region_counts, ax=ax)
            ax.set_title('Establecimientos por Región', fontsize=14)
            ax.set_xlabel('Cantidad', fontsize=12)
            ax.set_ylabel('Región', fontsize=12)
            # Asegurar que las etiquetas del eje y se muestren completas
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.dataframe(region_counts, hide_index=True, 
                        column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f%%")})
    else:
        st.warning("No se encontró la columna 'RegionGlosa' en los datos")

# Tab 2: Tipos de Establecimientos
with tab2:
    st.subheader("Tipos de Establecimientos")
    
    if "TipoEstablecimientoGlosa" in df_filtered.columns:
        # Contar tipos de establecimientos
        tipo_counts = df_filtered['TipoEstablecimientoGlosa'].value_counts().reset_index()
        tipo_counts.columns = ['Tipo', 'Cantidad']
        tipo_counts['Porcentaje'] = (tipo_counts['Cantidad'] / len(df_filtered) * 100).round(1)
        
        # Mostrar gráfico y tabla
        fig, ax = plt.subplots(figsize=(10, 8))
        # Configurar el gráfico para mostrar correctamente los acentos
        plt.rcParams['font.family'] = 'DejaVu Sans'
        sns.barplot(x='Cantidad', y='Tipo', data=tipo_counts.head(10), ax=ax)
        ax.set_title('Principales Tipos de Establecimientos', fontsize=14)
        ax.set_xlabel('Cantidad', fontsize=12)
        ax.set_ylabel('Tipo', fontsize=12)
        # Asegurar que las etiquetas del eje y se muestren completas
        plt.tight_layout()
        st.pyplot(fig)
        
        st.dataframe(tipo_counts, hide_index=True,
                    column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f%%")})
        

    else:
        st.warning("No se encontró la columna 'TipoEstablecimientoGlosa' en los datos")

# Tab 3: Niveles de Atención
with tab3:
    st.subheader("Niveles de Atención y Complejidad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if "NivelAtencionEstabglosa" in df_filtered.columns:
            nivel_counts = df_filtered['NivelAtencionEstabglosa'].value_counts().reset_index()
            nivel_counts.columns = ['Nivel', 'Cantidad']
            
            fig, ax = plt.subplots(figsize=(8, 8))
            # Configurar el gráfico para mostrar correctamente los acentos
            plt.rcParams['font.family'] = 'DejaVu Sans'
            colors = sns.color_palette('pastel')[0:5]
            plt.pie(nivel_counts['Cantidad'], labels=nivel_counts['Nivel'], 
                   autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 12})
            plt.axis('equal')
            plt.title('Distribución por Nivel de Atención', fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("No se encontró la columna 'NivelAtencionEstabglosa' en los datos")
    
    with col2:
        if "NivelComplejidadEstabGlosa" in df_filtered.columns:
            complej_counts = df_filtered['NivelComplejidadEstabGlosa'].value_counts().reset_index()
            complej_counts.columns = ['Complejidad', 'Cantidad']
            
            fig, ax = plt.subplots(figsize=(8, 8))
            # Configurar el gráfico para mostrar correctamente los acentos
            plt.rcParams['font.family'] = 'DejaVu Sans'
            colors = sns.color_palette('pastel')[0:5]
            plt.pie(complej_counts['Cantidad'], labels=complej_counts['Complejidad'],
                   autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 12})
            plt.axis('equal')
            plt.title('Distribución por Nivel de Complejidad', fontsize=14)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("No se encontró la columna 'NivelComplejidadEstabGlosa' en los datos")

# Tab 4: Datos Brutos
with tab4:
    st.subheader(f"Muestra de Datos (primeras 10 filas de un total de {len(df_filtered)} registros)")
    
    # Seleccionar columnas importantes a mostrar (si existen)
    cols_to_show = [col for col in [
        'EstablecimientoGlosa', 'RegionGlosa', 'ComunaGlosa', 
        'TipoEstablecimientoGlosa', 'TipoSistemaSaludGlosa', 'NivelAtencionEstabglosa',
        'TieneServicioUrgencia'
    ] if col in df_filtered.columns]
    
    # Aplicar estilo personalizado para la tabla
    st.markdown("""
    <style>
    .dataframe {
        font-family: 'Roboto', sans-serif !important;
    }
    .dataframe th {
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if cols_to_show:
        # Crear una copia del dataframe para evitar advertencias
        display_df = df_filtered[cols_to_show].head(10).copy()
        
        # Configurar las columnas para mostrar correctamente
        column_config = {
            col: st.column_config.TextColumn(col) for col in cols_to_show
        }
        
        st.dataframe(
            display_df, 
            hide_index=False,
            column_config=column_config,
            use_container_width=True
        )
    else:
        st.dataframe(df_filtered.head(10), hide_index=False, use_container_width=True)
    
    # Opción para descargar datos
    st.download_button(
        label="Descargar datos completos como CSV",
        data=df_filtered.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
        file_name='establecimientos_salud.csv',
        mime='text/csv',
    )

# Footer
st.markdown("---")
st.markdown("""
**Análisis de Establecimientos de Salud en Chile** | Datos del Ministerio de Salud

Desarrollado por: Rodrigo Muñoz Soto  
📧 munozsoto.rodrigo@gmail.com | 🔗 [GitHub: rodrigooig](https://github.com/rodrigooig) | 💼 [LinkedIn](https://www.linkedin.com/in/munozsoto-rodrigo/)  
Versión: 0.0.1
""")
st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True) 