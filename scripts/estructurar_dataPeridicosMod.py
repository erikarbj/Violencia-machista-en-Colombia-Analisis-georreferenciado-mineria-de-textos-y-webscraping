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
from spacy.util import filter_spans  # Asegúrate de tener este import arriba en el script


# Variables de ruta
ruta_DATA_ESP = "datos_base/Departamentos_y_municipios_de_Colombia.csv"
directorio_trabajo = "articulos_x_procesar_Colombiano/"
origen = "elcolombiano"

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

# 🔧 FUNCION AJUSTADA para mejorar detección de términos como 'abuso sexual'
def obtener_palabras_clave():
    with open('datos_base/Terminos.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        terms = [term.strip().lower() for row in reader for term in row[0].split(",") if term.strip()]

    patrones = {}
    for term in terms:
        patron = r"\b" + r"\s+".join(map(re.escape, term.split())) + r"\b"
        patrones[term] = patron
    return patrones

patrones_delitos = obtener_palabras_clave()

def normalizar_delito(texto):
    texto = texto.lower().strip()
    coincidencias = [clave for clave, patron in patrones_delitos.items() if re.search(patron, texto)]
    return coincidencias or [texto]

if not os.path.isfile(ruta_DATA_ESP):
    print(f"El archivo {ruta_DATA_ESP} no existe.")
    sys.exit(1)

if not os.path.isdir(directorio_trabajo):
    os.makedirs(directorio_trabajo)

df_depmun = pd.read_csv(ruta_DATA_ESP)
municipios = set(df_depmun['MUNICIPIO'].str.lower())
departamentos = set(df_depmun['DEPARTAMENTO'].str.lower())
paises = {c.name.lower() for c in pycountry.countries} | {"china","españa", "mexico", "turquía", "brasil", "islandia", "eua"}

def verificar_localizacion(loc):
    loc = loc.lower()
    if loc in municipios:
        return "MUNICIPIO"
    elif loc in departamentos:
        return "DEPARTAMENTO"
    return "No encontrado"

def obtener_departamento(municipio):
    res = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    return res.iloc[0]['DEPARTAMENTO'] if not res.empty else "Sin especificar"

def detectar_pais(url):
    ext = tldextract.extract(url)
    dominio = ext.domain.lower()
    path = url.lower()
    for pais in paises:
        if pais in dominio or pais in path:
            return pais.title()

def obtener_una_url(archivo):
    ruta = os.path.join(directorio_trabajo, archivo)
    if archivo.endswith(".csv") and os.path.exists(ruta):
        df = pd.read_csv(ruta, header=None)
        return df.iloc[0, 0] if not df.empty else None
    return None

nlp = spacy.load("es_core_news_lg")
palabrasExcluir = nlp.Defaults.stop_words
palabrasExcluir.add("el colombiano")

lstEventos = []

output_dir = "C:/Users/Asus/TFM_CREDITOS/TFM2/Pruebas_Erika/"
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "salida_abuso_sexual.txt")

with open(log_path, "w", encoding="utf-8") as log_file:

    for archivo in os.listdir(directorio_trabajo):
        if not archivo.endswith(".csv"):
            continue

        evento = {}
        file_path = os.path.join(directorio_trabajo, archivo)
        df = pd.read_csv(file_path)
        df_text = df.to_string()

        print("------ Analizando archivo:", archivo)
        print("------ Analizando archivo:", archivo, file=log_file)

        print("'abuso sexual' en texto:", "abuso sexual" in df_text.lower())
        print("'abuso sexual' en texto:", "abuso sexual" in df_text.lower(), file=log_file)

        match = re.search(patrones_delitos["abuso sexual"], df_text.lower())
        print("Regex match con patrón:", match)
        print("Regex match con patrón:", match, file=log_file)

        filename = archivo.replace("elcolombiano_", "").replace(".csv", "")
        evento["ID_noticia"] = f"COL_{filename}"
        evento["fecha"] = datetime.strptime(archivo.split('_')[1], '%Y%m%d%H%M%S').strftime('%d/%m/%Y')

        fechas = list(set(re.findall("|".join(regex_fechas), df_text.lower())))
        fechas_date = [convertir_a_fecha(f) for f in fechas if convertir_a_fecha(f)]
        fecha_menor = min(fechas_date) if fechas_date else None

        doc = nlp(df_text)
        delitos_encontrados = [(m.start(), m.end(), d) for d, p in patrones_delitos.items() for m in re.finditer(p, df_text.lower())]
        #nuevas_ents = [doc.char_span(s, e, label="DELITO") for s, e, _ in delitos_encontrados if doc.char_span(s, e, label="DELITO")]
        #nuevas_ents = [e for e in nuevas_ents if not any(e.start < ent.end and ent.start < e.end for ent in doc.ents)]
        #doc.ents = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]] + nuevas_ents

        # Crear spans nuevos a partir de los delitos encontrados
        nuevas_ents = [doc.char_span(s, e, label="DELITO") for s, e, _ in delitos_encontrados]
        nuevas_ents = [e for e in nuevas_ents if e is not None]  # Eliminar spans inválidos

        # Mantener solo LOC y PER de las entidades existentes
        entidades_existentes = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]

        # Unir entidades y eliminar solapamientos
        todas_ents = entidades_existentes + nuevas_ents
        todas_ents_filtradas = filter_spans(todas_ents)

        # Asignar nuevas entidades sin errores
        doc.set_ents(todas_ents_filtradas, default="unmodified")


        conteo_delitos = {k: 0 for k in patrones_delitos.keys()}
        municipio = departamento = ""
        url = obtener_una_url(archivo)
        pais = detectar_pais(url) if url else "Colombia"

        for ent in doc.ents:
            if ent.label_ == "DELITO":
                for d in normalizar_delito(ent.text):
                    if d in conteo_delitos:
                        conteo_delitos[d] += 1
            elif ent.label_ == "LOC" and not municipio:
                if verificar_localizacion(ent.text) == "MUNICIPIO":
                    municipio = ent.text
                    departamento = obtener_departamento(municipio)

        evento["token"] = conteo_delitos
        evento["diario"] = origen
        evento["país"] = "Colombia" if pais and pais.lower() == "colombia" else "Otro País"
        evento["ubicacion_noticia"] = f"{departamento or 'sin especificar departamento'}, {municipio or 'sin especificar municipio'}"

        lstEventos.append(evento)

with open(os.path.join(output_dir, "noticias_estandarizadas_COLOMBIANO20052025.json"), "w", encoding="utf-8") as f:
    json.dump(lstEventos, f, ensure_ascii=False, indent=4)