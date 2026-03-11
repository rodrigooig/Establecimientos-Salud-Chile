import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
COL_DEPENDENCIA = "DependenciaAdministrativa"
COL_TIPO_ATENCION = "TipoAtencionEstabGlosa"
COL_TIPO_URGENCIA = "TipoUrgencia"

SYSTEM_COLORS = {'Público': '#2ecc71', 'Privado': '#e74c3c', 'Otros': '#95a5a6'}
COMPLEXITY_COLORS = {
    'Alta Complejidad': '#e74c3c',
    'Mediana Complejidad': '#f39c12',
    'Baja Complejidad': '#2ecc71'
}
URGENCY_COLORS = {
    'Urgencia Hospitalaria (UEH)': '#e74c3c',
    'Urgencia Ambulatoria (SAPU)': '#f39c12',
    'Urgencia Ambulatoria (SAR)': '#3498db',
    'Urgencia Ambulatoria (SUR)': '#2ecc71',
    'Otros': '#95a5a6',
}
DEPENDENCY_COLORS = {
    'Municipal': '#3498db',
    'Privado': '#e74c3c',
    'Servicio de Salud': '#2ecc71',
    'Otro': '#95a5a6',
}
DEFAULT_PLOTLY_COLORS = px.colors.qualitative.Pastel

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
    try:
        try:
            df = pd.read_csv(path, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(path, sep=';', encoding='latin1')
        return df, None
    except Exception as e:
        return None, str(e)


def create_multiselect_filter(df, column_name, label, key):
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
    df_filtered = df.copy()
    for column, selected_values in filters.items():
        if selected_values:
            df_filtered = df_filtered[df_filtered[column].isin(selected_values)]
    return df_filtered


def classify_sistema(val):
    return val if val in ('Público', 'Privado') else 'Otros'


def simplify_dependency(val):
    if val in ('Municipal', 'Privado', 'Servicio de Salud'):
        return val
    return 'Otro'


def visualizar_mapa(map_data):
    if not all(col in map_data.columns for col in [COL_LAT, COL_LON]):
        st.warning(f"Faltan columnas '{COL_LAT}' o '{COL_LON}' para el mapa.")
        return

    map_data_valid = map_data.dropna(subset=[COL_LAT, COL_LON])
    if map_data_valid.empty:
        st.warning("No hay datos con coordenadas geográficas válidas.")
        return

    if COL_SISTEMA in map_data_valid.columns:
        map_data_valid = map_data_valid.assign(_sistema=map_data_valid[COL_SISTEMA].map(classify_sistema))
    else:
        map_data_valid = map_data_valid.assign(_sistema='Otros')

    # Build hover text
    hover_parts = []
    if COL_NOMBRE in map_data_valid.columns:
        hover_parts.append('<b>' + map_data_valid[COL_NOMBRE].astype(str) + '</b>')
    if COL_TIPO_ESTAB in map_data_valid.columns:
        hover_parts.append(map_data_valid[COL_TIPO_ESTAB].astype(str))
    if COL_COMUNA in map_data_valid.columns and COL_REGION in map_data_valid.columns:
        hover_parts.append(map_data_valid[COL_COMUNA].astype(str) + ', ' + map_data_valid[COL_REGION].astype(str))
    hover_text = '<br>'.join(hover_parts) if hover_parts else None

    fig_map = go.Figure()

    for sistema, color in SYSTEM_COLORS.items():
        df_sys = map_data_valid[map_data_valid['_sistema'] == sistema]
        if df_sys.empty:
            continue
        fig_map.add_trace(go.Scattermap(
            lat=df_sys[COL_LAT],
            lon=df_sys[COL_LON],
            mode='markers',
            marker=dict(size=7, color=color, opacity=0.7),
            name=sistema,
            hovertext=hover_text[df_sys.index] if hover_text is not None else None,
            hoverinfo='text',
            cluster=dict(enabled=True, maxzoom=12, size=40, step=3,
                         color=color, opacity=0.8),
        ))

    fig_map.update_layout(
        map=dict(style="open-street-map", center=dict(lat=-33.45, lon=-70.65), zoom=3.5),
        height=650,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            title="Sistema de Salud",
            orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.8)",
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True)


