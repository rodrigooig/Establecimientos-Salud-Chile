import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib
import folium
import plotly.express as px
import plotly.graph_objects as go
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

# Barra lateral con controles personalizados
st.sidebar.title("¡Bienvenido!👋")
st.sidebar.caption("En esta app podrás explorar datos de los establecimientos de salud en Chile.")
st.sidebar.caption("Puedes revisar el código fuente en [GitHub](https://github.com/rodrigooig/establecimientos-salud-chile)")

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

# Indicador de carga para la carga inicial de datos
with st.spinner('Cargando datos de establecimientos de salud...'):
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

# Mostrar información básica
st.header("Información General")

# Restaurar las columnas para los 3 KPIs principales
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("**Total Establecimientos**", f"{len(df_filtered)}")

with col2:
    urgencia_count = df_filtered["TieneServicioUrgencia"].value_counts().get("SI", 0)
    st.metric("**Con Servicio de Urgencia**", f"{urgencia_count} ({urgencia_count/len(df_filtered)*100:.1f}%)")

with col3:
    # Comprobar si existe la columna TipoSistemaSaludGlosa para el cálculo
    if "TipoSistemaSaludGlosa" in df_filtered.columns:
        public_count = df_filtered[df_filtered["TipoSistemaSaludGlosa"] == "Público"].shape[0]
        st.metric("Sistema Público", f"{public_count} ({public_count/len(df_filtered)*100:.1f}%)")
    else:
        st.metric("Columnas Disponibles", f"{len(df_filtered.columns)}")

# Agregar línea de separación después de la información general
st.divider()

# Pestañas para organizar el contenido
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Distribución Geográfica", "Tipos de Establecimientos", 
                                "Niveles de Atención", "Evolución Histórica", "Datos Brutos"])

