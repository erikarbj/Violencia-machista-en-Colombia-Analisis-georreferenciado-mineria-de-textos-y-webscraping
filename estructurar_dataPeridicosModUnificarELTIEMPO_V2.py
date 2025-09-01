import pandas as pd
import sys
import os
import re
import json
import csv
import spacy 
from datetime import datetime
import pycountry
from spacy.util import filter_spans
import unicodedata
from collections import Counter

# Configuración inicial
ruta_DATA_ESP = "datos_base/Departamentos_y_municipios_de_Colombia.csv"
directorio_trabajo = "articulos_x_procesar_ElTiempo_Duplicados/"
origen = "eltiempo"
output_dir = "C:/Users/Asus/TFM_CREDITOS/TFM2/Pruebas_Erika/"

# Expresiones regulares para fechas
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

# Configuración NLP
nlp = spacy.load("es_core_news_lg")
palabrasExcluir = nlp.Defaults.stop_words
palabrasExcluir.add("el tiempo")

# Palabras a excluir de ubicaciones
palabras_excluir_ubicacion = {
    "fiscalía", "artículo", "página", "web", "archivo", "noticias", 
    "judicial", "citara", "interrogatorio", "http", "https", "www", 
    "com", "articulo", "elsepectador", "web.archive", "virgen", "carmen",
    "jesús", "cristo", "dios", "santo", "santa", "iglesia", "religión"
}

# Lista de apellidos comunes
apellidos_comunes = {
    "cáceres", "gómez", "lópez", "rodríguez", "martínez", "hernández", 
    "garcía", "pérez", "gonzález", "sánchez", "ramírez", "torres", 
    "flores", "díaz", "vargas", "morales", "suárez", "castro", "romero"
}

# Mapeo de nacionalidades a países
nacionalidades_a_paises = {
    "argentino": "argentina", "argentina": "argentina",
    "italiano": "italia", "italiana": "italia",
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
    "salvadoreño": "el salvador", "salvadoreña": "el salvador", "salvadoreños": "el salvador",
    "saudi": "arabia saudita", "saudí": "arabia saudita", "saudies": "arabia saudita",
    "saudita": "arabia saudita", "arabia saudita": "arabia saudita",
    "estadounidense": "estados unidos", "norteamericano": "estados unidos", "norteamericana": "estados unidos","EE.UU": "estados unidos"
}

# Configuración de países
paises = {c.name.lower() for c in pycountry.countries} | {
    "china", "españa", "mexico", "turquía", "brasil", "islandia", "eua", "italia",
    "eeuu", "estados unidos", "usa", "us", "reino unido", "francia", "alemania",
    "italia", "canadá", "argentina", "venezuela", "perú", "ecuador",
    "arabia saudita", "arabia saudí", "saudi arabia",
    "chile", "panamá", "uruguay", "paraguay", "bolivia", "el salvador", "salvador"
}

# Nombres alternativos para localizaciones
nombres_alternativos = {
    "bogota": "bogota",
    "bogotá": "bogota",
    "bogotana": "bogota",
    "bogotano": "bogota",
    "bogota d.c.": "bogota",
    "capital": "bogota",
    "barranquilla": "barranquilla",
    "cartagena": "cartagena de indias",
    "cartagena de indias": "cartagena de indias",
    "buenaventura": "buenaventura",
    "santa marta": "santa marta",
    "cauca": "cauca",
    "arauca": "arauca",
    "antioquia": "antioquia",
    "norte de antioquia": "antioquia",
    "norte antioquia": "antioquia",
    "departamento de arauca": "arauca",
    "arauca arauca": "arauca",
    "santander de quilichao": "santander de quilichao",
    "quilichao": "santander de quilichao",
    "sierra nevada": "santa marta",
    "sierra nevada de santa marta": "santa marta"
}

