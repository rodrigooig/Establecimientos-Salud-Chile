# Changelog

Todas las modificaciones notables a este proyecto serán documentadas en este archivo.

## [0.0.2] - 2024-03-19

### Cambiado
- Mejorado el gráfico de distribución geográfica:
  - Implementado gráfico de barras apiladas para mostrar la distribución por sistema de salud
  - Agrupados los sistemas de salud en tres categorías: Público, Privado y Otros
  - Añadidos colores distintivos para cada categoría (verde para Público, rojo para Privado, gris para Otros)
- Actualizada la visualización del mapa con marcadores agrupados y círculos de tamaño variable
- Actualizadas las dependencias:
  - Añadido folium>=0.14.0
  - Añadido streamlit-folium>=0.13.0

## [0.0.1] - 2024-03-19

### Añadido
- Primera versión de la aplicación
- Visualización de datos de establecimientos de salud
- Filtros interactivos
- Gráficos de distribución geográfica
- Análisis por tipo de establecimiento
- Análisis por nivel de atención
- Vista de datos brutos 