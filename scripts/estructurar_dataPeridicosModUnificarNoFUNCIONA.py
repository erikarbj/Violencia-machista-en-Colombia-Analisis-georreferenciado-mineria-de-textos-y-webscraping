import pandas as pd
import sys
import os
import re
import json
import csv
import tldextract
import spacy 
from datetime import datetime
import pycountry
from spacy.util import filter_spans
import unicodedata
from functools import lru_cache
from collections import Counter

# Variables de ruta
ruta_DATA_ESP = "datos_base/Departamentos_y_municipios_de_Colombia.csv"
ruta_CIUDADES_PAISES = "datos_base/ciudades_paises.csv"
directorio_trabajo = "articulos_x_procesar_Espectador/"
origen = "elespectador"

# Expresiones regulares de fechas
regex_fechas = [
    r'\b\d{1,2}\sde\s(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s(?:de|del)\s\d{4}\b',
    r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s\d{1,2},?\s\d{4}\b',
    r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
    r'\b\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b'
]

meses = {
    'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2, 'marzo': 3, 'mar': 3,
    'abril': 4, 'abr': 4, 'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6,
    'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8, 'septiembre': 9, 'sep': 9,
    'octubre': 10, 'oct': 10, 'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
}

# Lista de nombres propios comunes
nombres_propios_comunes = {
    'juan', 'maría', 'josé', 'luis', 'carlos', 'ana', 'pedro', 'miguel',
    'jorge', 'francisco', 'antonio', 'manuel', 'david', 'javier', 'rafael',
    'andrés', 'fernando', 'ricardo', 'alberto', 'eduardo', 'santiago',
    'daniel', 'alejandro', 'guillermo', 'raul', 'oscar', 'arturo'
}

