import pandas as pd
import re

# Cargar el CSV de noticias
df_noticias = pd.read_csv('archivoControlElTiempo_2016_2025_Noticias.csv', header=None, names=['url', 'noticia'])

# Cargar el CSV de ciudades
df_ciudades = pd.read_csv('Departamentos_y_municipios_de_Colombia.csv')

# Crear una lista única de municipios (ciudades)
ciudades = df_ciudades['MUNICIPIO'].unique()

# Función para buscar la ciudad en el texto
def extraer_ciudad(texto):
    for ciudad in ciudades:
        # Busca coincidencia exacta, sin distinguir mayúsculas
        if re.search(r'\b' + re.escape(ciudad) + r'\b', texto, re.IGNORECASE):
            return ciudad
    return 'No identificado'

# Aplicar la función a cada fila
df_noticias['ciudad'] = df_noticias['noticia'].apply(extraer_ciudad)

# Guardar el resultado en un nuevo CSV
df_noticias.to_csv('archivoControlElTiempo_2016_2025_Ciudad.csv', index=False)

print(df_noticias[['url', 'ciudad']])
