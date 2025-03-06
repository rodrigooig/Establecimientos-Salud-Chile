import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

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
            df = pd.read_csv('data/establecimientos_cleaned.csv', sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            # Si falla, intentar con latin1
            df = pd.read_csv('data/establecimientos_cleaned.csv', sep=';', encoding='latin1')
            
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
    
    if "RegionGlosa" in df_filtered.columns and "TipoSistemaSaludGlosa" in df_filtered.columns:
        # Crear una copia del DataFrame y agrupar los sistemas de salud
        df_plot = df_filtered.copy()
        df_plot['TipoSistemaSaludGlosa'] = df_plot['TipoSistemaSaludGlosa'].apply(
            lambda x: x if x in ['Público', 'Privado'] else 'Otros'
        )
        
        # Crear un DataFrame con el conteo por región y sistema de salud
        region_sistema = pd.crosstab(
            df_plot['RegionGlosa'], 
            df_plot['TipoSistemaSaludGlosa'],
            margins=False
        ).reset_index()
        
        # Asegurar que todas las columnas existan
        for col in ['Público', 'Privado', 'Otros']:
            if col not in region_sistema.columns:
                region_sistema[col] = 0
        
        # Reordenar las columnas para que Público y Privado aparezcan primero
        cols = ['RegionGlosa', 'Público', 'Privado', 'Otros']
        region_sistema = region_sistema[cols]
        
        # Calcular el total por región para ordenar
        region_counts = df_filtered['RegionGlosa'].value_counts().reset_index()
        region_counts.columns = ['Región', 'Cantidad']
        region_counts['Porcentaje'] = (region_counts['Cantidad'] / len(df_filtered) * 100).round(1)
        
        # Ordenar regiones por cantidad total y establecer el orden
        regiones_ordenadas = region_counts['Región'].tolist()
        region_sistema['RegionGlosa'] = pd.Categorical(
            region_sistema['RegionGlosa'],
            categories=regiones_ordenadas,
            ordered=True
        )
        region_sistema = region_sistema.sort_values('RegionGlosa', ascending=False)
        
        # Mostrar gráfico y tabla lado a lado
        col1, col2 = st.columns([3, 2])
        
        with col1:
            fig, ax = plt.subplots(figsize=(12, 10))
            # Configurar el gráfico para mostrar correctamente los acentos
            plt.rcParams['font.family'] = 'DejaVu Sans'
            
            # Definir colores para cada tipo de sistema
            colors = ['#2ecc71', '#e74c3c', '#95a5a6']  # Verde para Público, Rojo para Privado, Gris para Otros
            
            # Crear el gráfico de barras apiladas
            bottom = np.zeros(len(region_sistema))
            
            for idx, col in enumerate(['Público', 'Privado', 'Otros']):
                ax.barh(region_sistema['RegionGlosa'], 
                       region_sistema[col], 
                       left=bottom, 
                       color=colors[idx], 
                       label=col)
                bottom += region_sistema[col]
            
            ax.set_title('Establecimientos por Región y Sistema de Salud', fontsize=14)
            ax.set_xlabel('Cantidad', fontsize=12)
            ax.set_ylabel('Región', fontsize=12)
            
            # Añadir leyenda en una posición adecuada
            plt.legend(title='Sistema de Salud', bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # Asegurar que las etiquetas del eje y se muestren completas
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.dataframe(region_counts, hide_index=True, 
                        column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f%%")})
    else:
        st.warning("No se encontraron las columnas necesarias en los datos")
    
    # Sección para el mapa
    st.subheader("Distribución Geográfica de Establecimientos")
    
    @st.cache_data
    def procesar_datos_mapa(map_data):
        """
        Procesa los datos para preparar la visualización en el mapa.
        Cachea el resultado para mejorar el rendimiento.
        
        Args:
            map_data (pd.DataFrame): DataFrame con datos de establecimientos.
        
        Returns:
            tuple: DataFrame con conteo de establecimientos por ubicación y datos procesados.
        """
        # Crear una columna con coordenadas como tupla (más eficiente que apply con lambda)
        map_data = map_data.copy()
        map_data['location'] = list(zip(map_data['Latitud'], map_data['Longitud']))
        
        # Calcular frecuencia por ubicación
        location_counts = pd.DataFrame(map_data['location'].value_counts()).reset_index()
        location_counts.columns = ['coords', 'count']
        
        return location_counts, map_data

    def obtener_color_sistema(sistema_principal):
        """Determina el color según el tipo de sistema de salud."""
        if sistema_principal == 'Público':
            return 'green'
        elif sistema_principal == 'Privado':
            return 'red'
        return 'gray'  # Default para otros casos

    def crear_texto_popup(establecimientos, count):
        """
        Crea el texto para el popup de cada marcador.
        
        Args:
            establecimientos (pd.DataFrame): DataFrame con establecimientos en esa ubicación.
            count (int): Cantidad de establecimientos.
            
        Returns:
            tuple: Texto HTML para el popup y color a usar para el marcador.
        """
        popup_text = f"Cantidad: {count} establecimiento(s)"
        
        # Función auxiliar para limitar y formatear listas de texto
        def formatear_lista(items, max_items=5):
            if len(items) > max_items:
                return "<br>".join(items[:max_items]) + f"<br>... y {len(items) - max_items} más"
            return "<br>".join(items)
        
        # Añadir nombres de establecimientos
        if 'EstablecimientoGlosa' in establecimientos.columns:
            establecimientos_list = establecimientos['EstablecimientoGlosa'].unique()
            establecimientos_text = formatear_lista(establecimientos_list)
            popup_text += f"<br><br><b>Establecimientos: </b><br>{establecimientos_text}"
        
        # Añadir tipos de establecimiento
        if 'TipoEstablecimientoGlosa' in establecimientos.columns:
            tipos_establecimientos = establecimientos['TipoEstablecimientoGlosa'].unique()
            if len(tipos_establecimientos) > 0:
                tipos_text = formatear_lista(tipos_establecimientos)
                popup_text += f"<br><br><b>Tipo(s) de establecimiento: </b><br>{tipos_text}"
        
        # Obtener color basado en el tipo de sistema de salud
        color = 'gray'  # Default
        if "TipoSistemaSaludGlosa" in establecimientos.columns:
            sistemas = establecimientos['TipoSistemaSaludGlosa'].value_counts()
            if not sistemas.empty:
                sistema_principal = sistemas.index[0]
                popup_text += f"<br><br><b>Sistema principal: </b><br>{sistema_principal}"
                color = obtener_color_sistema(sistema_principal)
        
        return popup_text, color

    def visualizar_mapa(map_data):
        """
        Crea y muestra un mapa interactivo con los establecimientos de salud.
        
        Args:
            map_data (pd.DataFrame): DataFrame con los datos filtrados que contienen coordenadas válidas.
        """
        # Crear mapa centrado en Chile
        m = folium.Map(location=[-33.45694, -70.64827], zoom_start=5)
        
        # Agrupar marcadores para mejor rendimiento
        marker_cluster = MarkerCluster().add_to(m)
        
        # Procesar datos para el mapa (con caché para mejorar rendimiento)
        location_counts, map_data_processed = procesar_datos_mapa(map_data)
        
        # Añadir marcadores al mapa
        for _, row in location_counts.iterrows():
            lat, lon = row['coords']
            count = row['count']
            
            # Filtrar establecimientos en esta ubicación (usar loc para mayor eficiencia)
            establecimientos = map_data_processed.loc[(map_data_processed['Latitud'] == lat) & 
                                                (map_data_processed['Longitud'] == lon)]
            
            # Crear texto para popup y determinar color
            popup_text, color = crear_texto_popup(establecimientos, count)
            
            # Añadir círculo al mapa con un radio fijo
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=popup_text,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7
            ).add_to(marker_cluster)
        
        # Mostrar el mapa en Streamlit
        st.markdown("Los colores de los círculos indican el tipo de sistema de salud: verde (público), rojo (privado), gris (otros).")
        folium_static(m, width=1000, height=600)

    # Verificar si hay columnas de coordenadas
    if "Latitud" in df_filtered.columns and "Longitud" in df_filtered.columns:
        # Filtrar datos con coordenadas válidas
        map_data = df_filtered.dropna(subset=['Latitud', 'Longitud']).copy()
        
        # Verificar si hay datos con coordenadas
        if len(map_data) > 0:
            visualizar_mapa(map_data)
        else:
            st.warning("No hay datos con coordenadas geográficas válidas para mostrar en el mapa.")
    else:
        st.warning("No se encontraron las columnas de coordenadas 'Latitud' y 'Longitud' en los datos.")

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
Versión: 0.0.3
""")
st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True) 