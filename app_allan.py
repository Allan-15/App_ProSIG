import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from branca.colormap import linear

# Título de la aplicación
st.title("Eventos ciclónicos en el cantón de Pérez Zeledón")

# Fuentes de datos
pz = 'https://github.com/Allan-15/App_ProSIG/raw/refs/heads/main/datos_perez_zeledon.csv'
distritos = 'https://github.com/Allan-15/App_ProSIG/raw/refs/heads/main/distritos_pz.gpkg'


# Cargar los datos
@st.cache_data
def cargar_datos_csv():
    return pd.read_csv(pz, encoding="utf-8", delimiter=';')

@st.cache_data
def cargar_datos_geopackage():
    return gpd.read_file(distritos)

# Datos cargados
datos = cargar_datos_csv()
distritos = cargar_datos_geopackage()

# Selección de evento
eventos = ["INUNDACION", "DESLIZAMIENTO"]
evento_seleccionado = st.sidebar.selectbox("Selecciona un tipo de evento", eventos)

# Selección de año para contabilizar los eventos
anios = sorted(datos["AÑO"].unique())  # Lista de años únicos
anio_seleccionado = st.sidebar.selectbox("Selecciona un año", anios)

# Filtrar datos por evento y año
datos_filtrados = datos[(datos[evento_seleccionado] == 1) & (datos["AÑO"] == anio_seleccionado)]

#  Tabla de datos
columnas_mostrar = ["CICLON", "NOMBRE", "FECHA", "CANTON", "DISTRITO", "TOTAL_AFECTADOS", "PERDIDA_DOLARES"]
st.subheader(f"Eventos registrados: {evento_seleccionado} en {anio_seleccionado}")
if not datos_filtrados.empty:
    st.dataframe(datos_filtrados[columnas_mostrar], hide_index=True)
else:
    st.warning("No se encontraron datos para este evento.")
    st.stop()

#  Contabilizar la cantidad de eventos por año
eventos_por_anio = datos.groupby(["AÑO", evento_seleccionado]).size().reset_index(name="Cantidad")
eventos_por_anio = eventos_por_anio[eventos_por_anio[evento_seleccionado] == 1]

# Gráfico interactivo de eventos por año
grafico_eventos = px.bar(
    eventos_por_anio,
    x="AÑO",
    y="Cantidad",
    color=evento_seleccionado,
    title=f"Cantidad de {evento_seleccionado} por año",
    labels={"Cantidad": f"Cantidad de {evento_seleccionado}", "AÑO": "Año"},
    color_continuous_scale="Viridis"
)
st.plotly_chart(grafico_eventos)

# Mapa interactivo
# Preparar datos para el mapa: cantidad de eventos por distrito
cantidad_eventos_por_distrito = datos_filtrados.groupby("DISTRITO")[evento_seleccionado].sum().reset_index()
# Hacer merge con el geopackage de distritos
distritos = distritos.merge(
    cantidad_eventos_por_distrito,
    how="left",
    left_on="distrito",
    right_on="DISTRITO"
)
distritos[evento_seleccionado] = distritos[evento_seleccionado].fillna(0)

# Crear el mapa
mapa = folium.Map(location=[9.39, -83.7], zoom_start=10)  # Centrado en Pérez Zeledón
colormap = linear.YlOrRd_09.scale(
    distritos[evento_seleccionado].min(),
    distritos[evento_seleccionado].max()
)

folium.GeoJson(
    distritos,
    style_function=lambda feature: {
        "fillColor": colormap(feature["properties"][evento_seleccionado]),
        "color": "black",
        "weight": 0.5,
        "fillOpacity": 0.7,
    },
    tooltip=folium.features.GeoJsonTooltip(
        fields=["distrito", evento_seleccionado],
        aliases=["Distrito:", f"Cantidad de {evento_seleccionado}:"],
    )
).add_to(mapa)

colormap.caption = f"Cantidad de {evento_seleccionado}"
colormap.add_to(mapa)

st.subheader(f"Mapa interactivo de cantidad de {evento_seleccionado} por distrito ({evento_seleccionado} en {anio_seleccionado})")
folium_static(mapa)