# --- Main App Logic ---

# Load Data
with st.spinner('Cargando datos de establecimientos de salud...'):
    df, error = load_data()

if error:
    st.error(f"Error al cargar los datos: {error}")
    st.stop()

# Sidebar
st.sidebar.title("Bienvenido")
st.sidebar.caption("Explora datos de establecimientos de salud en Chile.")
st.sidebar.caption("Código fuente en [GitHub](https://github.com/rodrigooig/establecimientos-salud-chile)")
st.sidebar.markdown("### Información del Dataset")
st.sidebar.info(f"""
- **Registros totales:** {len(df):,}
- **Fuente:** Ministerio de Salud de Chile
""")

# Sidebar Filters
df_filtered = df
if not df.empty:
    st.sidebar.markdown("### Filtros")

    if st.sidebar.button("Reiniciar Filtros"):
        keys_to_reset = ['regiones_sel', 'tipos_sel', 'sistemas_sel', 'estados_sel', 'dependencia_sel']
        for key in keys_to_reset:
            st.session_state[key] = []
        st.rerun()

    st.sidebar.markdown("---")

    filters_selected = {
        COL_REGION: create_multiselect_filter(df, COL_REGION, "Regiones", 'regiones_sel'),
        COL_TIPO_ESTAB: create_multiselect_filter(df, COL_TIPO_ESTAB, "Tipos de Establecimiento", 'tipos_sel'),
        COL_SISTEMA: create_multiselect_filter(df, COL_SISTEMA, "Sistema de Salud", 'sistemas_sel'),
        COL_ESTADO: create_multiselect_filter(df, COL_ESTADO, "Estado de Funcionamiento", 'estados_sel'),
        COL_DEPENDENCIA: create_multiselect_filter(df, COL_DEPENDENCIA, "Dependencia Administrativa", 'dependencia_sel'),
    }

    df_filtered = apply_filters(df, filters_selected)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Establecimientos filtrados:** {len(df_filtered):,}")

# --- Main Panel ---
st.title("Establecimientos de Salud en Chile")

# --- KPIs ---
if not df_filtered.empty:
    total_filtered = len(df_filtered)

    # Row 1: Core metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Establecimientos", f"{total_filtered:,}")
    with col2:
        if COL_TIPO_URGENCIA in df_filtered.columns:
            urg_count = df_filtered[df_filtered[COL_TIPO_URGENCIA].isin(
                [k for k in URGENCY_COLORS if k != 'Otros']
            )].shape[0]
            if urg_count == 0:
                urg_count = df_filtered[COL_URGENCIA].value_counts().get("SI", 0) if COL_URGENCIA in df_filtered.columns else 0
            urg_perc = (urg_count / total_filtered * 100) if total_filtered else 0
            st.metric("Servicios de Urgencia", f"{urg_count:,} ({urg_perc:.1f}%)")
        else:
            st.metric("Servicios de Urgencia", "N/A")
    with col3:
        if COL_SISTEMA in df_filtered.columns:
            public_count = df_filtered[df_filtered[COL_SISTEMA] == "Público"].shape[0]
            public_perc = (public_count / total_filtered * 100) if total_filtered else 0
            st.metric("Sistema Público", f"{public_count:,} ({public_perc:.1f}%)")
        else:
            st.metric("Sistema Público", "N/A")

    # Row 2: Structural metrics
    col4, col5, col6 = st.columns(3)
    with col4:
        if COL_TIPO_ATENCION in df_filtered.columns:
            amb = df_filtered[df_filtered[COL_TIPO_ATENCION].str.contains('Abierta', case=False, na=False)].shape[0]
            amb_perc = (amb / total_filtered * 100) if total_filtered else 0
            st.metric("Atención Ambulatoria", f"{amb:,} ({amb_perc:.1f}%)")
        else:
            st.metric("Atención Ambulatoria", "N/A")
    with col5:
        if COL_COMUNA in df_filtered.columns and COL_URGENCIA in df_filtered.columns:
            total_comunas = df[COL_COMUNA].nunique()
            comunas_urg = df_filtered[df_filtered[COL_URGENCIA] == 'SI'][COL_COMUNA].nunique()
            sin_cobertura = total_comunas - comunas_urg
            st.metric("Cobertura Comunal de Urgencia", f"{comunas_urg} / {total_comunas}", delta=f"-{sin_cobertura} sin cobertura", delta_color="inverse")
        else:
            st.metric("Cobertura Comunal de Urgencia", "N/A")
    with col6:
        if COL_DEPENDENCIA in df_filtered.columns:
            mun = df_filtered[df_filtered[COL_DEPENDENCIA] == 'Municipal'].shape[0]
            mun_perc = (mun / total_filtered * 100) if total_filtered else 0
            st.metric("Dependencia Municipal", f"{mun:,} ({mun_perc:.1f}%)")
        else:
            st.metric("Dependencia Municipal", "N/A")
