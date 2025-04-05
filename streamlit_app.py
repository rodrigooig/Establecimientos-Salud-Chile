import streamlit as st
import pandas as pd
import matplotlib
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

# --- Constants ---
DATA_PATH = 'data/establecimientos_cleaned.csv'
COL_REGION = "RegionGlosa"
COL_TIPO_ESTAB = "TipoEstablecimientoGlosa"
COL_SISTEMA = "TipoSistemaSaludGlosa"
COL_ESTADO = "EstadoFuncionamiento"
COL_URGENCIA = "TieneServicioUrgencia"
COL_NIVEL_ATENCION = "NivelAtencionEstabglosa"
COL_NIVEL_COMPLEJIDAD = "NivelComplejidadEstabGlosa"
COL_FECHA_INICIO = "FechaInicioFuncionamientoEstab"
COL_LAT = "Latitud"
COL_LON = "Longitud"
COL_NOMBRE = "EstablecimientoGlosa"
COL_COMUNA = "ComunaGlosa"

SYSTEM_COLORS = {'Público': '#2ecc71', 'Privado': '#e74c3c', 'Otros': '#95a5a6'}
COMPLEXITY_COLORS = {
    'Alta Complejidad': '#e74c3c',    # Rojo
    'Mediana Complejidad': '#f39c12', # Naranja
    'Baja Complejidad': '#2ecc71'     # Verde
}
DEFAULT_PLOTLY_COLORS = px.colors.qualitative.Pastel

# --- Matplotlib Configuration ---
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

