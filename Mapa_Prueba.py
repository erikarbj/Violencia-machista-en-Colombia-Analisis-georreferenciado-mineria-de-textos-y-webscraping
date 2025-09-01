import pandas as pd
import folium
import geopandas as gpd
import requests
import unicodedata

# 1. Cargar datos desde Excel
archivo_excel = "datos_corregidos_unificadosmd_normalizadoFinal.xlsx"
df = pd.read_excel(archivo_excel)
df.columns = df.columns.str.strip()
print("Columnas detectadas:", df.columns.tolist())

# 2. Filtrar solo Colombia
df = df[df["pais"].str.lower() == "colombia"]

# 3. Calcular total de delitos (desde columna H en adelante)
col_inicio_delitos = 7  # índice base 0
df["total_delitos"] = df.iloc[:, col_inicio_delitos:].sum(axis=1)

# Agrupar por Departamento
df_mapa = df.groupby("Departamento", as_index=False)["total_delitos"].sum()
print("Totales por departamento:")
print(df_mapa.head())

# 4. Descargar GeoJSON de departamentos
url_geojson = (
    "https://raw.githubusercontent.com/santiblanko/colombia.geojson/master/depto.json"
)
archivo_geojson = "depto_colombia.json"
r = requests.get(url_geojson)
r.raise_for_status()
with open(archivo_geojson, "wb") as f:
    f.write(r.content)
print("GeoJSON de departamentos descargado.")

# 5. Leer el GeoJSON con GeoPandas
gdf = gpd.read_file(archivo_geojson)
print("GeoJSON cargado. Columnas:", gdf.columns.tolist())

# 6. Normalizar nombres: eliminar tildes y uniformar mayúsculas
def normalize(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode().upper()

df_mapa["dept_norm"] = df_mapa["Departamento"].apply(normalize)
if "NOMBRE_DPT" in gdf.columns:
    gdf["dept_norm"] = gdf["NOMBRE_DPT"].apply(normalize)
elif "DEPARTAMENT" in gdf.columns:
    gdf["dept_norm"] = gdf["DEPARTAMENT"].apply(normalize)
else:
    gdf["dept_norm"] = gdf.iloc[:, 0].apply(normalize)

# 7. Unir datos
gdf = gdf.merge(df_mapa, on="dept_norm", how="left")
gdf["total_delitos"] = gdf["total_delitos"].fillna(0)

# 8. Crear mapa coroplético
m = folium.Map(location=[4.5709, -74.2973], zoom_start=6)
folium.Choropleth(
    geo_data=gdf,
    data=gdf,
    columns=["dept_norm", "total_delitos"],
    key_on="feature.properties.dept_norm",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Total de delitos reportados"
).add_to(m)

for _, row in gdf.iterrows():
    folium.Marker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        popup=f"{row.get('Departamento', row.get('NOMBRE_DPT', row.get(gdf.columns[0])))}: {int(row['total_delitos'])} delitos",
        icon=folium.Icon(color="red" if row["total_delitos"] > 0 else "gray")
    ).add_to(m)

# 9. Guardar HTML del mapa
ruta_html = "mapa_colombia_delitos.html"
m.save(ruta_html)
print(f"Mapa generado exitosamente: {ruta_html}")