else:
    st.warning("No hay datos para mostrar con los filtros seleccionados.")

# --- Tabs ---
tab_titles = ["Panorama Nacional", "Evolución Histórica", "Red de Urgencias", "Explorador de Datos"]
tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

# =====================================================
# TAB 1: PANORAMA NACIONAL
# =====================================================
with tab1:
    st.subheader("Distribución Geográfica")
    visualizar_mapa(df_filtered)

    st.divider()

    # --- Region x System stacked bar ---
    st.subheader('Establecimientos por Región y Sistema de Salud')
    if all(c in df_filtered.columns for c in [COL_REGION, COL_SISTEMA]):
        df_plot = df_filtered.copy()
        df_plot[COL_SISTEMA] = df_plot[COL_SISTEMA].map(classify_sistema)

        region_sistema = pd.crosstab(df_plot[COL_REGION], df_plot[COL_SISTEMA]).reset_index()
        for col in SYSTEM_COLORS.keys():
            if col not in region_sistema.columns:
                region_sistema[col] = 0

        ordered_cols = [COL_REGION] + list(SYSTEM_COLORS.keys())
        region_sistema = region_sistema[ordered_cols]
        region_total_counts = df_filtered[COL_REGION].value_counts()
        region_sistema = region_sistema.set_index(COL_REGION).loc[region_total_counts.index].reset_index()

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
            yaxis={'categoryorder': 'total ascending'},
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title='Sistema de Salud'),
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis_title='Cantidad de Establecimientos',
            yaxis_title='Región'
        )
        st.plotly_chart(fig_region_sys, use_container_width=True)

    st.divider()

    # --- Gobernanza: Region x Dependency ---
    st.subheader('Gobernanza: Dependencia Administrativa por Región')
    if all(c in df_filtered.columns for c in [COL_REGION, COL_DEPENDENCIA]):
        df_gov = df_filtered.copy()
        df_gov['_dep'] = df_gov[COL_DEPENDENCIA].apply(simplify_dependency)

        region_dep = pd.crosstab(df_gov[COL_REGION], df_gov['_dep']).reset_index()
        for col in DEPENDENCY_COLORS.keys():
            if col not in region_dep.columns:
                region_dep[col] = 0

        ordered_dep_cols = [COL_REGION] + list(DEPENDENCY_COLORS.keys())
        region_dep = region_dep[[c for c in ordered_dep_cols if c in region_dep.columns]]
        region_dep['_total'] = region_dep.select_dtypes(include='number').sum(axis=1)
        region_dep = region_dep.sort_values('_total', ascending=True).drop(columns='_total')

        fig_gov = go.Figure()
        for dep_name in DEPENDENCY_COLORS.keys():
            if dep_name in region_dep.columns:
                fig_gov.add_trace(go.Bar(
                    name=dep_name,
                    y=region_dep[COL_REGION],
                    x=region_dep[dep_name],
                    orientation='h',
                    marker_color=DEPENDENCY_COLORS[dep_name],
                    hovertemplate=f'<b>%{{y}}</b><br>{dep_name}: <b>%{{x}}</b><extra></extra>'
                ))

        fig_gov.update_layout(
            barmode='stack',
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title='Dependencia'),
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis_title='Cantidad de Establecimientos',
            yaxis_title='Región'
        )
        st.plotly_chart(fig_gov, use_container_width=True)

    st.divider()

    # --- Distribución por Nivel de Atención y Complejidad (side by side) ---
    st.subheader("Niveles de Atención y Complejidad")
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        if COL_NIVEL_ATENCION in df_filtered.columns:
            counts_na = df_filtered[COL_NIVEL_ATENCION].value_counts().reset_index()
            counts_na.columns = ['Label', 'Cantidad']
            fig_na = go.Figure(data=[go.Pie(
                labels=counts_na['Label'], values=counts_na['Cantidad'],
                hole=0.4,
                marker=dict(colors=DEFAULT_PLOTLY_COLORS, line=dict(color='white', width=2)),
                textinfo='label+percent', textposition='outside', textfont=dict(size=11),
                hovertemplate='<b>%{label}</b><br>Cantidad: <b>%{value}</b><br>%{percent}<extra></extra>',
            )])
            fig_na.update_layout(
                title={'text': 'Nivel de Atención', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'font': dict(size=16)},
                showlegend=False, height=420,
                annotations=[dict(text="Atención", x=0.5, y=0.5, font=dict(size=13), showarrow=False)],
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig_na, use_container_width=True)

    with col_d2:
        if COL_NIVEL_COMPLEJIDAD in df_filtered.columns:
            counts_nc = df_filtered[COL_NIVEL_COMPLEJIDAD].value_counts().reset_index()
            counts_nc.columns = ['Label', 'Cantidad']
            fig_nc = go.Figure(data=[go.Pie(
                labels=counts_nc['Label'], values=counts_nc['Cantidad'],
                hole=0.4,
                marker=dict(colors=DEFAULT_PLOTLY_COLORS, line=dict(color='white', width=2)),
                textinfo='label+percent', textposition='outside', textfont=dict(size=11),
                hovertemplate='<b>%{label}</b><br>Cantidad: <b>%{value}</b><br>%{percent}<extra></extra>',
            )])
            fig_nc.update_layout(
                title={'text': 'Nivel de Complejidad', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'font': dict(size=16)},
                showlegend=False, height=420,
                annotations=[dict(text="Complejidad", x=0.5, y=0.5, font=dict(size=13), showarrow=False)],
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig_nc, use_container_width=True)


