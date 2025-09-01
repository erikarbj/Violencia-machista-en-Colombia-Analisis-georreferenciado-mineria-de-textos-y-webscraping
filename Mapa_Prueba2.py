import pandas as pd
import folium
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import unicodedata

# 1. Cargar datos desde Excel
archivo_excel = "datos_corregidos_unificadosmd_normalizadoFinal.xlsx"
df = pd.read_excel(archivo_excel)
df.columns = df.columns.str.strip()
print("Columnas detectadas:", df.columns.tolist())

# 2. Filtrar solo Colombia
df = df[df["pais"].str.lower() == "colombia"]

# 3. Calcular total de delitos (desde columna H en adelante, índice base 0: columna 7)
col_inicio_delitos = 7
df["total_delitos"] = df.iloc[:, col_inicio_delitos:].sum(axis=1)

# 4. Agrupar por MUNICIPIO (columna F, que es la columna índice 5)
df_municipios = df.groupby("Municipio", as_index=False)["total_delitos"].sum()
print("Totales por municipio:")
print(df_municipios.head())

# 5. Normalizar nombres de municipios para geocodificación
def normalize(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode().upper()

df_municipios["municipio_norm"] = df_municipios["Municipio"].apply(normalize)

# 6. Geocodificar municipios (obtener latitud y longitud)
geolocator = Nominatim(user_agent="colombia_delitos_map")

def geocodificar_municipio(nombre):
    try:
        # Buscar como "Municipio, Colombia"
        location = geolocator.geocode(f"{nombre}, Colombia", timeout=10)
        if location:
            return pd.Series([location.latitude, location.longitude])
        else:
            print(f"⚠️ No se encontró: {nombre}")
            return pd.Series([None, None])
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"❌ Error con {nombre}: {e}")
        return pd.Series([None, None])

# Aplicar geocodificación con pausas para no saturar la API
print("Iniciando geocodificación de municipios...")
coords = df_municipios["Municipio"].apply(geocodificar_municipio)
df_municipios["lat"] = coords[0]
df_municipios["lon"] = coords[1]

# Filtrar municipios sin coordenadas
df_municipios = df_municipios.dropna(subset=["lat", "lon"]).reset_index(drop=True)
print(f"✅ {len(df_municipios)} municipios geocodificados con éxito.")

# 7. Crear mapa centrado en Colombia
m = folium.Map(location=[4.5709, -74.2973], zoom_start=6, tiles="OpenStreetMap")

# 8. Añadir marcadores para cada municipio
for _, row in df_municipios.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=max(3, row["total_delitos"] / 50),  # Tamaño proporcional a delitos
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.6,
        popup=f"<b>{row['Municipio']}</b><br>Total delitos: {int(row['total_delitos'])}",
        tooltip=row["Municipio"]
    ).add_to(m)

# 9. Guardar el mapa
ruta_html = "mapa_colombia_municipios_delitos.html"
m.save(ruta_html)
print(f"✅ Mapa generado exitosamente: {ruta_html}")