import pandas as pd

# --- Paso 1: Leer el archivo Excel (sin header automático para controlarlo)
# Asumimos que la primera fila del archivo son los títulos
df = pd.read_excel('noticias_tokens_combinado_Revisar1.xlsx', header=None)

print("Forma original del archivo:", df.shape)
print("Primeras filas antes:")
print(df.head())

# --- Paso 2: Separar encabezado (primera fila) y datos
header = df.iloc[0]  # Primera fila → títulos
data = df.iloc[1:]   # Resto → datos

print(f"\nTítulos detectados (columnas): {len(header)}")
print("Ejemplo de títulos:")
print(header.tolist()[:10], "...")

# --- Paso 3: Convertir datos a numéricos (por si hay texto o errores)
data_numeric = data.apply(pd.to_numeric, errors='coerce')  # Convierte a número, no válidos → NaN
data_numeric = data_numeric.fillna(0)  # NaN → 0
data_numeric = data_numeric.astype(int)  # Asegura que sean enteros

# --- Paso 4: Binarizar: si valor > 0 → 1, si 0 → 0
data_binary = (data_numeric > 0).astype(int)

# --- Paso 5: Volver a unir títulos y datos binarizados
df_binario = pd.concat([header.to_frame().T, data_binary], ignore_index=True)

print("\nPrimeras filas después de binarizar (con títulos):")
print(df_binario.head())

# --- Paso 6: Guardar el resultado
# Usamos Excel para mantener estructura
df_binario.to_excel('noticias_tokens_combinado_Revisar_Ajustado.xlsx', index=False, header=False)

print("\n✅ Archivo guardado como 'noticias_tokens_combinado_Revisar_Ajustado.xlsx'")
print("📌 Importante: Se mantuvo la primera fila como títulos y se binarizaron los datos.")