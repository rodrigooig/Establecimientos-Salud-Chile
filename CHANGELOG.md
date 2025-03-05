# Changelog

Todas las modificaciones notables a este proyecto serán documentadas en este archivo.

## [0.0.2] - 2024-02-25

### Añadido
- Mapa interactivo con Folium para visualizar la distribución geográfica de establecimientos
- Gráfico de barras apiladas por sistema de salud (Público, Privado, Otros)
- Script de limpieza de datos (`clean_data.py`) para normalización de texto y estandarización
- Dataset limpio y normalizado (`establecimientos_cleaned.csv`)
- Nuevas dependencias: Folium para visualización de mapas

### Modificado
- Actualización de visualizaciones para usar datos normalizados
- Mejora en la categorización de sistemas de salud
- Documentación actualizada con proceso de limpieza de datos

### Técnico
- Normalización de nombres de regiones y establecimientos
- Estandarización de mayúsculas/minúsculas en palabras clave
- Limpieza de espacios y caracteres especiales
- Optimización del proceso de carga de datos

## [0.0.1] - 2024-02-24

### Añadido
- Primera versión de la aplicación Streamlit
- Visualización básica de datos de establecimientos de salud
- Gráficos de distribución por región
- Filtros básicos de datos
- Estructura inicial del proyecto 