def convertir_a_fecha(fecha_str):
    for expresion in regex_fechas:
        coincidencia = re.search(expresion, fecha_str)
        if coincidencia:
            try:
                texto = coincidencia.group().lower()
                if "de" in texto:
                    partes = texto.split(" de ")
                    if len(partes) == 3:
                        dia = int(partes[0])
                        mes = meses[partes[1].strip()]
                        anio = int(partes[2])
                elif "," in texto:
                    partes = texto.replace(",", "").split()
                    mes = meses[partes[0]]
                    dia = int(partes[1])
                    anio = int(partes[2])
                else:
                    partes = list(map(int, re.split(r"[-/]", texto)))
                    if len(str(partes[0])) == 4:
                        anio, mes, dia = partes
                    else:
                        dia, mes, anio = partes
                        if anio < 100:
                            anio += 2000
                return datetime(anio, mes, dia).strftime('%d/%m/%Y')
            except:
                continue
    return None

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def obtener_palabras_clave():
    with open('datos_base/Terminos.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        terms = [quitar_tildes(term.strip().lower()) for row in reader for term in row[0].split(",") if term.strip()]

    patrones = {}
    for term in terms:
        if len(term) >= 4:
            palabras = term.split()
            if len(palabras) > 1:
                partes_patron = []
                for p in palabras:
                    raiz = re.escape(p[:4])
                    partes_patron.append(r'\b' + raiz + r'\w*')
                patron = r'\b' + r'(?:\W+\w+){0,3}\W+'.join(partes_patron) + r'\b'
            else:
                raiz = re.escape(term[:4])
                patron = r'\b' + raiz + r'\w*'
            patrones[term] = patron
    return patrones

def normalizar_delito(texto):
    texto_normalizado = quitar_tildes(texto.lower())
    coincidencias = [clave for clave, patron in patrones_delitos.items() if re.search(patron, texto_normalizado)]
    return coincidencias or [texto]

def cargar_base_ciudades():
    """Carga la base de datos de ciudades y países desde CSV"""
    if not os.path.exists(ruta_CIUDADES_PAISES):
        print(f"El archivo {ruta_CIUDADES_PAISES} no existe. Por favor crea este archivo con las ciudades y países.")
        print("El archivo debe tener al menos las columnas: 'ciudad' y 'pais'")
        return pd.DataFrame(columns=['ciudad', 'pais', 'ciudad_normalizada'])
    
    try:
        df = pd.read_csv(ruta_CIUDADES_PAISES)
        
        if not all(col in df.columns for col in ['ciudad', 'pais']):
            print(f"Error: El archivo {ruta_CIUDADES_PAISES} debe contener las columnas 'ciudad' y 'pais'")
            return pd.DataFrame(columns=['ciudad', 'pais', 'ciudad_normalizada'])
        
        df = df[['ciudad', 'pais']].copy()
        df['ciudad'] = df['ciudad'].astype(str).str.strip()
        df['pais'] = df['pais'].astype(str).str.strip()
        df['ciudad_normalizada'] = df['ciudad'].apply(
            lambda x: quitar_tildes(x.lower().strip()) if pd.notna(x) else x)
        
        return df.drop_duplicates()
    
    except Exception as e:
        print(f"Error al cargar el archivo de ciudades: {str(e)}")
        return pd.DataFrame(columns=['ciudad', 'pais', 'ciudad_normalizada'])
    
@lru_cache(maxsize=1000)
def obtener_pais_por_ubicacion(ubicacion):
    """Determina el país al que pertenece una ubicación"""
    if not ubicacion or not isinstance(ubicacion, str):
        return None
    
    try:
        ubicacion_buscada = quitar_tildes(ubicacion.lower().strip())
        resultado = df_ciudades[df_ciudades['ciudad_normalizada'] == ubicacion_buscada]
        
        if not resultado.empty:
            return resultado.iloc[0]['pais']
        
        resultado_parcial = df_ciudades[
            df_ciudades['ciudad_normalizada'].str.startswith(ubicacion_buscada, na=False)
        ]
        
        if not resultado_parcial.empty:
            return resultado_parcial.iloc[0]['pais']
            
        return None
    
    except Exception as e:
        print(f"Error al buscar ubicación {ubicacion}: {str(e)}")
        return None

def obtener_una_url(archivo):
    ruta = os.path.join(directorio_trabajo, archivo)
    if archivo.endswith(".csv") and os.path.exists(ruta):
        df = pd.read_csv(ruta, header=None)
        return df.iloc[0, 0] if not df.empty else None
    return None

def es_apellido(texto, doc):
    """Identifica apellidos con mayor precisión"""
    if not texto or len(texto.split()) > 2:
        return False
    
    texto_normalizado = quitar_tildes(texto.strip().lower())
    
    # Lista ampliada de apellidos comunes y municipios que son también apellidos
    apellidos_comunes = {
        'garcía', 'rodríguez', 'gonzález', 'fernández', 'lópez', 'martínez', 
        'sánchez', 'pérez', 'gómez', 'martín', 'díaz', 'moreno', 'álvarez', 
        'romero', 'cáceres', 'suárez', 'torres', 'ruiz', 'hernández', 'jiménez',
        'vargas', 'ramírez', 'muñoz', 'serrano', 'morales', 'ortiz', 'delgado',
        'castro', 'flores', 'medina', 'uribe', 'pastrana', 'mosquera'
    }
    
    if texto_normalizado in apellidos_comunes:
        return True
    
    # Verificar contexto en el documento
    for ent in doc.ents:
        if ent.label_ in ("PER", "PERSON"):
            entidad_normalizada = quitar_tildes(ent.text.strip().lower())
            partes = entidad_normalizada.split()
            
            if texto_normalizado == partes[-1]:
                if len(partes) > 1 and partes[0] in nombres_propios_comunes:
                    return True
                
                for token in doc:
                    if token.text.lower() in {'sr.', 'sra.', 'dr.', 'dra.', 'don', 'doña'}:
                        if abs(token.i - ent.start) < 3:
                            return True
    
    # Verificar si aparece en mayúsculas (indicando nombre propio)
    if texto[0].isupper() and texto.lower() in municipios:
        return True
    
    return False

def verificar_localizacion(loc, doc):
    """Versión mejorada con verificación de contexto geográfico"""
    loc = loc.lower().strip()
    
    if es_apellido(loc, doc):
        return "No encontrado"
    
    if loc in municipios:
        texto = doc.text.lower()
        idx = texto.find(loc)
        if idx != -1:
            contexto = texto[max(0, idx-50):min(len(texto), idx+50)]
            
            palabras_geograficas = {
                'municipio', 'ciudad', 'localidad', 'pueblo', 'comuna',
                'corregimiento', 'vereda', 'barrio', 'departamento',
                'región', 'zona', 'área', 'lugar', 'sitio'
            }
            
            if not any(palabra in contexto for palabra in palabras_geograficas):
                return "No encontrado"
        
        return "MUNICIPIO"
    
    elif loc in departamentos:
        return "DEPARTAMENTO"
    
    return "No encontrado"

def obtener_departamento(municipio):
    res = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    return res.iloc[0]['DEPARTAMENTO'] if not res.empty else "Sin especificar"

def detectar_pais(url, texto_noticia):
    """Versión mejorada con mayor precisión en detección de países"""
    if not url:
        return "Colombia"

    url_lower = url.lower()
    texto_lower = quitar_tildes(texto_noticia.lower())
    doc = nlp(texto_noticia)
    
    if 'elmundo' in url_lower or 'el-mundo' in url_lower:
        return "Internacional"
    
    if 'colombia' in url_lower:
        return "Colombia"

    paises_mencionados = []
    menciones_colombia = 0
    
    for ent in doc.ents:
        if ent.label_ in ("LOC", "GPE"):
            pais = obtener_pais_por_ubicacion(ent.text)
            if pais:
                if pais.lower() == "colombia":
                    menciones_colombia += 1
                elif not es_apellido(ent.text, doc):
                    paises_mencionados.append(pais.lower())

    for p in paises:
        if p in texto_lower:
            if p == "colombia":
                menciones_colombia += 1
            else:
                paises_mencionados.append(p)

    if menciones_colombia > len(paises_mencionados):
        return "Colombia"
    
    if paises_mencionados:
        conteo = Counter(paises_mencionados)
        pais_principal = conteo.most_common(1)[0][0].title()
        
        if conteo.most_common(1)[0][1] >= 2:
            return pais_principal
        elif menciones_colombia > 0:
            return "Colombia"
        else:
            return pais_principal
    
    for token in doc:
        if token.text.lower() in municipios or token.text.lower() in departamentos:
            return "Colombia"
    
    return "Colombia"

# Cargar datos iniciales
if not os.path.isfile(ruta_DATA_ESP):
    print(f"El archivo {ruta_DATA_ESP} no existe.")
    sys.exit(1)

if not os.path.isdir(directorio_trabajo):
    os.makedirs(directorio_trabajo)

df_depmun = pd.read_csv(ruta_DATA_ESP)
df_ciudades = cargar_base_ciudades()
municipios = set(df_depmun['MUNICIPIO'].str.lower())
departamentos = set(df_depmun['DEPARTAMENTO'].str.lower())
paises = {c.name.lower() for c in pycountry.countries} | {"china","españa", "mexico", "turquía", "brasil", "islandia", "eua", "ee.uu.", "estados unidos"}

# Configuración de Spacy
nlp = spacy.load("es_core_news_lg")
palabrasExcluir = nlp.Defaults.stop_words
palabrasExcluir.add("el espectador")

# Procesamiento principal
output_dir = "C:/Users/Asus/TFM_CREDITOS/TFM2/Pruebas_Erika/"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "salida_abuso_sexual.txt")