# =====================================================
# TAB 2: EVOLUCIÓN HISTÓRICA
# =====================================================
with tab2:
    st.subheader("Inauguración de Establecimientos por Año")
    st.info("Evolución anual de nuevos establecimientos. Ajusta el rango con el slider.")

    if all(c in df_filtered.columns for c in [COL_FECHA_INICIO, COL_NIVEL_COMPLEJIDAD]):
        df_hist = df_filtered.copy()
        df_hist[COL_FECHA_INICIO] = pd.to_datetime(df_hist[COL_FECHA_INICIO], errors='coerce')
        df_hist = df_hist.dropna(subset=[COL_FECHA_INICIO])
        df_hist['Año'] = df_hist[COL_FECHA_INICIO].dt.year.astype(int)

        if not df_hist.empty:
            min_year = max(int(df_hist['Año'].min()), 2000)
            max_year = int(df_hist['Año'].max())

            year_range = st.slider("Rango de años", min_value=min_year, max_value=max_year, value=(min_year, max_year))
            df_hist = df_hist[(df_hist['Año'] >= year_range[0]) & (df_hist['Año'] <= year_range[1])]

            niveles_complejidad = list(COMPLEXITY_COLORS.keys())
            df_hist_c = df_hist[df_hist[COL_NIVEL_COMPLEJIDAD].isin(niveles_complejidad)]

            view_mode = st.radio("Vista", ["Anual", "Acumulado"], horizontal=True)

            if not df_hist_c.empty:
                df_agrupado = df_hist_c.groupby(['Año', COL_NIVEL_COMPLEJIDAD]).size().reset_index(name='Cantidad')

                if view_mode == "Acumulado":
                    df_agrupado = df_agrupado.sort_values('Año')
                    df_agrupado['Cantidad'] = df_agrupado.groupby(COL_NIVEL_COMPLEJIDAD)['Cantidad'].cumsum()

                fig_hist = go.Figure()
                for nivel in niveles_complejidad:
                    df_nivel = df_agrupado[df_agrupado[COL_NIVEL_COMPLEJIDAD] == nivel]
                    if not df_nivel.empty:
                        mode = 'lines+markers' if view_mode == "Acumulado" else 'lines+markers+text'
                        fig_hist.add_trace(go.Scatter(
                            x=df_nivel['Año'], y=df_nivel['Cantidad'],
                            mode=mode, name=nivel,
                            line=dict(color=COMPLEXITY_COLORS.get(nivel, '#3498db'), width=3),
                            marker=dict(size=8),
                            text=df_nivel['Cantidad'] if view_mode == "Anual" else None,
                            textposition='top center',
                            hovertemplate=f'<b>%{{x}}</b><br>{nivel}: <b>%{{y}}</b><extra></extra>'
                        ))

                y_title = 'Acumulado de Establecimientos' if view_mode == "Acumulado" else 'Establecimientos Inaugurados'
                unique_years = sorted(df_hist_c['Año'].unique())
                fig_hist.update_layout(
                    xaxis_title='Año', yaxis_title=y_title,
                    hovermode='closest',
                    xaxis=dict(tickmode='array', tickvals=unique_years, ticktext=unique_years, gridcolor='lightgray'),
                    yaxis=dict(gridcolor='lightgray'),
                    plot_bgcolor='white', height=550,
                    margin=dict(l=50, r=50, t=50, b=50),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

                # Table
                st.divider()
                st.subheader("Detalle por Año")
                tabla = df_agrupado.pivot_table(
                    values='Cantidad', index='Año', columns=COL_NIVEL_COMPLEJIDAD,
                    aggfunc='sum', fill_value=0
                ).astype(int).sort_index()
                st.dataframe(tabla, use_container_width=True)
            else:
                st.warning("No hay datos de complejidad válidos para el rango seleccionado.")
        else:
            st.warning("No hay registros con fechas de inicio válidas.")
    else:
        st.warning(f"Faltan columnas requeridas para el análisis histórico.")


# =====================================================
# TAB 3: RED DE URGENCIAS
# =====================================================
with tab3:
    st.subheader("Red de Servicios de Urgencia")
    st.info("Análisis de cobertura y tipología de la red de urgencias a nivel nacional.")

    if COL_TIPO_URGENCIA in df_filtered.columns:
        # Filter to actual urgency services
        urgency_types = [k for k in URGENCY_COLORS if k != 'Otros']
        df_urg = df_filtered[df_filtered[COL_TIPO_URGENCIA].isin(urgency_types)].copy()

        # Also include minor types grouped as "Otros"
        minor_urgency = df_filtered[
            (~df_filtered[COL_TIPO_URGENCIA].isin(urgency_types)) &
            (df_filtered[COL_TIPO_URGENCIA] != 'No Aplica') &
            (df_filtered[COL_TIPO_URGENCIA] != 'SIN DATO') &
            (df_filtered[COL_TIPO_URGENCIA].notna())
        ].copy()
        minor_urgency[COL_TIPO_URGENCIA] = 'Otros'
        df_urg_all = pd.concat([df_urg, minor_urgency], ignore_index=True)

        total_urg = len(df_urg_all)

        # Mini KPIs
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Total Servicios de Urgencia", f"{total_urg:,}")
        with k2:
            total_comunas = df[COL_COMUNA].nunique()
            comunas_con = df_filtered[df_filtered[COL_URGENCIA] == 'SI'][COL_COMUNA].nunique()
            comunas_sin = total_comunas - comunas_con
            st.metric("Comunas Sin Cobertura", f"{comunas_sin}", delta=f"de {total_comunas} totales", delta_color="inverse")
        with k3:
            ueh = df_urg_all[df_urg_all[COL_TIPO_URGENCIA] == 'Urgencia Hospitalaria (UEH)'].shape[0]
            sapu = df_urg_all[df_urg_all[COL_TIPO_URGENCIA] == 'Urgencia Ambulatoria (SAPU)'].shape[0]
            ratio = f"{ueh/sapu:.2f}" if sapu > 0 else "N/A"
            st.metric("Ratio Hospitalaria / SAPU", ratio, help="Relación entre urgencias hospitalarias (UEH) y atención primaria (SAPU)")

        st.divider()

        # --- Urgency types by region (stacked bar) ---
        st.subheader("Tipos de Urgencia por Región")
        if COL_REGION in df_urg_all.columns and not df_urg_all.empty:
            region_urg = pd.crosstab(df_urg_all[COL_REGION], df_urg_all[COL_TIPO_URGENCIA]).reset_index()

            for col in URGENCY_COLORS.keys():
                if col not in region_urg.columns:
                    region_urg[col] = 0

            region_urg['_total'] = region_urg.select_dtypes(include='number').sum(axis=1)
            region_urg = region_urg.sort_values('_total', ascending=True).drop(columns='_total')

            fig_urg_region = go.Figure()
            for urg_type, color in URGENCY_COLORS.items():
                if urg_type in region_urg.columns:
                    fig_urg_region.add_trace(go.Bar(
                        name=urg_type.replace('Urgencia ', '').replace('Ambulatoria ', ''),
                        y=region_urg[COL_REGION],
                        x=region_urg[urg_type],
                        orientation='h',
                        marker_color=color,
                        hovertemplate=f'<b>%{{y}}</b><br>{urg_type}: <b>%{{x}}</b><extra></extra>'
                    ))

            fig_urg_region.update_layout(
                barmode='stack', height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title='Tipo de Urgencia'),
                margin=dict(l=50, r=50, t=50, b=50),
                xaxis_title='Cantidad', yaxis_title='Región',
            )
            st.plotly_chart(fig_urg_region, use_container_width=True)

        st.divider()

        # --- Urgency type donut ---
        col_u1, col_u2 = st.columns([1, 1])
        with col_u1:
            st.subheader("Distribución por Tipo")
            urg_counts = df_urg_all[COL_TIPO_URGENCIA].value_counts().reset_index()
            urg_counts.columns = ['Tipo', 'Cantidad']
            colors_list = [URGENCY_COLORS.get(t, '#95a5a6') for t in urg_counts['Tipo']]

            fig_urg_donut = go.Figure(data=[go.Pie(
                labels=urg_counts['Tipo'].str.replace('Urgencia ', '').str.replace('Ambulatoria ', ''),
                values=urg_counts['Cantidad'],
                hole=0.4,
                marker=dict(colors=colors_list, line=dict(color='white', width=2)),
                textinfo='label+percent', textposition='outside', textfont=dict(size=11),
                hovertemplate='<b>%{label}</b><br>Cantidad: <b>%{value}</b><br>%{percent}<extra></extra>',
            )])
            fig_urg_donut.update_layout(
                showlegend=False, height=400,
                annotations=[dict(text=f"{total_urg}", x=0.5, y=0.5, font=dict(size=18, weight='bold'), showarrow=False)],
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_urg_donut, use_container_width=True)

        # --- Coverage gap table ---
        with col_u2:
            st.subheader("Comunas Sin Urgencia")
            if COL_COMUNA in df_filtered.columns and COL_REGION in df_filtered.columns:
                todas_comunas = df[[COL_COMUNA, COL_REGION]].drop_duplicates()
                comunas_con_urg = df_filtered[df_filtered[COL_URGENCIA] == 'SI'][COL_COMUNA].unique()
                comunas_sin_urg = todas_comunas[~todas_comunas[COL_COMUNA].isin(comunas_con_urg)]
                comunas_sin_urg = comunas_sin_urg.sort_values([COL_REGION, COL_COMUNA])

                if not comunas_sin_urg.empty:
                    st.caption(f"{len(comunas_sin_urg)} comunas sin servicio de urgencia")
                    st.dataframe(
                        comunas_sin_urg.rename(columns={COL_REGION: 'Región', COL_COMUNA: 'Comuna'}),
                        hide_index=True, use_container_width=True, height=340,
                    )
                else:
                    st.success("Todas las comunas cuentan con al menos un servicio de urgencia.")
    else:
        st.warning("No hay datos de tipo de urgencia disponibles.")