def quitar_tildes(texto):
    if not texto or pd.isna(texto):
        return ""
    texto = unicodedata.normalize('NFD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto

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

def es_ubicacion_valida(texto):
    texto_lower = quitar_tildes(texto.lower())
    if any(palabra in texto_lower for palabra in palabras_excluir_ubicacion):
        return False
    terminos_religiosos = {
        "virgen del carmen", "virgen de chiquinquirá", "virgen de fatima",
        "sagrado corazón", "jesucristo", "jesús", "cristo", "dios"
    }
    if texto_lower in terminos_religiosos:
        return False
    return True

def verificar_localizacion(loc):
    if not loc or pd.isna(loc):
        return "No encontrado"
    loc_normalized = quitar_tildes(str(loc).strip().lower())
    special_cases = {"cauca", "arauca", "bogota", "bogotá", "antioquia"}
    if loc_normalized in special_cases:
        return "DEPARTAMENTO" if loc_normalized in {"cauca", "arauca", "antioquia"} else "MUNICIPIO"
    if loc_normalized in nombres_alternativos:
        loc_normalized = nombres_alternativos[loc_normalized]
    if loc_normalized in municipios_normalizados:
        return "MUNICIPIO"
    if loc_normalized in departamentos_normalizados:
        return "DEPARTAMENTO"
    for mun in municipios_normalizados:
        if mun == loc_normalized or mun in loc_normalized or loc_normalized in mun:
            return "MUNICIPIO"
    for dep in departamentos_normalizados:
        if dep == loc_normalized or dep in loc_normalized or loc_normalized in dep:
            return "DEPARTAMENTO"
    return "No encontrado"

def obtener_departamento(municipio):
    if not municipio or pd.isna(municipio):
        return "Sin especificar"
    municipio_normalizado = quitar_tildes(str(municipio).lower())
    if municipio_normalizado in nombres_alternativos:
        municipio_normalizado = nombres_alternativos[municipio_normalizado]
    res = df_depmun[df_depmun['municipio_norm'] == municipio_normalizado]
    if res.empty:
        for idx, row in df_depmun.iterrows():
            if municipio_normalizado in row['municipio_norm'] or row['municipio_norm'] in municipio_normalizado:
                return row['departamento']
    return res.iloc[0]['departamento'] if not res.empty else "Sin especificar"

def detectar_pais(url, doc_text):
    texto_normalizado = quitar_tildes(doc_text.lower())
    url_lower = url.lower() if url else ""

    # 1. Verificar si es internacional
    if url_lower and ("/elmundo/" in url_lower or "/el-mundo/" in url_lower or "/entretenimiento/" in url_lower):
        return "Internacional"

    # 2. Buscar en el título
    lineas = [linea.strip() for linea in doc_text.split('\n') if linea.strip()]
    titulo = min(lineas[:3], key=len) if lineas else ""
    titulo_normalizado = quitar_tildes(titulo.lower())

    for nacionalidad, pais in nacionalidades_a_paises.items():
        if nacionalidad in titulo_normalizado:
            if "colombiano" in titulo_normalizado or "colombiana" in titulo_normalizado:
                continue
            return pais.title()

    # 3. Búsqueda exhaustiva de nacionalidades en todo el texto
    nacionalidades_encontradas = []
    palabras = texto_normalizado.split()
    for i, palabra in enumerate(palabras):
        if palabra in nacionalidades_a_paises:
            nacionalidades_encontradas.append(nacionalidades_a_paises[palabra])
        if i > 0 and palabras[i-1] in ["los", "las", "en", "de"]:
            if palabra in nacionalidades_a_paises:
                nacionalidades_encontradas.append(nacionalidades_a_paises[palabra])

    paises_no_colombianos = [p for p in nacionalidades_encontradas if p != "colombia"]
    if paises_no_colombianos:
        return max(set(paises_no_colombianos), key=paises_no_colombianos.count).title()

    # 4. Análisis de entidades LOC
    doc = nlp(doc_text)
    ubicaciones_colombianas = []
    paises_encontrados = []
    for ent in doc.ents:
        if ent.label_ == "LOC" and es_ubicacion_valida(ent.text):
            loc_normalized = quitar_tildes(ent.text.lower())
            tipo_loc = verificar_localizacion(ent.text)
            if tipo_loc in ["MUNICIPIO", "DEPARTAMENTO"]:
                ubicaciones_colombianas.append(ent.text)
            if loc_normalized in paises:
                paises_encontrados.append(loc_normalized)

    paises_unicos = list(set(paises_encontrados))
    if len(paises_unicos) == 1 and paises_unicos[0] != "colombia":
        return paises_unicos[0].title()

    if ubicaciones_colombianas:
        return "Colombia"

    if url_lower and any(sec in url_lower for sec in ["/bogota/", "/colombia/", "/nacional/", "/antioquia/"]):
        return "Colombia"

    return "Colombia"


def procesar_ubicacion(doc_text, pais, url=None):
    texto_normalizado = quitar_tildes(doc_text.lower())
    
    if pais != "Colombia":
        return "Internacional"

    # Prioridad 1: Verificar URL
    if url:
        url_lower = url.lower()
        for loc in nombres_alternativos:
            if f"/{loc}/" in url_lower:
                municipio = nombres_alternativos[loc]
                depto = obtener_departamento(municipio)
                return f"{depto}, {municipio}"

    # Prioridad 2: Casos específicos conocidos
    if "engativá" in texto_normalizado or "usaquén" in texto_normalizado:
        return "Bogotá, Bogotá"
    if "chapinero" in texto_normalizado:
        return "Bogotá, Bogotá"

    # Prioridad 3: Patrones en el texto
    patrones_ubicacion = [
        (r'en(?:\s+el)?\s+(?:municipio|localidad)\s+de\s+([^\s,.;]+)', "MUNICIPIO"),
        (r'en ([^\s,.;]+),\s*(?:departamento|depto)\.?\s*de\s*([^\s,.;]+)', "MUNICIPIO_CON_DEPTO"),
        (r'barrio ([^\s,.;]+) de ([^\s,.;]+)', "BARRIO_CIUDAD"),
        (r'norte\s+de\s+bogotá', "BOGOTA_NORTE"),  # Nuevo patrón
        (r'sector\s+del\s+norte\s+de\s+bogotá', "BOGOTA_NORTE"),
        (r'la picota', "BOGOTA"),
        (r'bogotá', "BOGOTA")
    ]

    for patron, tipo in patrones_ubicacion:
        coincidencias = re.finditer(patron, texto_normalizado)
        for match in coincidencias:
            if tipo == "BOGOTA":
                return "Bogotá, Bogotá"
            elif tipo == "BOGOTA_NORTE":
                return "Bogotá, Norte de Bogotá"
            elif tipo == "MUNICIPIO":
                municipio = match.group(1).strip().lower()
                if municipio in municipios_normalizados:
                    depto = obtener_departamento(municipio.title())
                    return f"{depto}, {municipio.title()}"
            elif tipo == "MUNICIPIO_CON_DEPTO":
                municipio = match.group(1).strip().lower()
                depto = match.group(2).strip().lower()
                if municipio in municipios_normalizados:
                    depto_real = obtener_departamento(municipio.title())
                    return f"{depto_real}, {municipio.title()}"
                elif depto in departamentos_normalizados:
                    return f"{depto.title()}, Sin especificar municipio"
            elif tipo == "BARRIO_CIUDAD":
                ciudad = match.group(2).strip().lower()
                if ciudad in municipios_normalizados:
                    depto = obtener_departamento(ciudad.title())
                    return f"{depto}, {ciudad.title()}"

    # Prioridad 4: Entidades LOC con verificación estricta
    doc = nlp(doc_text)
    for ent in doc.ents:
        if ent.label_ == "LOC" and es_ubicacion_valida(ent.text):
            loc_type = verificar_localizacion(ent.text)
            if loc_type == "MUNICIPIO":
                municipio = ent.text.strip().lower()
                if municipio in municipios_normalizados:
                    depto = obtener_departamento(municipio.title())
                    return f"{depto}, {municipio.title()}"
            elif loc_type == "DEPARTAMENTO":
                depto = ent.text.strip().lower()
                if depto in departamentos_normalizados:
                    return f"{depto.title()}, Sin especificar municipio"

    # Fallback seguro
    return "Colombia (ubicación no especificada)"

# Cargar datos de localizaciones
df_depmun = pd.read_csv(ruta_DATA_ESP)
df_depmun.columns = ['region', 'codigo_region', 'departamento', 'codigo_depto', 'municipio']
df_depmun['municipio_norm'] = df_depmun['municipio'].apply(lambda x: quitar_tildes(str(x).strip().lower()))
df_depmun['departamento_norm'] = df_depmun['departamento'].apply(lambda x: quitar_tildes(str(x).strip().lower()))

# Localidades por ciudad
localidades_por_ciudad = {
    "usaquén": "bogotá", "chapinero": "bogotá", "santa fe": "bogotá",
    "san cristóbal": "bogotá", "usme": "bogotá", "tunjuelito": "bogotá",
    "bosa": "bogotá", "kennedy": "bogotá", "fontibón": "bogotá",
    "engativá": "bogotá", "suba": "bogotá", "barrios unidos": "bogotá",
    "teusaquillo": "bogotá", "los mártires": "bogotá", "antonio nariño": "bogotá",
    "puente aranda": "bogotá", "candelaria": "bogotá", "rafael uribe uribe": "bogotá"
}

# Ampliar nombres alternativos
nombres_alternativos.update({
    "medellin": "medellín", "cali": "cali", "barranquilla": "barranquilla",
    "cartagena": "cartagena de indias", "bucaramanga": "bucaramanga",
    "pereira": "pereira", "manizales": "manizales", "cucuta": "cúcuta",
    "villavicencio": "villavicencio"
})

municipios_normalizados = set(df_depmun['municipio_norm'])
departamentos_normalizados = set(df_depmun['departamento_norm'])

# Procesamiento de archivos
lstEventos = []
patrones_delitos = obtener_palabras_clave()

for archivo in os.listdir(directorio_trabajo):
    if not archivo.endswith(".csv"):
        continue
    print(f"\nProcesando archivo: {archivo}")
    file_path = os.path.join(directorio_trabajo, archivo)
    df = pd.read_csv(file_path)
    df_text = df.to_string()
    filename = archivo.replace("eltiempo_", "").replace(".csv", "")

    # Fecha
    fechas = list(set(re.findall("|".join(regex_fechas), df_text.lower())))
    fechas_date = [convertir_a_fecha(f) for f in fechas if convertir_a_fecha(f)]
    fecha_menor = min(fechas_date) if fechas_date else None

    # Procesar texto con spaCy
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

    # Conteo de delitos
    conteo_delitos = {k: 0 for k in patrones_delitos.keys()}
    for ent in doc.ents:
        if ent.label_ == "DELITO":
            for d in normalizar_delito(ent.text):
                if d in conteo_delitos:
                    conteo_delitos[d] += 1

    # Procesar ubicación
    url = None
    try:
        df_url = pd.read_csv(file_path, header=None)
        url = df_url.iloc[0, 0] if not df_url.empty else None
    except Exception:
        pass

    pais = detectar_pais(url, df_text)
    ubicacion = procesar_ubicacion(df_text, pais, url)

    evento = {
        "ID_noticia": f"COL_{filename}",
        "fecha": datetime.strptime(archivo.split('_')[1], '%Y%m%d%H%M%S').strftime('%d/%m/%Y'),
        "token": conteo_delitos,
        "diario": origen,
        "país": pais,
        "ubicacion_noticia": ubicacion,
        "enlace": url
    }

    lstEventos.append(evento)
    print(f"Procesado: {filename} | País: {pais} | Ubicación: {ubicacion}")

# Guardar resultados
output_file = os.path.join(output_dir, "noticias_estandarizadas_Tiempo_24082025.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(lstEventos, f, ensure_ascii=False, indent=4)

print(f"\nProcesamiento completado. Resultados guardados en: {output_file}")
print(f"Total de noticias procesadas: {len(lstEventos)}")