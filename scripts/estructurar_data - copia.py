"""
@author: Ingrid Rodriguez
"""
import pandas as pd
import os
import re
import json
import spacy 
from datetime import datetime
import pycountry

# Expresiones regulares de fecha
regex_formato_textual = r'\b\d{1,2}\sde\s(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s(?:de|del)\s\d{4}\b'
regex_mes_antes = r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s\d{1,2},?\s\d{4}\b'
regex_formato_numerico = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
regex_formato_iso = r'\b\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b'
regex_fechas = [regex_formato_textual, regex_mes_antes, regex_formato_numerico, regex_formato_iso]

meses = {
    'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2,
    'marzo': 3, 'mar': 3, 'abril': 4, 'abr': 4,
    'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6, 
    'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8,
    'septiembre': 9, 'sep': 9, 'octubre': 10, 'oct': 10, 
    'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
}

# Patrones para detectar expresiones asociadas a la violencia machista
patrones_delitos = {
    "feminicidio": r"feminicid\w+",
    "violencia machista": r"violencia\s+machista",
    "violencia contra la mujer": r"violencia\s+contra\s+la\s+mujer",
    "violencia de género": r"violencia\s+de\s+género",
    "violencia doméstica": r"violencia\s+doméstica",
    "acoso sexual": r"acoso\s+sexual",
    "abuso sexual": r"abuso\s+sexual",
    "acoso callejero": r"acoso\s+callejero",
    "ciberviolencia": r"ciberviolencia",
    "explotación sexual": r"explotaci\w+\s+sexual",
    "mutilación genital": r"mutilaci\w+\s+genital",
    "matrimonio forzado": r"matrimonio\s+forzado",
    "trata de mujeres": r"trata\s+de\s+mujer\w*",
    "sumisión química": r"sumisión\s+química",
    "violencia bajo el efecto de sustancias": r"violencia\s+bajo\s+el\s+efecto\s+de\s+sustancia",
    "violencia digital": r"violencia\s+digital",
    "violencia familiar": r"violencia\s+familiar",
    "violencia intrafamiliar": r"violencia\s+intrafamiliar",
    "violencia vicaria": r"violencia\s+vicaria",
    "violencia económica": r"violencia\s+económica",
    "violencia psicológica": r"violencia\s+psicológica",
    "machismo": r"machismo",
    "grooming": r"grooming",
    "violaciones": r"violacion\w*",
    "maltrato a mujeres": r"maltrat\w+\s+a\s+mujer\w*",
    "hostigamiento": r"hostigamiento",
    "agresión sexual": r"agresi\w+\s+sexual",
    "violación": r"violación",
    "violencia sexual": r"violencia\s+sexual",
    "violencia sobre la salud sexual y reproductiva": r"violencia\s+sobre\s+la\s+salud\s+sexual\s+y\s+reproductiva",
    "misoginia": r"misoginia",
    "asesinatos de mujeres": r"asesinatos\s+de\s+mujer\w*",
    "dominación masculina": r"dominación\s+masculina",
    "techo de cristal": r"techo\s+de\s+cristal",
    "violencia contra la mujer": r"violencia\s+contra\s+la\s+mujer",
    "violencia docente": r"violencia\s+docente",
    "violencia en la comunidad": r"violencia\s+en\s+la\s+comunidad",
    "violencia familiar": r"violencia\s+familiar",
    "violencia física": r"violencia\s+física",
    "violencia institucional": r"violencia\s+institucional",
    "violencia laboral": r"violencia\s+laboral",
    "violencia patrimonial": r"violencia\s+patrimonial",
    "discriminación contra la mujer": r"discriminación\s+contra\s+la\s+mujer",
    "estupro": r"estupro",
    "hostigamiento sexual": r"hostigamiento\s+sexual",
    "microagresiones": r"microagresiones",
    "sexismo": r"sexismo",
    "violencia simbólica": r"violencia\s+simbólica",
    "acoso laboral": r"acoso\s+laboral",
    "acceso carnal violento": r"acceso\s+carnal\s+violento",
    "acto sexual violento": r"acto\s+sexual\s+violento",
    "inducción a la prostitución": r"inducción\s+a\s+la\s+prostitución",
    "constreñimiento a la prostitución": r"constreñimiento\s+a\s+la\s+prostitución",
    "violencia sexual cibernética": r"violencia\s+sexual\s+cibernética",
    "pornografía": r"pornografía"
}

