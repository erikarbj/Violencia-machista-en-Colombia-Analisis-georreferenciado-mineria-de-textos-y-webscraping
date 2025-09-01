import pandas as pd
import json

def procesar_json_a_csv(archivo_json, archivo_csv):
    """
    Convierte un archivo JSON con múltiples registros en un CSV
    donde cada columna representa una categoría de token
    """
    
    # Leer el archivo JSON
    with open(archivo_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    # Lista para almacenar todos los registros procesados
    registros_procesados = []
    
    # Procesar cada registro
    for item in datos:
        # Crear diccionario base con los campos principales
        registro = {
            "ID_noticia": item.get("ID_noticia", ""),
            "fecha": item.get("fecha", ""),
            "diario": item.get("diario", ""),
            "país": item.get("país", ""),
            "ubicacion_noticia": item.get("ubicacion_noticia", ""),
            "enlace": item.get("enlace", "")
        }
        
        # Añadir todos los tokens
        if "token" in item:
            registro.update(item["token"])
        
        # Añadir el registro procesado a la lista
        registros_procesados.append(registro)
    
    # Crear DataFrame
    df = pd.DataFrame(registros_procesados)
    
    # Guardar como CSV
    df.to_csv(archivo_csv, index=False, encoding='utf-8')
    
    print(f"Procesados {len(registros_procesados)} registros")
    print(f"Archivo CSV generado: {archivo_csv}")
    print(f"Total de columnas: {len(df.columns)}")
    
    return df

# USO DEL SCRIPT
# Asegúrate de que tu archivo JSON tenga este formato:
# [
#   {
#     "ID_noticia": "...",
#     "fecha": "...",
#     "token": {...},
#     "diario": "...",
#     "país": "...",
#     "ubicacion_noticia": "..."
#   },
#   {
#     ... otro registro ...
#   }
# ]

# Ejecutar la conversión
df_resultante = procesar_json_a_csv('noticias_estandarizadas_ESPECTADOR_M.json', 'noticias_tokensESPECTADOR.csv')

# Opcional: Mostrar información del DataFrame
print("\nInformación del DataFrame:")
print(df_resultante.info())

# Opcional: Mostrar las primeras filas
print("\nPrimeras 5 filas:")
print(df_resultante.head())