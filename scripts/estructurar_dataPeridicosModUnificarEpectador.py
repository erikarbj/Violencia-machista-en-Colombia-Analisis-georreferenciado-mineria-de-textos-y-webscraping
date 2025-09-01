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

# Variables de ruta
ruta_DATA_ESP = "datos_base/Departamentos_y_municipios_de_Colombia.csv"
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

if not os.path.isfile(ruta_DATA_ESP):
    print(f"El archivo {ruta_DATA_ESP} no existe.")
    sys.exit(1)

if not os.path.isdir(directorio_trabajo):
    os.makedirs(directorio_trabajo)

# Cargar datos de localizaciones colombianas
df_depmun = pd.read_csv(ruta_DATA_ESP)
municipios = set(df_depmun['MUNICIPIO'].str.lower())
departamentos = set(df_depmun['DEPARTAMENTO'].str.lower())

# Configuración de países y nacionalidades
paises = {c.name.lower() for c in pycountry.countries} | {
    "china", "españa", "mexico", "turquía", "brasil", "islandia", "eua",
    "eeuu", "estados unidos", "usa", "reino unido", "francia", "alemania",
    "italia", "canadá", "argentina", "venezuela", "perú", "ecuador",
    "chile", "panamá", "uruguay", "paraguay", "bolivia"
}

# Mapeo de nacionalidades a países
nacionalidades_a_paises = {
    "argentino": "argentina", "argentina": "argentina",
    "boliviano": "bolivia", "boliviana": "bolivia",
    "brasileño": "brasil", "brasileña": "brasil", "brasilero": "brasil", "brasilera": "brasil",
    "chileno": "chile", "chilena": "chile",
    "colombiano": "colombia", "colombiana": "colombia",
    "ecuatoriano": "ecuador", "ecuatoriana": "ecuador",
    "español": "españa", "española": "españa",
    "mexicano": "mexico", "mexicana": "mexico",
    "paraguayo": "paraguay", "paraguaya": "paraguay",
    "peruano": "perú", "peruana": "perú",
    "uruguayo": "uruguay", "uruguaya": "uruguay",
    "venezolano": "venezuela", "venezolana": "venezuela",
    "estadounidense": "estados unidos", "norteamericano": "estados unidos", "norteamericana": "estados unidos",
    "americano": "estados unidos", "americana": "estados unidos"
}

def verificar_localizacion(loc):
    loc_normalized = quitar_tildes(loc.lower())
    municipios_normalized = {quitar_tildes(m.lower()) for m in municipios}
    departamentos_normalized = {quitar_tildes(d.lower()) for d in departamentos}
    
    if loc_normalized in municipios_normalized:
        return "MUNICIPIO"
    elif loc_normalized in departamentos_normalized:
        return "DEPARTAMENTO"
    return "No encontrado"

def obtener_departamento(municipio):
    res = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    return res.iloc[0]['DEPARTAMENTO'] if not res.empty else "Sin especificar"

def detectar_pais(url, doc_text):
    # Normalizar el texto para búsqueda
    texto_normalizado = quitar_tildes(doc_text.lower())
    
    # 1. Buscar nacionalidades en el texto (ej: "brasileño" -> "brasil")
    for nacionalidad, pais in nacionalidades_a_paises.items():
        if nacionalidad in texto_normalizado:
            return pais.title()
    
    # 2. Buscar menciones directas de países en el texto
    doc = nlp(doc_text)
    paises_en_texto = []
    for ent in doc.ents:
        if ent.label_ == "LOC":
            loc_lower = quitar_tildes(ent.text.lower())
            if loc_lower in paises:
                paises_en_texto.append(ent.text.title())
    
    if paises_en_texto:
        return paises_en_texto[0]
    
    # 3. Verificar si es una noticia internacional (sección "el-mundo")
    if url and ("el-mundo" in url.lower() or "elmundo" in url.lower()):
        # Buscar en el título (primeras líneas del texto)
        primeras_lineas = doc_text[:500].lower()
        for pais in paises:
            if pais in primeras_lineas:
                return pais.title()
    
    # 4. Verificar localizaciones colombianas
    for ent in doc.ents:
        if ent.label_ == "LOC":
            loc_type = verificar_localizacion(ent.text)
            if loc_type in ["MUNICIPIO", "DEPARTAMENTO"]:
                return "Colombia"
    
    # 5. Si no se encuentra nada, buscar en la URL
    if url:
        url_lower = url.lower()
        for pais in paises:
            if pais in url_lower:
                return pais.title()
    
    return None