lstEventos = []

with open(log_path, "w", encoding="utf-8") as log_file:
    patrones_delitos = obtener_palabras_clave()
    for archivo in os.listdir(directorio_trabajo):
        if not archivo.endswith(".csv"):
            continue

        evento = {}
        file_path = os.path.join(directorio_trabajo, archivo)
        df = pd.read_csv(file_path)
        df_text = df.to_string()

        filename = archivo.replace("elespectador_", "").replace(".csv", "")
        evento["ID_noticia"] = f"COL_{filename}"
        evento["fecha"] = datetime.strptime(archivo.split('_')[1], '%Y%m%d%H%M%S').strftime('%d/%m/%Y')

        fechas = list(set(re.findall("|".join(regex_fechas), df_text.lower())))
        fechas_date = [convertir_a_fecha(f) for f in fechas if convertir_a_fecha(f)]
        fecha_menor = min(fechas_date) if fechas_date else None

        doc = nlp(df_text)
        df_text_sin_tildes = quitar_tildes(df_text.lower())
        delitos_encontrados = [(m.start(), m.end(), d) for d, p in patrones_delitos.items() for m in re.finditer(p, df_text_sin_tildes)]

        nuevas_ents = [doc.char_span(s, e, label="DELITO") for s, e, _ in delitos_encontrados]
        nuevas_ents = [e for e in nuevas_ents if e is not None]

        entidades_existentes = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]
        todas_ents = entidades_existentes + nuevas_ents
        todas_ents_filtradas = filter_spans(todas_ents)
        doc.set_ents(todas_ents_filtradas, default="unmodified")

        conteo_delitos = {k: 0 for k in patrones_delitos.keys()}
        municipio = departamento = ""
        url = obtener_una_url(archivo)
        pais = detectar_pais(url, df_text) if url else "Colombia"

        for ent in doc.ents:
            if ent.label_ == "DELITO":
                for d in normalizar_delito(ent.text):
                    if d in conteo_delitos:
                        conteo_delitos[d] += 1
            elif ent.label_ == "LOC" and not municipio:
                resultado = verificar_localizacion(ent.text, doc)
                if resultado == "MUNICIPIO":
                    contexto = doc.text[max(0, ent.start_char-30):min(len(doc.text), ent.end_char+30)].lower()
                    if any(palabra in contexto for palabra in ['municipio', 'ciudad', 'localidad']):
                        municipio = ent.text
                        departamento = obtener_departamento(municipio)

        evento["token"] = conteo_delitos
        evento["diario"] = origen
        evento["país"] = pais if pais else "Colombia"
        evento["ubicacion_noticia"] = f"{departamento or 'sin especificar departamento'}, {municipio or 'sin especificar municipio'}"

        lstEventos.append(evento)

with open(os.path.join(output_dir, "noticias_estandarizadas_ESPECTADOR2305.json"), "w", encoding="utf-8") as f:
    json.dump(lstEventos, f, ensure_ascii=False, indent=4)