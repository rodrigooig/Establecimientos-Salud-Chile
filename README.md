# Análisis de Establecimientos de Salud en Chile 🏥

Aplicación web interactiva que permite explorar y visualizar datos sobre establecimientos de salud en Chile, desarrollada con Streamlit.

## Demo en vivo

Puedes acceder a la versión desplegada en Streamlit Cloud aquí: [Análisis de Establecimientos de Salud](https://establecimientos-salud-chile.streamlit.app)

## Descripción

Esta aplicación analiza los datos abiertos del Ministerio de Salud de Chile sobre establecimientos de salud en el país. Permite explorar:

- Distribución geográfica por región
- Tipos de establecimientos
- Niveles de atención y complejidad
- Servicios de urgencia
- Datos detallados de cada establecimiento

## Características

- 📊 **Visualizaciones interactivas**: Gráficos y tablas dinámicas
- 🗺️ **Distribución geográfica**: Análisis por región
- 🏥 **Categorización**: Por tipo de establecimiento y nivel de atención
- 📱 **Responsive**: Adaptado a diferentes dispositivos
- 💾 **Descarga de datos**: Posibilidad de descargar los resultados

## Requisitos

- Python 3.8+
- Streamlit 1.27+
- Pandas 1.5+
- Otras dependencias listadas en `requirements.txt`

## Instalación local

1. Clona este repositorio:
   ```bash
   git clone https://github.com/rodrigooig/Establecimientos-Salud-Chile.git
   cd Establecimientos-Salud-Chile
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:
   ```bash
   streamlit run streamlit_app.py
   ```

4. Abre tu navegador en `http://localhost:8501`

## Estructura del proyecto

```
.
├── streamlit_app.py       # Aplicación principal Streamlit
├── data/                  # Directorio de datos
│   └── establecimientos_20250225.csv  # Datos de establecimientos
├── requirements.txt       # Dependencias del proyecto
├── packages.txt          # Paquetes del sistema necesarios
├── runtime.txt          # Versión de Python para el despliegue
└── README.md            # Documentación
```

## Datos

Los datos utilizados en esta aplicación son datos abiertos del Ministerio de Salud de Chile, disponibles en el [Portal de Datos Abiertos](https://datos.gob.cl/).

## Desarrollo

Para contribuir al desarrollo:

1. Crea un fork del repositorio
2. Crea una rama para tu funcionalidad: `git checkout -b nueva-funcionalidad`
3. Realiza tus cambios y haz commit: `git commit -am 'Añade nueva funcionalidad'`
4. Sube los cambios: `git push origin nueva-funcionalidad`
5. Envía un Pull Request

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## Autor

**Rodrigo Muñoz Soto**
- 📧 Email: munozsoto.rodrigo@gmail.com
- 🔗 GitHub: [@rodrigooig](https://github.com/rodrigooig)
- 💼 LinkedIn: [munozsoto-rodrigo](https://www.linkedin.com/in/munozsoto-rodrigo/)

## Contacto

Si tienes preguntas o sugerencias, no dudes en contactar al autor o abrir un issue en GitHub.

---

Desarrollado con ❤️ para el análisis de establecimientos de salud en Chile | Versión 0.0.1 