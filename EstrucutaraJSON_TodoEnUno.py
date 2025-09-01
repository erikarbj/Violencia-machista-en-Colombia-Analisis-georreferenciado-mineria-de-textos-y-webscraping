import pandas as pd
import json

def procesar_varios_json_a_csv(archivos_json, archivo_csv_salida):
    """
    Convierte varios archivos JSON en un solo CSV combinado.
    Cada JSON debe tener el mismo formato estructurado.
    """
    registros_totales = []

    for archivo_json in archivos_json:
        # Leer el archivo JSON
        with open(archivo_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        # Procesar cada registro del JSON
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

            # Añadir todos los tokens si existen
            if "token" in item:
                registro.update(item["token"])

            # Añadir registro a la lista
            registros_totales.append(registro)

    # Crear DataFrame final con todos los registros
    df_final = pd.DataFrame(registros_totales)

    # Guardar como CSV
    df_final.to_csv(archivo_csv_salida, index=False, encoding='utf-8')

    print(f"Procesados {len(registros_totales)} registros en total.")
    print(f"Archivo CSV generado: {archivo_csv_salida}")
    print(f"Total de columnas: {len(df_final.columns)}")

    return df_final


# 📂 Lista de archivos JSON a procesar (ajusta las rutas según tus archivos)
archivos_json = [
    'noticias_estandarizadas_Colombiano24082025.json',
    'noticias_estandarizadas_Heraldo_24082025.json',
    'noticias_estandarizadas_Tiempo_24082025.json',
    'noticias_estandarizadas_Universal_24082025.json',
    'noticias_estandarizadas_Espectador_24082025.json'
]

# 🚀 Ejecutar la conversión
df_resultante = procesar_varios_json_a_csv(archivos_json, 'noticias_tokens_combinado.csv')

# 📊 Opcional: Mostrar información del DataFrame
print("\nInformación del DataFrame:")
print(df_resultante.info())

# 👀 Opcional: Mostrar las primeras filas
print("\nPrimeras 5 filas:")
print(df_resultante.head())