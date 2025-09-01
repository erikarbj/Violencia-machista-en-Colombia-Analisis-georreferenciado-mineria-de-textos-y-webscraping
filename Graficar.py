import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import numpy as np

# --- 1. Leer el archivo Excel ---
archivo = 'noticias_tokens_combinado_Revisar1.xlsx'  # Cambia si es otro nombre
df = pd.read_excel(archivo)

# Corregir posible error de codificación en el nombre de la columna
df.columns = [col.replace('paÃ­s', 'país') if 'paÃ­s' in col else col for col in df.columns]

# Verificar que existe la columna 'país'
if 'país' not in df.columns:
    print("❌ No se encontró la columna 'país'. Revisa el archivo.")
    print("Columnas disponibles:", df.columns.tolist())
    exit()

# --- 2. Filtrar solo noticias de Colombia ---
df['país'] = df['país'].astype(str).str.strip().str.lower()
colombia = df[df['país'] == 'colombia'].copy()

if len(colombia) == 0:
    print("⚠️ No se encontraron noticias de Colombia. Valores únicos en 'país':")
    print(df['país'].value_counts())
    exit()

print(f"✅ Filtrado: {len(colombia)} noticias de Colombia")
# Las columnas de violencia comienzan después de 'enlace'
try:
    start_idx = df.columns.get_loc('enlace') + 1
except KeyError:
    print("❌ No se encontró la columna 'enlace'. Revisa el nombre.")
    exit()

# Seleccionar columnas de violencia
violence_columns = df.columns[start_idx:].tolist()
colombia_violencia = colombia[violence_columns].copy()

# Convertir a numérico (por si hay texto o errores)
colombia_violencia = colombia_violencia.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
frecuencia = colombia_violencia.sum().sort_values(ascending=False)

plt.figure(figsize=(10, 6))
frecuencia.head(15).plot(kind='barh', color='crimson', edgecolor='darkred')
plt.title('Top 15 tipos de violencia de género en Colombia', fontsize=14)
plt.xlabel('Frecuencia total en noticias')
plt.ylabel('Tipo de violencia')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()
from wordcloud import WordCloud

word_freq = frecuencia[frecuencia > 0].to_dict()

wc = WordCloud(
    width=800,
    height=400,
    background_color='white',
    colormap='Reds',
    collocations=False,
    max_words=50
).generate_from_frequencies(word_freq)

plt.figure(figsize=(12, 6))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.title('Nube de palabras: Violencia de género en Colombia', fontsize=16)
plt.tight_layout()
plt.show()
top_10 = frecuencia.head(10)
bottom_10 = frecuencia.tail(10)

fig, ax = plt.subplots(1, 2, figsize=(14, 6))

top_10.plot(kind='bar', ax=ax[0], color='indianred')
ax[0].set_title('10 más mencionadas')
ax[0].tick_params(axis='x', rotation=45)

bottom_10.plot(kind='bar', ax=ax[1], color='lightcoral')
ax[1].set_title('10 menos mencionadas')
ax[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.show()
# Matriz de co-ocurrencia binaria
binary_data = (colombia_violencia > 0).astype(int)
coocurrence = binary_data.T @ binary_data

plt.figure(figsize=(12, 10))
sns.heatmap(coocurrence, cmap='OrRd', cbar=True, xticklabels=False, yticklabels=False)
plt.title('Co-ocurrencia entre tipos de violencia en Colombia')
plt.tight_layout()
plt.show()
# Definir categorías
categorias = {
    'Violencia física': ['violencia fisica', 'agresion sexual', 'violencia domestica', 'violencia familiar', 'violencia intrafamiliar'],
    'Violencia sexual': ['abuso sexual', 'violacion', 'violaciones', 'acceso carnal violento', 'acto sexual violento'],
    'Violencia digital': ['ciberviolencia', 'ciberacoso', 'ciberhostigamiento', 'doxing', 'revenge porn'],
    'Violencia estructural': ['discriminacion femenina', 'machismo', 'techo de cristal', 'sexismo', 'cultura de violacion'],
    'Delitos graves': ['feminicidio', 'asesinatos de mujeres', 'trata de mujeres', 'matrimonio forzado', 'esclavitud sexual'],
    'Violencia psicológica': ['violencia psicologica', 'violencia emocional', 'misoginia', 'microagresiones']
}

# Sumar por categoría
suma_categorias = {}
for cat, cols in categorias.items():
    existentes = [c for c in cols if c in colombia_violencia.columns]
    suma_categorias[cat] = colombia_violencia[existentes].sum(axis=1).sum()

# Graficar
plt.figure(figsize=(10, 6))
pd.Series(suma_categorias).sort_values().plot(kind='barh', color='steelblue', edgecolor='black')
plt.title('Violencia de género en Colombia por categoría temática')
plt.xlabel('Frecuencia total')
plt.tight_layout()
plt.show()
categoria_series = pd.Series(suma_categorias)
top_5 = categoria_series.nlargest(5)
otros = categoria_series[~categoria_series.index.isin(top_5.index)].sum()
if otros > 0:
    top_5['Otros'] = otros

plt.figure(figsize=(8, 8))
top_5.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
plt.title('Distribución de violencia de género en Colombia')
plt.ylabel('')
plt.tight_layout()
plt.show()
digitales = [
    'ciberviolencia', 'ciberacoso', 'ciberhostigamiento',
    'doxing', 'revenge porn', 'violencia sexual cibernetica'
]

digitales_existentes = [d for d in digitales if d in colombia_violencia.columns]
if digitales_existentes:
    digitales_data = colombia_violencia[digitales_existentes].sum().sort_values(ascending=False)
    plt.figure(figsize=(8, 5))
    digitales_data.plot(kind='bar', color='purple')
    plt.title('Violencia digital en Colombia')
    plt.ylabel('Frecuencia')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ No se encontraron columnas de violencia digital.")

if 'fecha' in df.columns:
    colombia['fecha'] = pd.to_datetime(colombia['fecha'], errors='coerce')
    colombia['mes'] = colombia['fecha'].dt.to_period('M')
    timeline = colombia.groupby('mes').size()

    plt.figure(figsize=(12, 5))
    timeline.plot(marker='o', color='navy')
    plt.title('Cantidad de noticias sobre violencia de género en Colombia por mes')
    plt.ylabel('Número de noticias')
    plt.xlabel('Mes')
    plt.xticks(rotation=45)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ No se encontró la columna 'fecha'.")

colombia.to_excel('noticias_colombia.xlsx', index=False)
print("✅ Datos de Colombia guardados en 'noticias_colombia.xlsx'")