# Tab 1: Distribución Geográfica
with tab1:
    # Sección para el mapa (movida al principio)
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
        folium_static(m, width=1000, height=600)

    # Verificar si hay columnas de coordenadas
    if "Latitud" in df_filtered.columns and "Longitud" in df_filtered.columns:
        # Filtrar datos con coordenadas válidas
        map_data = df_filtered.dropna(subset=['Latitud', 'Longitud']).copy()
        
        # Verificar si hay datos con coordenadas
        if len(map_data) > 0:
            # Guía de colores usando elementos nativos de Streamlit
            st.info("**Guía de colores:** 🟢 Establecimientos públicos, 🔴 Establecimientos privados, ⚪ Otros.")
            
            # Añadir indicador de carga mientras se procesa el mapa
            with st.spinner('Construyendo mapa interactivo... Por favor espere unos segundos.'):
                # Mostrar un mensaje de progreso personalizado
                progress_placeholder = st.empty()
                
                # Visualizar el mapa
                visualizar_mapa(map_data)
                
                # Eliminar el mensaje de progreso una vez cargado
                progress_placeholder.empty()
        else:
            st.warning("No hay datos con coordenadas geográficas válidas para mostrar en el mapa.")
    else:
        st.warning("No se encontraron las columnas de coordenadas 'Latitud' y 'Longitud' en los datos.")

    # Ahora mostramos la sección de distribución por región (movida después del mapa)
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
        
        # Mostrar gráfico y tabla uno debajo del otro (sin columnas)
        st.markdown("#### Gráfico de Distribución por Región y Sistema de Salud")
        
        # Definir colores para cada tipo de sistema
        colors = ['#2ecc71', '#e74c3c', '#95a5a6']  # Verde para Público, Rojo para Privado, Gris para Otros
        
        # Crear gráfico de barras apiladas interactivo con Plotly
        fig = go.Figure()
        
        # Añadir una barra para cada tipo de sistema
        for idx, col in enumerate(['Público', 'Privado', 'Otros']):
            fig.add_trace(go.Bar(
                name=col,
                y=region_sistema['RegionGlosa'],
                x=region_sistema[col],
                orientation='h',
                marker_color=colors[idx],
                hovertemplate='<b>%{y}</b><br>' +
                             col + ': <b>%{x}</b><extra></extra>'
            ))
        
        # Actualizar el diseño del gráfico
        fig.update_layout(
            title={
                'text': 'Establecimientos por Región y Sistema de Salud',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18)
            },
            barmode='stack',
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                title='Sistema de Salud'
            ),
            margin=dict(l=50, r=50, t=100, b=50),
            xaxis_title='Cantidad de Establecimientos',
            yaxis_title='Región'
        )
        
        # Mostrar el gráfico interactivo en Streamlit
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Tabla de Distribución por Región")
        st.dataframe(region_counts, hide_index=True,
                    column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f%%")})
    else:
        st.warning("No se encontraron las columnas necesarias en los datos")

# Tab 2: Tipos de Establecimientos
with tab2:
    st.subheader("Tipos de Establecimientos")
    
    if "TipoEstablecimientoGlosa" in df_filtered.columns:
        # Spinner para la carga de datos de tipos de establecimientos
        with st.spinner('Procesando información de tipos de establecimientos...'):
            # Contar tipos de establecimientos
            tipo_counts = df_filtered['TipoEstablecimientoGlosa'].value_counts().reset_index()
            tipo_counts.columns = ['Tipo', 'Cantidad']
            tipo_counts['Porcentaje'] = (tipo_counts['Cantidad'] / len(df_filtered) * 100).round(1)
        
        # Añadir descripción introductoria usando elementos nativos de Streamlit
        st.info("Los establecimientos de salud se clasifican en diferentes tipos según sus características, servicios ofrecidos y nivel de complejidad. A continuación se muestra la distribución de los diferentes tipos de establecimientos filtrados.")
        
        # Mostrar gráfico y tabla uno debajo del otro (sin columnas)
        st.subheader("Gráfico de Tipos de Establecimientos")
        
        # Spinner para la generación del gráfico
        with st.spinner('Generando visualización...'):
            # Crear gráfico de barras horizontal interactivo con Plotly
            fig = go.Figure()
            
            # Usar los 20 tipos más frecuentes
            tipos_data = tipo_counts.head(20)
            
            # Añadir la barra principal
            fig.add_trace(go.Bar(
                x=tipos_data['Cantidad'],
                y=tipos_data['Tipo'],
                orientation='h',
                marker_color=px.colors.sequential.Blues[-2],  # Usar un tono de azul consistente
                hovertemplate='<b>%{y}</b><br>' +
                             'Cantidad: <b>%{x}</b><br>' +
                             'Porcentaje: <b>%{text}</b><extra></extra>',
                text=[f'{n} ({p:.1f}%)' for n, p in zip(tipos_data['Cantidad'], tipos_data['Porcentaje'])],
                textposition='outside',
            ))
            
            # Actualizar el diseño del gráfico
            fig.update_layout(
                title={
                    'text': 'Tipos de Establecimientos',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=18)
                },
                height=max(500, len(tipos_data) * 35),  # Aumentar el factor de multiplicación de 25 a 35
                margin=dict(l=50, r=150, t=80, b=50),  # Mantener los márgenes
                xaxis_title='Cantidad de Establecimientos',
                yaxis_title='Tipo de Establecimiento',
                yaxis={'categoryorder': 'total ascending'},  # Ordenar de menor a mayor
                showlegend=False
            )
            
            # Mostrar el gráfico interactivo en Streamlit
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Tabla de Tipos de Establecimientos")
        st.dataframe(tipo_counts, hide_index=True,
                    column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f%%")})
    else:
        st.warning("No se encontró la columna 'TipoEstablecimientoGlosa' en los datos")

# Tab 3: Niveles de Atención
with tab3:
    st.subheader("Niveles de Atención y Complejidad")
    
    # Agregar contexto introductorio usando elementos nativos de Streamlit
    st.info("El nivel de atención y complejidad de un establecimiento de salud define su capacidad resolutiva y el tipo de servicios que puede ofrecer. Los establecimientos primarios atienden necesidades básicas, mientras que los de mayor complejidad ofrecen servicios especializados.")
    
    # Mostrar gráficos uno debajo del otro (sin columnas)
    
    # Gráfico de Nivel de Atención
    st.subheader("Distribución por Nivel de Atención")
    if "NivelAtencionEstabglosa" in df_filtered.columns:
        # Spinner para el procesamiento de datos y generación del gráfico
        with st.spinner('Analizando niveles de atención...'):
            nivel_counts = df_filtered['NivelAtencionEstabglosa'].value_counts().reset_index()
            nivel_counts.columns = ['Nivel', 'Cantidad']
            
            # Ordenar de mayor a menor cantidad
            nivel_counts = nivel_counts.sort_values('Cantidad', ascending=True)  # Ordenar ascendente para que aparezca en sentido horario
            
            # Usar paleta de colores pastel
            colors = px.colors.qualitative.Pastel
            
            # Crear gráfico de donut interactivo con Plotly
            fig = go.Figure(data=[go.Pie(
                labels=nivel_counts['Nivel'],
                values=nivel_counts['Cantidad'],
                hole=0.4,
                marker=dict(colors=colors, line=dict(color='white', width=2)),
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=12),
                hoverinfo='label+value+percent',
                hovertemplate='<b>%{label}</b><br>Cantidad: <b>%{value}</b><br>Porcentaje: <b>%{percent}</b><extra></extra>',
                direction='clockwise',
                sort=True
            )])
            
            # Configurar el diseño del gráfico
            fig.update_layout(
                title={
                    'text': 'Distribución por Nivel de Atención',
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=18)
                },
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                height=500,
                annotations=[
                    dict(
                        text='Niveles<br>de Atención',
                        x=0.5,
                        y=0.5,
                        font=dict(size=15),
                        showarrow=False
                    )
                ]
            )
            
            # Mostrar el gráfico interactivo en Streamlit
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se encontró la columna 'NivelAtencionEstabglosa' en los datos")
    
    # Agregar línea de separación
    st.divider()
    
    # Gráfico de Nivel de Complejidad
    st.subheader("Distribución por Nivel de Complejidad")
    if "NivelComplejidadEstabGlosa" in df_filtered.columns:
        complej_counts = df_filtered['NivelComplejidadEstabGlosa'].value_counts().reset_index()
        complej_counts.columns = ['Complejidad', 'Cantidad']
        
        # Ordenar de mayor a menor cantidad
        complej_counts = complej_counts.sort_values('Cantidad', ascending=True)  # Ordenar ascendente para que aparezca en sentido horario
        
        # Usar paleta de colores pastel
        colors = px.colors.qualitative.Pastel
        
        # Crear gráfico de donut interactivo con Plotly
        fig = go.Figure(data=[go.Pie(
            labels=complej_counts['Complejidad'],
            values=complej_counts['Cantidad'],
            hole=0.4,
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=12),
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Cantidad: <b>%{value}</b><br>Porcentaje: <b>%{percent}</b><extra></extra>',
            direction='clockwise',
            sort=True
        )])
        
        # Configurar el diseño del gráfico
        fig.update_layout(
            title={
                'text': 'Distribución por Nivel de Complejidad',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18)
            },
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            height=500,
            annotations=[
                dict(
                    text='Niveles<br>de Complejidad',
                    x=0.5,
                    y=0.5,
                    font=dict(size=15),
                    showarrow=False
                )
            ]
        )
        
        # Mostrar el gráfico interactivo en Streamlit
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se encontró la columna 'NivelComplejidadEstabGlosa' en los datos")