def obtener_una_url(archivo):
    ruta = os.path.join(directorio_trabajo, archivo)
    if archivo.endswith(".csv") and os.path.exists(ruta):
        df = pd.read_csv(ruta, header=None)
        return df.iloc[0, 0] if not df.empty else None
    return None

# Configuración de NLP
nlp = spacy.load("es_core_news_lg")
palabrasExcluir = nlp.Defaults.stop_words
palabrasExcluir.add("el espectador")

# Lista de apellidos comunes que coinciden con municipios
apellidos_comunes = {
    "cáceres", "gómez", "lópez", "rodríguez", "martínez", "hernández", 
    "garcía", "pérez", "gonzález", "sánchez", "ramírez", "torres", 
    "flores", "díaz", "vargas", "morales", "suárez", "castro", "romero"
}

def es_probable_apellido(texto, contexto):
    # Si el texto está en mayúsculas o sigue un nombre propio, probablemente sea apellido
    if texto.isupper() or texto.istitle():
        return True
    
    # Buscar patrones de nombres completos (Nombre + Apellido)
    if re.search(r'\b[A-Z][a-z]+\s+' + re.escape(texto) + r'\b', contexto):
        return True
    
    # Verificar si es un apellido común
    if quitar_tildes(texto.lower()) in apellidos_comunes:
        return True
    
    return False

# Procesamiento de archivos
lstEventos = []
output_dir = "C:/Users/Asus/TFM_CREDITOS/TFM2/Pruebas_Erika/"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "salida_abuso_sexual.txt")

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

        # Procesamiento de fechas
        fechas = list(set(re.findall("|".join(regex_fechas), df_text.lower())))
        fechas_date = [convertir_a_fecha(f) for f in fechas if convertir_a_fecha(f)]
        fecha_menor = min(fechas_date) if fechas_date else None

        # Procesamiento de texto con spaCy
        doc = nlp(df_text)
        df_text_sin_tildes = quitar_tildes(df_text.lower())
        
        # Detección de delitos
        delitos_encontrados = [(m.start(), m.end(), d) for d, p in patrones_delitos.items() for m in re.finditer(p, df_text_sin_tildes)]
        nuevas_ents = [doc.char_span(s, e, label="DELITO") for s, e, _ in delitos_encontrados]
        nuevas_ents = [e for e in nuevas_ents if e is not None]

        # Filtrado de entidades
        entidades_existentes = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]
        todas_ents = entidades_existentes + nuevas_ents
        todas_ents_filtradas = filter_spans(todas_ents)
        doc.set_ents(todas_ents_filtradas, default="unmodified")

        # Conteo de delitos y detección de ubicación
        conteo_delitos = {k: 0 for k in patrones_delitos.keys()}
        municipio = departamento = ""
        url = obtener_una_url(archivo)
        pais = detectar_pais(url, df_text)

        for ent in doc.ents:
            if ent.label_ == "DELITO":
                for d in normalizar_delito(ent.text):
                    if d in conteo_delitos:
                        conteo_delitos[d] += 1
            elif ent.label_ == "LOC":
                # Verificar si es probablemente un apellido antes de considerarlo ubicación
                if not es_probable_apellido(ent.text, df_text):
                    loc_type = verificar_localizacion(ent.text)
                    if loc_type == "MUNICIPIO" and not municipio:
                        municipio = ent.text
                        departamento = obtener_departamento(municipio)
                    elif loc_type == "DEPARTAMENTO" and not departamento:
                        departamento = ent.text

        # Solo incluir ubicación si el país es Colombia
        if pais and pais.lower() == "colombia":
            ubicacion = f"{departamento or 'sin especificar departamento'}, {municipio or 'sin especificar municipio'}"
        else:
            ubicacion = "sin especificar departamento, sin especificar municipio"

        # Construcción del evento final
        evento["token"] = conteo_delitos
        evento["diario"] = origen
        evento["país"] = pais if pais else "Colombia" if municipio or departamento else "Sin especificar"
        evento["ubicacion_noticia"] = ubicacion
        
        lstEventos.append(evento)

# Guardar resultados
with open(os.path.join(output_dir, "noticias_estandarizadas_ESPECTADOR22.json"), "w", encoding="utf-8") as f:
    json.dump(lstEventos, f, ensure_ascii=False, indent=4)