# =====================================================
# TAB 4: EXPLORADOR DE DATOS
# =====================================================
with tab4:
    st.subheader("Explorador de Datos")

    # Top 20 types in expander
    with st.expander("Top 20 Tipos de Establecimiento", expanded=False):
        if COL_TIPO_ESTAB in df_filtered.columns:
            counts = df_filtered[COL_TIPO_ESTAB].value_counts().reset_index()
            counts.columns = ['Tipo de Establecimiento', 'Cantidad']
            total_count = len(df_filtered)
            counts['Porcentaje'] = (counts['Cantidad'] / total_count * 100)
            data_top = counts.head(20)

            fig_types = go.Figure(go.Bar(
                x=data_top['Cantidad'], y=data_top['Tipo de Establecimiento'],
                orientation='h',
                marker_color=px.colors.sequential.Blues[-2],
                text=[f'{n} ({p:.1f}%)' for n, p in zip(data_top['Cantidad'], data_top['Porcentaje'])],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Cantidad: <b>%{x}</b><extra></extra>'
            ))
            fig_types.update_layout(
                height=max(500, len(data_top) * 35),
                margin=dict(l=50, r=150, t=30, b=50),
                yaxis={'categoryorder': 'total ascending'}, showlegend=False,
                xaxis_title='Cantidad', yaxis_title='Tipo',
            )
            st.plotly_chart(fig_types, use_container_width=True)

    st.divider()

    # Data table
    st.subheader("Muestra de Datos Filtrados")
    st.caption(f"Mostrando **{len(df_filtered):,}** registros filtrados.")

    if not df_filtered.empty:
        cols_to_show = [
            COL_NOMBRE, COL_REGION, COL_COMUNA, COL_TIPO_ESTAB,
            COL_SISTEMA, COL_DEPENDENCIA, COL_TIPO_ATENCION,
            COL_NIVEL_ATENCION, COL_TIPO_URGENCIA, COL_URGENCIA
        ]
        cols_exist = [col for col in cols_to_show if col in df_filtered.columns]

        if cols_exist:
            st.dataframe(df_filtered[cols_exist], hide_index=True, use_container_width=True)
        else:
            st.dataframe(df_filtered, hide_index=True, use_container_width=True)

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

Desarrollado por: Rodrigo Muñoz Soto | [GitHub: rodrigooig](https://github.com/rodrigooig) | [LinkedIn](https://www.linkedin.com/in/munozsoto-rodrigo/)
""")