# --- Page Configuration ---
st.set_page_config(
    page_title="Establecimientos de Salud en Chile",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---

@st.cache_data
def load_data(path=DATA_PATH):
    """Loads data from CSV, handling potential encoding issues."""
    try:
        try:
            df = pd.read_csv(path, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep=';', encoding='latin1')

        # Clean object columns encoding if necessary
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = df[col].astype('unicode_escape').str.encode('latin1').str.decode('utf-8', errors='replace')
            except Exception: # Broad except to catch various potential string issues
                pass # Ignore columns that can't be decoded

        return df, None
    except Exception as e:
        return None, str(e)

def create_multiselect_filter(df, column_name, label, key):
    """Creates a multiselect widget in the sidebar if the column exists."""
    if column_name in df.columns:
        options = sorted(df[column_name].unique().tolist())
        return st.sidebar.multiselect(
            label,
            options=options,
            default=st.session_state.get(key, []),
            help=f"Seleccione uno o más {label.lower()}",
            key=key
        )
    return []

def apply_filters(df, filters):
    """Applies a dictionary of filters to the DataFrame."""
    df_filtered = df.copy()
    for column, selected_values in filters.items():
        if selected_values:
            df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
    return df_filtered

def plot_horizontal_bar(df, category_col, title, xaxis_title, yaxis_title, n_top=20):
    """Generates and displays a Plotly horizontal bar chart."""
    if category_col not in df.columns:
        st.warning(f"No se encontró la columna '{category_col}' en los datos.")
        return

    with st.spinner('Generando visualización...'):
        counts = df[category_col].value_counts().reset_index()
        counts.columns = [yaxis_title, xaxis_title] # Use titles for column names
        total_count = len(df)
        counts['Porcentaje'] = (counts[xaxis_title] / total_count * 100)

        data_to_plot = counts.head(n_top)

        fig = go.Figure(go.Bar(
            x=data_to_plot[xaxis_title],
            y=data_to_plot[yaxis_title],
            orientation='h',
            marker_color=px.colors.sequential.Blues[-2],
            text=[f'{n} ({p:.1f}%)' for n, p in zip(data_to_plot[xaxis_title], data_to_plot['Porcentaje'])],
            textposition='outside',
            hovertemplate=f'<b>%{{y}}</b><br>{xaxis_title}: <b>%{{x}}</b><br>Porcentaje: <b>%{{text}}</b><extra></extra>'
        ))

        fig.update_layout(
            title={'text': title, 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': dict(size=18)},
            height=max(500, len(data_to_plot) * 35),
            margin=dict(l=50, r=150, t=80, b=50),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    return counts # Return the full counts DataFrame for potential table display

def plot_donut(df, category_col, title, center_text):
    """Generates and displays a Plotly donut chart."""
    if category_col not in df.columns:
        st.warning(f"No se encontró la columna '{category_col}' en los datos.")
        return

    with st.spinner(f'Analizando {category_col}...'):
        counts = df[category_col].value_counts().reset_index()
        counts.columns = ['Label', 'Cantidad']
        counts = counts.sort_values('Cantidad', ascending=True) # For clockwise display

        fig = go.Figure(data=[go.Pie(
            labels=counts['Label'],
            values=counts['Cantidad'],
            hole=0.4,
            marker=dict(colors=DEFAULT_PLOTLY_COLORS, line=dict(color='white', width=2)),
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=12),
            hoverinfo='label+value+percent',
            hovertemplate='<b>%{label}</b><br>Cantidad: <b>%{value}</b><br>Porcentaje: <b>%{percent}</b><extra></extra>',
            direction='clockwise',
            sort=True # Already sorted, but good practice
        )])

        fig.update_layout(
            title={'text': title, 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': dict(size=18)},
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=500,
            annotations=[dict(text=center_text, x=0.5, y=0.5, font=dict(size=15), showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True)

# --- Map Specific Helpers (Adapted from original) ---
@st.cache_data
def procesar_datos_mapa(map_data):
    """Processes data for map visualization (cached)."""
    map_data = map_data.copy()
    map_data['location'] = list(zip(map_data[COL_LAT], map_data[COL_LON]))
    location_counts = pd.DataFrame(map_data['location'].value_counts()).reset_index()
    location_counts.columns = ['coords', 'count']
    return location_counts, map_data

def obtener_color_sistema(sistema_principal):
    """Determines marker color based on health system."""
    return SYSTEM_COLORS.get(sistema_principal, 'gray') # Use constant map

def crear_texto_popup(establecimientos, count):
    """Creates HTML popup text for map markers."""
    popup_text = f"Cantidad: {count} establecimiento(s)"

    def formatear_lista(items, max_items=5):
        items = list(items) # Ensure it's a list
        if len(items) > max_items:
            return "<br>".join(items[:max_items]) + f"<br>... y {len(items) - max_items} más"
        return "<br>".join(items)

    if COL_NOMBRE in establecimientos.columns:
        nombres = formatear_lista(establecimientos[COL_NOMBRE].unique())
        popup_text += f"<br><br><b>Establecimientos: </b><br>{nombres}"

    if COL_TIPO_ESTAB in establecimientos.columns:
        tipos = formatear_lista(establecimientos[COL_TIPO_ESTAB].unique())
        if tipos:
            popup_text += f"<br><br><b>Tipo(s): </b><br>{tipos}"

    color = 'gray'
    if COL_SISTEMA in establecimientos.columns:
        sistemas = establecimientos[COL_SISTEMA].value_counts()
        if not sistemas.empty:
            sistema_principal = sistemas.index[0]
            popup_text += f"<br><br><b>Sistema principal: </b><br>{sistema_principal}"
            color = obtener_color_sistema(sistema_principal)

    return popup_text, color

def visualizar_mapa(map_data):
    """Creates and displays the Folium map."""
    if not all(col in map_data.columns for col in [COL_LAT, COL_LON]):
        st.warning(f"Faltan columnas '{COL_LAT}' o '{COL_LON}' para el mapa.")
        return

    map_data_valid = map_data.dropna(subset=[COL_LAT, COL_LON]).copy()
    if map_data_valid.empty:
        st.warning("No hay datos con coordenadas geográficas válidas para mostrar en el mapa.")
        return

    # Use markdown with HTML for colored circles
    color_guide_html = ' '.join([
        f'<span style="display:inline-block; background-color:{color}; border-radius:50%; width:10px; height:10px; margin-right:5px; vertical-align: middle;"></span> {name}'
        for name, color in SYSTEM_COLORS.items()
    ])
    st.markdown(f"**Guía de colores:** {color_guide_html}", unsafe_allow_html=True)

    with st.spinner('Construyendo mapa interactivo...'):
        m = folium.Map(location=[-33.45694, -70.64827], zoom_start=5)
        marker_cluster = MarkerCluster().add_to(m)
        location_counts, map_data_processed = procesar_datos_mapa(map_data_valid) # Use cached function

        for _, row in location_counts.iterrows():
            lat, lon = row['coords']
            count = row['count']
            # Efficient filtering using .loc
            establecimientos = map_data_processed.loc[
                (map_data_processed[COL_LAT] == lat) & (map_data_processed[COL_LON] == lon)
            ]
            popup_text, color = crear_texto_popup(establecimientos, count)

            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300), # Add max_width
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7
            ).add_to(marker_cluster)

        folium_static(m, width=1000, height=600)

# --- Main App Logic ---

# Load Data
with st.spinner('Cargando datos de establecimientos de salud...'):
    df, error = load_data()

if error:
    st.error(f"Error al cargar los datos: {error}")
    st.stop() # Stop execution if data loading fails

# Sidebar Setup
st.sidebar.title("¡Bienvenido!👋")
st.sidebar.caption("Explora datos de establecimientos de salud en Chile.")
st.sidebar.caption("Código fuente en [GitHub](https://github.com/rodrigooig/establecimientos-salud-chile)")
st.sidebar.markdown("### Información del Dataset")
st.sidebar.info(f"""
- **Registros totales:** {len(df)}
- **Fuente:** Ministerio de Salud de Chile
""")

# Sidebar Filters
df_filtered = df # Start with the full dataframe
if not df.empty:
    st.sidebar.markdown("### Filtros")

    # Reset Button
    if st.sidebar.button("🔄 Reiniciar Filtros"):
        keys_to_reset = ['regiones_sel', 'tipos_sel', 'sistemas_sel', 'estados_sel']
        for key in keys_to_reset:
            st.session_state[key] = []
        st.rerun()

    st.sidebar.markdown("---")

    # Create filters using helper
    filters_selected = {
        COL_REGION: create_multiselect_filter(df, COL_REGION, "Regiones", 'regiones_sel'),
        COL_TIPO_ESTAB: create_multiselect_filter(df, COL_TIPO_ESTAB, "Tipos de Establecimiento", 'tipos_sel'),
        COL_SISTEMA: create_multiselect_filter(df, COL_SISTEMA, "Sistema de Salud", 'sistemas_sel'),
        COL_ESTADO: create_multiselect_filter(df, COL_ESTADO, "Estado de Funcionamiento", 'estados_sel')
    }

    # Apply filters using helper
    df_filtered = apply_filters(df, filters_selected)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Establecimientos filtrados:** {len(df_filtered)}")

# --- Main Panel ---
st.title("Análisis de Establecimientos de Salud en Chile")

# KPIs
if not df_filtered.empty:
    col1, col2, col3 = st.columns(3)
    total_filtered = len(df_filtered)

    with col1:
        st.metric("**Total Establecimientos**", f"{total_filtered}")

    with col2:
        if COL_URGENCIA in df_filtered.columns:
            urgencia_count = df_filtered[COL_URGENCIA].value_counts().get("SI", 0)
            urgencia_perc = (urgencia_count / total_filtered * 100) if total_filtered else 0
            st.metric("**Con Servicio de Urgencia**", f"{urgencia_count} ({urgencia_perc:.1f}%)")
        else:
             st.metric("**Con Servicio de Urgencia**", "N/A")


    with col3:
        if COL_SISTEMA in df_filtered.columns:
            public_count = df_filtered[df_filtered[COL_SISTEMA] == "Público"].shape[0]
            public_perc = (public_count / total_filtered * 100) if total_filtered else 0
            st.metric("Sistema Público", f"{public_count} ({public_perc:.1f}%)")
        else:
             st.metric("Sistema Público", "N/A")
else:
    st.warning("No hay datos para mostrar con los filtros seleccionados.")
    # Optionally stop if no data? st.stop()


# Tabs for Content Organization
tab_titles = ["Distribución Geográfica", "Tipos de Establecimientos",
              "Niveles de Atención", "Evolución Histórica", "Datos Brutos"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)

# --- Tab 1: Distribución Geográfica ---
with tab1:
    st.subheader("Distribución Geográfica de Establecimientos")
    visualizar_mapa(df_filtered) # Use map helper function

    st.divider() # Add separator

    # Stacked Bar Chart: Region vs System
    st.subheader('Establecimientos por Región y Sistema de Salud')
    if all(c in df_filtered.columns for c in [COL_REGION, COL_SISTEMA]):
        df_plot = df_filtered.copy()
        # Group less common systems into 'Otros'
        df_plot[COL_SISTEMA] = df_plot[COL_SISTEMA].apply(
            lambda x: x if x in SYSTEM_COLORS else 'Otros'
        )

        # Use crosstab for counts
        region_sistema = pd.crosstab(
            df_plot[COL_REGION],
            df_plot[COL_SISTEMA]
        ).reset_index()

        # Ensure all system columns exist, fill with 0 if not
        for col in SYSTEM_COLORS.keys():
            if col not in region_sistema.columns:
                region_sistema[col] = 0

        # Order columns consistently
        ordered_cols = [COL_REGION] + list(SYSTEM_COLORS.keys())
        region_sistema = region_sistema[ordered_cols]

        # Order regions by total count (descending for plot)
        region_total_counts = df_filtered[COL_REGION].value_counts()
        region_sistema = region_sistema.set_index(COL_REGION).loc[region_total_counts.index].reset_index()

        # Create Plotly Figure
        fig_region_sys = go.Figure()
        for col in SYSTEM_COLORS.keys():
            fig_region_sys.add_trace(go.Bar(
                name=col,
                y=region_sistema[COL_REGION],
                x=region_sistema[col],
                orientation='h',
                marker_color=SYSTEM_COLORS[col],
                hovertemplate=f'<b>%{{y}}</b><br>{col}: <b>%{{x}}</b><extra></extra>'
            ))

        fig_region_sys.update_layout(
            barmode='stack',
            yaxis={'categoryorder': 'total ascending'}, # Already sorted by total, but good practice
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title='Sistema de Salud'),
            margin=dict(l=50, r=50, t=50, b=50), # Reduced top margin
            xaxis_title='Cantidad de Establecimientos',
            yaxis_title='Región'
            # Removed explicit title, using st.subheader above
        )
        st.plotly_chart(fig_region_sys, use_container_width=True)
    else:
        st.warning(f"Faltan columnas '{COL_REGION}' o '{COL_SISTEMA}' para el gráfico.")

    st.divider()

    # Treemap: Region vs Complexity
    st.subheader('Distribución Regional por Nivel de Complejidad')
    if all(c in df_filtered.columns for c in [COL_REGION, COL_NIVEL_COMPLEJIDAD]):
        niveles_complejidad_filter = list(COMPLEXITY_COLORS.keys()) # Use keys from constant
        df_treemap = df_filtered[df_filtered[COL_NIVEL_COMPLEJIDAD].isin(niveles_complejidad_filter)].copy()

        if not df_treemap.empty:
            treemap_data = df_treemap.groupby([COL_REGION, COL_NIVEL_COMPLEJIDAD]).size().reset_index(name='Cantidad')

            # Calculate totals for percentages
            region_totals = treemap_data.groupby(COL_REGION)['Cantidad'].sum().reset_index(name='Total_Region')
            treemap_data = treemap_data.merge(region_totals, on=COL_REGION)
            treemap_data['Porcentaje'] = (treemap_data['Cantidad'] / treemap_data['Total_Region'] * 100).round(1)

            fig_treemap = px.treemap(
                treemap_data,
                path=[COL_REGION, COL_NIVEL_COMPLEJIDAD],
                values='Cantidad',
                # title='Distribución Regional por Nivel de Complejidad', # Use subheader
                color=COL_REGION, # Color by region
                color_discrete_sequence=px.colors.qualitative.Set3,
                custom_data=['Cantidad', 'Porcentaje', 'Total_Region']
            )

            fig_treemap.update_traces(
                textinfo='label+text',
                texttemplate="%{label}<br>%{customdata[0]:,} (%{customdata[1]:.1f}%)",
                textposition="top left",
                textfont=dict(size=11),
                hovertemplate='<b>%{label}</b><br>' +
                             'Cantidad: %{customdata[0]:,}<br>' +
                             'Porcentaje de la región: %{customdata[1]:.1f}%<br>' +
                             'Total regional: %{customdata[2]:,}<extra></extra>'
            )

            fig_treemap.update_layout(
                height=800,
                margin=dict(l=20, r=20, t=20, b=20) # Reduced margins
            )
            st.plotly_chart(fig_treemap, use_container_width=True)
        else:
             st.warning("No hay datos de complejidad válidos para mostrar en el treemap.")
    else:
        st.warning(f"Faltan columnas '{COL_REGION}' o '{COL_NIVEL_COMPLEJIDAD}' para el treemap.")


# --- Tab 2: Tipos de Establecimientos ---
with tab2:
    st.subheader("Tipos de Establecimientos")
    st.info("Clasificación de establecimientos según características, servicios y complejidad.")

    # Use helper function for the bar chart
    tipo_counts_df = plot_horizontal_bar(
        df_filtered,
        category_col=COL_TIPO_ESTAB,
        title="Top 20 Tipos de Establecimientos",
        xaxis_title="Cantidad",
        yaxis_title="Tipo de Establecimiento",
        n_top=20
    )

    # Display table if data was generated
    if tipo_counts_df is not None and not tipo_counts_df.empty:
        st.divider()
        st.subheader("Tabla Completa de Tipos")
        st.dataframe(
            tipo_counts_df,
            hide_index=True,
            column_config={"Porcentaje": st.column_config.NumberColumn(format="%.1f%%")},
            use_container_width=True
        )


# --- Tab 3: Niveles de Atención ---
with tab3:
    st.subheader("Niveles de Atención y Complejidad")
    st.info("Capacidad resolutiva y tipo de servicios ofrecidos.")

    # Donut chart for Attention Level
    plot_donut(
        df_filtered,
        category_col=COL_NIVEL_ATENCION,
        title="Distribución por Nivel de Atención",
        center_text="Niveles<br>de Atención"
    )

    st.divider()

    # Donut chart for Complexity Level
    plot_donut(
        df_filtered,
        category_col=COL_NIVEL_COMPLEJIDAD,
        title="Distribución por Nivel de Complejidad",
        center_text="Niveles<br>de Complejidad"
    )

# --- Tab 4: Evolución Histórica ---
with tab4:
    st.subheader("Inauguración de Establecimientos por Año (desde 2010)")
    st.info("Evolución anual por nivel de complejidad. Interactúa con el gráfico.")

    if all(c in df_filtered.columns for c in [COL_FECHA_INICIO, COL_NIVEL_COMPLEJIDAD]):
        with st.spinner('Procesando datos históricos...'):
            df_historico = df_filtered.copy()
            try:
                # Convert to datetime, coerce errors, drop invalid dates
                df_historico[COL_FECHA_INICIO] = pd.to_datetime(df_historico[COL_FECHA_INICIO], errors='coerce')
                df_historico = df_historico.dropna(subset=[COL_FECHA_INICIO])

                # Extract year and filter
                df_historico['Año'] = df_historico[COL_FECHA_INICIO].dt.year
                df_historico = df_historico[df_historico['Año'] >= 2010]

                # Filter by relevant complexity levels
                niveles_complejidad_hist = list(COMPLEXITY_COLORS.keys())
                df_historico = df_historico[df_historico[COL_NIVEL_COMPLEJIDAD].isin(niveles_complejidad_hist)]

                if not df_historico.empty:
                    # Group data
                    df_agrupado = df_historico.groupby(['Año', COL_NIVEL_COMPLEJIDAD]).size().reset_index(name='Cantidad')

                    # Create Plotly Figure
                    fig_hist = go.Figure()
                    for nivel in niveles_complejidad_hist:
                        df_nivel = df_agrupado[df_agrupado[COL_NIVEL_COMPLEJIDAD] == nivel]
                        if not df_nivel.empty:
                            fig_hist.add_trace(go.Scatter(
                                x=df_nivel['Año'],
                                y=df_nivel['Cantidad'],
                                mode='lines+markers+text',
                                name=nivel,
                                line=dict(color=COMPLEXITY_COLORS.get(nivel, '#3498db'), width=3),
                                marker=dict(size=10, symbol='circle'),
                                text=df_nivel['Cantidad'],
                                textposition='top center',
                                textfont=dict(size=12, color='black'),
                                hovertemplate=f'<b>%{{x}}</b><br><b>{nivel}</b><br>Inaugurados: <b>%{{y}}</b><extra></extra>'
                            ))

                    # Configure Layout
                    unique_years = sorted(df_historico['Año'].unique())
                    fig_hist.update_layout(
                        # title is handled by st.subheader
                        xaxis_title='Año de Inauguración',
                        yaxis_title='Cantidad de Establecimientos Inaugurados',
                        hovermode='closest',
                        xaxis=dict(tickmode='array', tickvals=unique_years, ticktext=unique_years, gridcolor='lightgray', gridwidth=0.5),
                        yaxis=dict(gridcolor='lightgray', gridwidth=0.5),
                        plot_bgcolor='white',
                        height=600,
                        # width=900, # Use container width
                        margin=dict(l=50, r=50, t=50, b=50), # Reduced top margin
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                    )

                    # Add buttons (optional, kept from original)
                    fig_hist.update_layout(
                        updatemenus=[dict(
                            type="buttons", direction="left",
                            buttons=[
                                dict(args=[{"yaxis.type": "linear"}], label="Lineal", method="relayout"),
                                dict(args=[{"yaxis.type": "log"}], label="Log", method="relayout")
                            ],
                            pad={"r": 10, "t": 10}, showactive=True, x=0.1, xanchor="left", y=1.1, yanchor="top"
                        )]
                    )

                    st.plotly_chart(fig_hist, use_container_width=True)

                    # Display Table
                    st.divider()
                    st.subheader("Tabla de Inauguraciones por Año (desde 2010)")
                    tabla_historica = df_agrupado.pivot_table(
                        values='Cantidad', index='Año', columns=COL_NIVEL_COMPLEJIDAD,
                        aggfunc='sum', fill_value=0
                    ).astype(int).sort_index()
                    st.dataframe(tabla_historica, use_container_width=True)

                else:
                    st.warning("No hay datos suficientes para generar el gráfico histórico con los filtros seleccionados.")
            except Exception as e:
                st.error(f"Error al procesar los datos históricos: {str(e)}")
                st.exception(e) # Show traceback for debugging if needed
    else:
        st.warning(f"Faltan columnas '{COL_FECHA_INICIO}' o '{COL_NIVEL_COMPLEJIDAD}' para el análisis histórico.")


# --- Tab 5: Datos Brutos ---
with tab5:
    st.subheader("Muestra de Datos Filtrados")
    st.info(f"""
        A continuación se muestra una muestra de los **{len(df_filtered)}** registros filtrados.
        Puede descargar el conjunto completo usando el botón.
    """)

    if not df_filtered.empty:
        with st.spinner('Preparando visualización de datos...'):
            cols_to_show = [
                COL_NOMBRE, COL_REGION, COL_COMUNA, COL_TIPO_ESTAB,
                COL_SISTEMA, COL_NIVEL_ATENCION, COL_URGENCIA
            ]
            # Filter columns that actually exist in the filtered data
            cols_exist = [col for col in cols_to_show if col in df_filtered.columns]

            if cols_exist:
                st.dataframe(
                    df_filtered[cols_exist].head(10), # Display only existing columns
                    hide_index=True, # Often preferred for display tables
                    use_container_width=True
                )
            else:
                st.dataframe(df_filtered.head(10), hide_index=True, use_container_width=True) # Fallback

        # Download Button
        csv_data = df_filtered.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="Descargar datos filtrados (CSV)",
            data=csv_data,
            file_name='establecimientos_salud_filtrados.csv',
            mime='text/csv',
        )
    else:
        st.warning("No hay datos para mostrar o descargar.")


# --- Footer ---
st.markdown("---")
st.markdown("""
**Análisis de Establecimientos de Salud en Chile** | Datos del Ministerio de Salud

Desarrollado por: Rodrigo Muñoz Soto
📧 munozsoto.rodrigo@gmail.com | 🔗 [GitHub: rodrigooig](https://github.com/rodrigooig) | 💼 [LinkedIn](https://www.linkedin.com/in/munozsoto-rodrigo/)
""")
# Version removed as it might become outdated, keep it in comments or config if needed.
# The CSS already hides the default Streamlit footer 