# Tab 4: Evolución Histórica
with tab4:
    st.subheader("Inauguración de Establecimientos de Salud por Año")
    
    # Agregar contexto introductorio usando elementos nativos de Streamlit
    st.info("Este gráfico interactivo muestra la inauguración de establecimientos de salud según su fecha de inicio de funcionamiento desde 2010, agrupados por año y categorizados por nivel de complejidad. Puedes hacer zoom, pasar el cursor sobre los puntos para ver detalles, y más.")
    
    # Verificar si existen las columnas necesarias
    if "FechaInicioFuncionamientoEstab" in df_filtered.columns and "NivelComplejidadEstabGlosa" in df_filtered.columns:
        # Spinner para el procesamiento de datos y generación del gráfico
        with st.spinner('Procesando datos históricos...'):
            # Crear una copia del DataFrame para no modificar el original
            df_historico = df_filtered.copy()
            
            # Convertir la columna de fecha a tipo datetime
            try:
                df_historico['FechaInicioFuncionamientoEstab'] = pd.to_datetime(
                    df_historico['FechaInicioFuncionamientoEstab'], 
                    errors='coerce'  # Convertir errores a NaT
                )
                
                # Filtrar registros con fechas válidas
                df_historico = df_historico.dropna(subset=['FechaInicioFuncionamientoEstab'])
                
                # Extraer el año de la fecha
                df_historico['Año'] = df_historico['FechaInicioFuncionamientoEstab'].dt.year
                
                # Filtrar solo desde 2010 en adelante
                df_historico = df_historico[df_historico['Año'] >= 2010]
                
                # Filtrar solo los niveles de complejidad solicitados
                niveles_complejidad = ['Alta Complejidad', 'Mediana Complejidad', 'Baja Complejidad']
                df_historico = df_historico[df_historico['NivelComplejidadEstabGlosa'].isin(niveles_complejidad)]
                
                if len(df_historico) > 0:
                    # Agrupar por año y nivel de complejidad
                    df_agrupado = df_historico.groupby(['Año', 'NivelComplejidadEstabGlosa']).size().reset_index(name='Cantidad')
                    
                    # Definir colores para cada nivel de complejidad
                    colores = {
                        'Alta Complejidad': '#e74c3c',    # Rojo
                        'Mediana Complejidad': '#f39c12', # Naranja
                        'Baja Complejidad': '#2ecc71'     # Verde
                    }
                    
                    # Crear un gráfico interactivo con Plotly
                    fig = go.Figure()
                    
                    # Añadir una línea para cada nivel de complejidad
                    for nivel in niveles_complejidad:
                        df_nivel = df_agrupado[df_agrupado['NivelComplejidadEstabGlosa'] == nivel]
                        if not df_nivel.empty:
                            fig.add_trace(go.Scatter(
                                x=df_nivel['Año'],
                                y=df_nivel['Cantidad'],
                                mode='lines+markers+text',
                                name=nivel,
                                line=dict(color=colores.get(nivel, '#3498db'), width=3),
                                marker=dict(size=10, symbol='circle'),
                                text=df_nivel['Cantidad'],
                                textposition='top center',
                                textfont=dict(size=12, color='black'),
                                hovertemplate='<b>%{x}</b><br>' +
                                             '<b>' + nivel + '</b><br>' +
                                             'Establecimientos inaugurados: <b>%{y}</b><extra></extra>'
                            ))
                    
                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        title={
                            'text': 'Inauguración de Establecimientos de Salud por Nivel de Complejidad (desde 2010)',
                            'y': 0.95,
                            'x': 0.5,
                            'xanchor': 'center',
                            'yanchor': 'top',
                            'font': dict(size=20)
                        },
                        xaxis_title='Año de Inauguración',
                        yaxis_title='Cantidad de Establecimientos Inaugurados',
                        
                        hovermode='closest',
                        xaxis=dict(
                            tickmode='array',
                            tickvals=sorted(df_historico['Año'].unique()),
                            ticktext=sorted(df_historico['Año'].unique()),
                            gridcolor='lightgray',
                            gridwidth=0.5
                        ),
                        yaxis=dict(
                            gridcolor='lightgray',
                            gridwidth=0.5
                        ),
                        plot_bgcolor='white',
                        height=600,
                        width=900,
                        margin=dict(l=50, r=50, t=80, b=50),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5
                        )
                    )
                    
                    # Añadir herramientas interactivas
                    fig.update_layout(
                        updatemenus=[
                            dict(
                                type="buttons",
                                direction="left",
                                buttons=[
                                    dict(
                                        args=[{"yaxis.type": "linear"}],
                                        label="Escala Lineal",
                                        method="relayout"
                                    ),
                                    dict(
                                        args=[{"yaxis.type": "log"}],
                                        label="Escala Logarítmica",
                                        method="relayout"
                                    )
                                ],
                                pad={"r": 10, "t": 10},
                                showactive=True,
                                x=0.1,
                                xanchor="left",
                                y=1.1,
                                yanchor="top"
                            )
                        ]
                    )
                    
                    # Añadir anotaciones para guiar al usuario

                    
                    # Mostrar el gráfico interactivo en Streamlit
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Agregar línea de separación
                    st.divider()
                    
                    # Mostrar tabla con los datos
                    st.subheader("Tabla de Inauguraciones por Año (desde 2010)")
                    
                    # Crear una tabla más legible
                    tabla_historica = df_agrupado.pivot_table(
                        values='Cantidad', 
                        index='Año',
                        columns='NivelComplejidadEstabGlosa', 
                        aggfunc='sum'
                    ).fillna(0).astype(int)
                    
                    # Ordenar por año
                    tabla_historica = tabla_historica.sort_index()
                    
                    # Mostrar la tabla
                    st.dataframe(
                        tabla_historica,
                        use_container_width=True
                    )
                else:
                    st.warning("No hay suficientes datos para generar el gráfico histórico con los filtros seleccionados.")
            except Exception as e:
                st.error(f"Error al procesar los datos históricos: {str(e)}")
    else:
        st.warning("No se encontraron las columnas necesarias para el análisis histórico.")

# Tab 5: Datos Brutos
with tab5:
    st.subheader("Muestra de Datos")
    
    # Agregar descripción usando elementos nativos de Streamlit
    st.info(f"A continuación se muestra una muestra de los datos filtrados. Se presentan las primeras 10 filas de un total de **{len(df_filtered)}** registros. Puede descargar el conjunto completo de datos utilizando el botón al final de esta sección.")
    
    # Spinner para la carga de la tabla de datos
    with st.spinner('Preparando visualización de datos...'):
        # Seleccionar columnas importantes a mostrar (si existen)
        cols_to_show = [col for col in [
            'EstablecimientoGlosa', 'RegionGlosa', 'ComunaGlosa', 
            'TipoEstablecimientoGlosa', 'TipoSistemaSaludGlosa', 'NivelAtencionEstabglosa',
            'TieneServicioUrgencia'
        ] if col in df_filtered.columns]
        
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
Versión: 0.1.1
""")
st.markdown("""
<style>
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True) 