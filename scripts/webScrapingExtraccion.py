import pandas as pd
from newspaper import Article
import time

# Ruta al CSV original
input_csv = 'archivoControlUniversal_2016.csv'
output_csv = 'archivoControlUniversal_2016_Noticas.csv'

# Leer CSV original
df = pd.read_csv(input_csv, header=None, names=['raw'])
# Extraer solo los enlaces
df['link'] = df['raw'].str.extract(r'Artículo:\s*(https?://\S+)')
df = df.dropna(subset=['link'])

# Lista para guardar resultados
resultados = []

for idx, row in df.iterrows():
    url = row['link']
    print(f"Procesando: {url}")
    try:
        article = Article(url)
        article.download()
        article.parse()
        texto = article.text.strip().replace('\n', ' ')
        if not texto:
            texto = 'No se pudo extraer contenido'
        resultados.append({'enlace': url, 'noticia': texto})
    except Exception as e:
        print(f"Error en {url}: {e}")
        resultados.append({'enlace': url, 'noticia': f"Error al extraer: {e}"})
    
    # Pausa para no sobrecargar (opcional)
    time.sleep(1)

# Guardar resultados en nuevo CSV
df_resultado = pd.DataFrame(resultados)
df_resultado.to_csv(output_csv, index=False, encoding='utf-8')

print(f"Proceso terminado. Resultados guardados en {output_csv}")