def normalizar_delito(texto_delito):
    for delito, patron in patrones_delitos.items():
        # Usamos search para encontrar coincidencias en cualquier parte del texto
        if re.search(patron, texto_delito.lower()):
            return delito
    return texto_delito

# Cargar municipios y departamentos de Colombia
df_depmun = pd.read_csv("datos_base/Departamentos_y_municipios_de_Colombia.csv")
municipios = set(df_depmun['MUNICIPIO'].str.lower())
departamentos = set(df_depmun['DEPARTAMENTO'].str.lower())
paises = {country.name for country in pycountry.countries}

def verificar_localizacion(localizacion):
    localizacion_lower = localizacion.lower()
    if localizacion_lower in municipios:
        return "Municipio"
    elif localizacion_lower in departamentos:
        return "Departamento"
    else:
        return "No encontrado"

def obtener_departamento(municipio):
    resultado = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    return resultado.iloc[0]['DEPARTAMENTO'] if not resultado.empty else "Sin especificar"

# Cargar modelo de spaCy para español
nlp = spacy.load("es_core_news_lg")
palabrasExcluir = nlp.Defaults.stop_words
palabrasExcluir.add("el tiempo")

lstEventos = []
os.chdir('articulos_x_procesar/')
files_csv = os.listdir()

for i in files_csv:
    evento = {}
    df = pd.read_csv(i)
    df_text = df.to_string()
    
    # Extraer el título del artículo (suponiendo que está en la segunda línea)
    evento["tituloarticulo"] = df_text.split('\n')[1][1:].strip()
    # Extraer la fecha a partir del nombre del archivo (asumiendo un formato en el nombre)
    evento["fechaarticulo"] = datetime.strptime(i.split('_')[1], '%Y%m%d%H%M%S').date().isoformat()
    
    doc = nlp(df_text)
    # Filtrar entidades ya reconocidas (localizaciones y personas)
    ents_filtradas = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]
    
    # Buscar términos de violencia machista en el texto y agregarlos como entidad DELITO
    delitos_encontrados = []
    for delito, patron in patrones_delitos.items():
        for match in re.finditer(patron, df_text.lower()):
            start, end = match.span()
            delitos_encontrados.append((start, end, delito))
    
    for start, end, delito in delitos_encontrados:
        span = doc.char_span(start, end, label="DELITO")
        if span is not None:
            # Evitar solapamientos con otras entidades
            overlapping = any(ent.start < span.end and span.start < ent.end for ent in doc.ents)
            if not overlapping:
                ents_filtradas.append(span)
    
    # Actualizar las entidades del documento con las detectadas
    doc.ents = ents_filtradas
    
    municipio, departamento, paisEncontrado = "", "", ""
    delitos_relacionados, personas_involucradas = [], []
    
    for ent in doc.ents:
        if ent.label_ == "DELITO":
            delitos_relacionados.append(normalizar_delito(ent.text))
        elif ent.label_ == "LOC":
            tipo = verificar_localizacion(ent.text)
            if tipo == "Municipio" and municipio == "":
                municipio = ent.text
                departamento = obtener_departamento(municipio)
            elif tipo == "Departamento" and departamento == "":
                municipio = "Sin especificar"
                departamento = ent.text
            elif ent.text in paises:
                paisEncontrado = ent.text
        elif ent.label_ == "PER":
            persona_detectada = ent.text
            if persona_detectada not in personas_involucradas and persona_detectada.lower() not in palabrasExcluir:
                personas_involucradas.append(persona_detectada)
    
    evento["delitos_relacionados"] = list(set(delitos_relacionados))
    evento["pais"] = "Colombia" if paisEncontrado == "Colombia" or departamento != "" else "Otros Paises"
    evento["departamento"] = departamento if departamento != "" else "Sin especificar"
    evento["municipio"] = municipio if municipio != "" else "Sin especificar"
    evento["personas_involucradas"] = list(set(personas_involucradas))
    
    lstEventos.append(evento)

with open("C:/Users/Asus/TFM_CREDITOS/TFM2/Pruebas_Erika/noticias_estandarizadasCol.json", "w", encoding="utf-8") as archivo:
    json.dump(lstEventos, archivo, ensure_ascii=False, indent=4)