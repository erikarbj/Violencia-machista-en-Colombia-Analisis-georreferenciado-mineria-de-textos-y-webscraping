"""
@author: Ingrid Rodriguez
"""
import pandas as pd
#import nltk
import os
import re
#from nltk.probability import FreqDist
#from nltk.corpus import stopwords
import json
import spacy 
#from spacy.tokens import Span
from datetime import datetime
import pycountry

###############################################################
###############################################################
#Expresiones regulares de fecha
# Formato 12 de septiembre de|del 2023
regex_formato_textual = r'\b\d{1,2}\sde\s(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s(?:de|del)\s\d{4}\b'
# Formato Septiembre 12, 2023 o Sept 12, 2023
regex_mes_antes = r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\s\d{1,2},?\s\d{4}\b'
# Formato dd/mm/yyyy o dd-mm-yyyy
regex_formato_numerico = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
# Formato yyyy-mm-dd o yyyy/mm/dd
regex_formato_iso = r'\b\d{2,4}[-/]\d{1,2}[-/]\d{1,2}\b'
# Combinar todas las expresiones regulares en una lista
regex_fechas = [regex_formato_textual, regex_mes_antes, regex_formato_numerico, regex_formato_iso]
###############################################################
# Diccionario para convertir meses en español a números
meses = {
    'enero': 1, 'ene': 1, 'febrero': 2, 'feb': 2,
    'marzo': 3, 'mar': 3, 'abril': 4, 'abr': 4,
    'mayo': 5, 'may': 5, 'junio': 6, 'jun': 6, 
    'julio': 7, 'jul': 7, 'agosto': 8, 'ago': 8,
    'septiembre': 9, 'sep': 9, 'octubre': 10, 'oct': 10, 
    'noviembre': 11, 'nov': 11, 'diciembre': 12, 'dic': 12
}
###############################################################
###### Funcion convertir_a_fecha
def convertir_a_fecha(fecha_str):
    # Probar con cada expresión regular
    for expresion in regex_fechas:
        coincidencia = re.search(expresion, fecha_str)
        
        if coincidencia:
            if expresion == regex_fechas[0]:  # Caso: "5 de diciembre de 2016"
                dia = int(re.search(r'\d{1,2}', coincidencia.group()).group())
                mes_texto = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', coincidencia.group()).group().lower()
                anio = int(re.search(r'\d{4}', coincidencia.group()).group())
                mes = meses[mes_texto]  # Convertir el mes en texto a número
            elif expresion == regex_fechas[1]:  # Caso: "diciembre 5, 2016" o "dic 5, 2016"
                mes_texto = re.search(r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', coincidencia.group()).group().lower()
                dia = int(re.search(r'\d{1,2}', coincidencia.group()).group())
                anio = int(re.search(r'\d{4}', coincidencia.group()).group())
                mes = meses[mes_texto]
            elif expresion == regex_fechas[2]:  # Caso: "05/12/16", "12/05/2016", "05-12-16"
                partes = re.split('[-/]', coincidencia.group())
                dia = int(partes[0])
                mes = int(partes[1])
                anio = int(partes[2])
            elif expresion == regex_fechas[3]:  # Caso: "16/05/12", "2016/12/05", "16-05-12"
                partes = re.split('[-/]', coincidencia.group())
                anio = int(partes[2])
                mes = int(partes[1])
                dia = int(partes[0])
                
            # Manejar años con 2 dígitos (asumir 2000 si es menor a 100)
            if anio < 100:
                anio += 2000
            
            # Si día es mayor a 31 se asume error y se cambia a 01
            if dia > 31:
                dia = 1
            
            # Crear el objeto datetime
            fecha = datetime(anio, mes, dia)
            
            # Convertir al formato yyyymmdd
            # return fecha.strftime('%Y%m%d')
            return fecha.date().isoformat()
    
    return "No se encontró una fecha en un formato válido."
###############################################################
###############################################################
# Expresiones regulares para detectar delitos y variaciones

patrones_delitos = {
    "abuso sexual": r"abuso\s+sexual",
    "acoso sexual": r"acoso\s+sexual",
    "acoso callejero": r"acoso\s+callejer\w+",
    "agresión sexual": r"agresi[oó]n\s+sexual",
    "ciberviolencia": r"ciberviolenc\w+",
    "feminicidio": r"feminicid\w+",
    "grooming": r"grooming",
    "explotación sexual": r"explotaci[oó]n\s+sexual",
    "matrimonio forzado": r"matrimonio\s+forzad\w+",
    "mutilación genital": r"mutilaci[oó]n\s+genital",
    "sumisión química": r"sumisi[oó]n\s+qu[ií]mic\w+",
    "trata de mujeres": r"trata\s+de\s+mujer\w+",
    "violencia machista": r"violencia\s+machist\w+",
    "machismo": r"machism\w+",
    "violación": r"violaci[oó]n|violaci[oó]nes|viola\w+",
    "violencia bajo el efecto de sustancias": r"violencia\s+bajo\s+el\s+efecto\s+de\s+sustancias",
    "violencia de género": r"violencia\s+de\s+g[eé]nero",
    "violencia digital": r"violencia\s+digital",
    "violencia doméstica": r"violencia\s+dom[eé]stic\w+",
    "violencia familiar": r"violencia\s+familiar",
    "violencia intrafamiliar": r"violencia\s+intrafamiliar",
    "violencia económica": r"violencia\s+econ[oó]mic\w+",
    "violencia vicaria": r"violencia\s+vicari\w+",
    "violencia psicológica": r"violencia\s+psicol[oó]gic\w+",
    "violencia sexual": r"violencia\s+sexual",
    "violencia sobre la salud sexual y reproductiva": r"violencia\s+sobre\s+la\s+salud\s+sexual\s+y\s+reproductiva",
    "misoginia": r"misogini\w+",
    "asesinatos de mujeres": r"asesinat\w+\s+de\s+mujer\w+",
    "dominación masculina": r"dominaci[oó]n\s+masculin\w+",
    "techo de cristal": r"techo\s+de\s+cristal",
    "violencia contra la mujer": r"violencia\s+contra\s+la\s+mujer",
    "violencia docente": r"violencia\s+docent\w+",
    "violencia en la comunidad": r"violencia\s+en\s+la\s+comunidad",
    "violencia física": r"violencia\s+f[ií]sic\w+",
    "violencia institucional": r"violencia\s+institucional",
    "violencia laboral": r"violencia\s+laboral",
    "violencia patrimonial": r"violencia\s+patrimonial",
    "discriminación contra la mujer": r"discriminaci[oó]n\s+contra\s+la\s+mujer",
    "estupro": r"estupro",
    "hostigamiento sexual": r"hostigamient\w+\s+sexual",
    "microagresiones": r"microagresi[oó]n|microagresiones",
    "sexismo": r"sexism\w+",
    "violencia simbólica": r"violencia\s+simb[oó]lic\w+",
    "acoso laboral": r"acoso\s+laboral",
    "acceso carnal violento": r"acceso\s+carnal\s+violent\w+",
    "acto sexual violento": r"acto\s+sexual\s+violent\w+",
    "inducción a la prostitución": r"inducci[oó]n\s+a\s+la\s+prostituci[oó]n",
    "constreñimiento a la prostitución": r"constre[ñn]imient\w+\s+a\s+la\s+prostituci[oó]n",
    "violencia sexual cibernética": r"violencia\s+sexual\s+cibern[eé]tic\w+",
    "pornografía": r"pornograf\w+"
}


###### Funcion para normalizar delitos a un solo nombre donde la py --version base de las expresiones regulares se mantengan
# Función para normalizar delitos a una forma estándar
def normalizar_delito(texto_delito):
   
# Sexual / abuso
    if re.match(r"abuso\s+sexual", texto_delito.lower()):
        return "abuso sexual"
    if re.match(r"acoso\s+sexual|acoso\s+callejer\w+", texto_delito.lower()):
        return "acoso sexual"
    if re.match(r"agresi[oó]n\s+sexual", texto_delito.lower()):
        return "agresión sexual"
    if re.match(r"hostigamient\w+\s+sexual", texto_delito.lower()):
        return "hostigamiento sexual"
    if re.match(r"grooming", texto_delito.lower()):
        return "grooming"
    if re.match(r"explotaci[oó]n\s+sexual", texto_delito.lower()):
        return "explotación sexual"
    if re.match(r"estupro", texto_delito.lower()):
        return "estupro"
    if re.match(r"acceso\s+carnal\s+violent\w+", texto_delito.lower()):
        return "acceso carnal violento"
    if re.match(r"acto\s+sexual\s+violent\w+", texto_delito.lower()):
        return "acto sexual violento"
    if re.match(r"inducci[oó]n\s+a\s+la\s+prostituci[oó]n|constre[ñn]imient\w+\s+a\s+la\s+prostituci[oó]n", texto_delito.lower()):
        return "inducción a la prostitución"
    if re.match(r"pornograf\w+", texto_delito.lower()):
        return "pornografía"

    # Violencia de género
    if re.match(r"feminicid\w+", texto_delito.lower()):
        return "feminicidio"
    if re.match(r"violaci[oó]n|violaci[oó]nes|viola\w+", texto_delito.lower()):
        return "violación"
    if re.match(r"violencia\s+machist\w+|machism\w+", texto_delito.lower()):
        return "violencia machista"
    if re.match(r"misogini\w+", texto_delito.lower()):
        return "misoginia"
    if re.match(r"asesinat\w+\s+de\s+mujer\w+", texto_delito.lower()):
        return "asesinatos de mujeres"
    if re.match(r"dominaci[oó]n\s+masculin\w+", texto_delito.lower()):
        return "dominación masculina"
    if re.match(r"techo\s+de\s+cristal", texto_delito.lower()):
        return "techo de cristal"
    if re.match(r"discriminaci[oó]n\s+contra\s+la\s+mujer", texto_delito.lower()):
        return "discriminación contra la mujer"

    # Violencia en general
    if re.match(r"violencia\s+bajo\s+el\s+efecto\s+de\s+sustancias", texto_delito.lower()):
        return "violencia bajo el efecto de sustancias"
    if re.match(r"violencia\s+de\s+g[eé]nero", texto_delito.lower()):
        return "violencia de género"
    if re.match(r"violencia\s+digital|ciberviolenc\w+|violencia\s+sexual\s+cibern[eé]tic\w+", texto_delito.lower()):
        return "violencia digital"
    if re.match(r"violencia\s+dom[eé]stic\w+", texto_delito.lower()):
        return "violencia doméstica"
    if re.match(r"violencia\s+familiar|violencia\s+intrafamiliar", texto_delito.lower()):
        return "violencia familiar"
    if re.match(r"violencia\s+econ[oó]mic\w+", texto_delito.lower()):
        return "violencia económica"
    if re.match(r"violencia\s+vicari\w+", texto_delito.lower()):
        return "violencia vicaria"
    if re.match(r"violencia\s+psicol[oó]gic\w+", texto_delito.lower()):
        return "violencia psicológica"
    if re.match(r"violencia\s+sexual", texto_delito.lower()):
        return "violencia sexual"
    if re.match(r"violencia\s+sobre\s+la\s+salud\s+sexual\s+y\s+reproductiva", texto_delito.lower()):
        return "violencia sobre la salud sexual y reproductiva"
    if re.match(r"violencia\s+contra\s+la\s+mujer", texto_delito.lower()):
        return "violencia contra la mujer"
    if re.match(r"violencia\s+docent\w+", texto_delito.lower()):
        return "violencia docente"
    if re.match(r"violencia\s+en\s+la\s+comunidad", texto_delito.lower()):
        return "violencia en la comunidad"
    if re.match(r"violencia\s+f[ií]sic\w+", texto_delito.lower()):
        return "violencia física"
    if re.match(r"violencia\s+institucional", texto_delito.lower()):
        return "violencia institucional"
    if re.match(r"violencia\s+laboral|acoso\s+laboral", texto_delito.lower()):
        return "violencia laboral"
    if re.match(r"violencia\s+patrimonial", texto_delito.lower()):
        return "violencia patrimonial"
    if re.match(r"microagresi[oó]n|microagresiones", texto_delito.lower()):
        return "microagresiones"
    if re.match(r"sexism\w+", texto_delito.lower()):
        return "sexismo"
    if re.match(r"violencia\s+simb[oó]lic\w+", texto_delito.lower()):
        return "violencia simbólica"

    # Otros específicos
    if re.match(r"matrimonio\s+forzad\w+", texto_delito.lower()):
        return "matrimonio forzado"
    if re.match(r"mutilaci[oó]n\s+genital", texto_delito.lower()):
        return "mutilación genital"
    if re.match(r"sumisi[oó]n\s+qu[ií]mic\w+", texto_delito.lower()):
        return "sumisión química"
    if re.match(r"trata\s+de\s+mujer\w+", texto_delito.lower()):
        return "trata de mujeres"




    return texto_delito
###############################################################
# Cargar la lista de municipios y departamentos desde un archivo CSV
df_depmun = pd.read_csv("datos_base/Departamentos_y_municipios_de_Colombia.csv")

# Crear conjuntos para buscar más rápido
municipios = set(df_depmun['MUNICIPIO'].str.lower())
departamentos = set(df_depmun['DEPARTAMENTO'].str.lower())

# Crear listado de paises
paises = {country.name for country in pycountry.countries}
###############################################################
###############################################################
###### Funcion para normalizar delitos a un solo nombre donde la base de las expresiones regulares se mantengan
# Función para verificar si una localización es un municipio o un departamento
def verificar_localizacion(localizacion):
    localizacion_lower = localizacion.lower()
    if localizacion_lower in municipios:
        return "Municipio"
    elif localizacion_lower in departamentos:
        return "Departamento"
    else:
        return "No encontrado"
###############################################################
###############################################################    
# Función para retornar el departamento de un municipio
def obtener_departamento(municipio):
    # Filtrar la fila correspondiente al municipio
    resultado = df_depmun[df_depmun['MUNICIPIO'].str.lower() == municipio.lower()]
    
    # Verificar si se encontró el municipio
    if not resultado.empty:
        # Retornar el departamento asociado al municipio
        return resultado.iloc[0]['DEPARTAMENTO']
    else:
        # Si no se encuentra el municipio, retornar un mensaje
        return f"Sin especificar"
###############################################################

indice = []
# Directorio de trabajo
os.chdir('articulos_x_procesar/')
files_csv = os.listdir()
nlp = spacy.load("es_core_news_lg")  # Modelo para español
palabrasExcluir = nlp.Defaults.stop_words #listado de stopwords de spacy usado para filtros posteriores
palabrasExcluir.add("el tiempo")

lstEventos = []
df = pd.DataFrame()
for i in files_csv:
    print(i)
    #Se inicializa el diccionario
    evento = {}
    # Formación del data frame a través de la lectura del archivo
    df = pd.read_csv(i)
    # Contenido del campo texto del data frame
    df_text = df.to_string()
    
    ###############################################################
    # Agregar el titulo del articulo
    tituloarticulo = df_text.split('\n')[1][1:].strip()
    evento["tituloarticulo"] = tituloarticulo
    
    #Tokenizacion de titulos
    doc_titulo = nlp(tituloarticulo)
    evento["tokenizaciontitulo"] = [token.text for token in doc_titulo if not token.is_stop and not token.is_punct]   
    
    ###############################################################
    # Agregar fecha del articulo
    fechaarticulo = datetime.strptime(i.split('_')[1], '%Y%m%d%H%M%S').date().isoformat()
    evento["fechaarticulo"] = fechaarticulo
    
    ###############################################################
    # Buscar fechas en el texto usando expresiones regulares
    fechas = []
    for regex in regex_fechas:
        fechas.extend(re.findall(regex, df_text.lower()))
    
    #Conversion de fechas de texto a tipo date
    fechas_sinduplicados = list(set(fechas))
    fechas_date = []
    for fecha in fechas_sinduplicados:
        fecha_formato = convertir_a_fecha(fecha)
        fechas_date.append(fecha_formato)

    # Obtener la menor fecha y adicionarla al diccionario de eventos de asesinatos si existen fechas
    fecha_menor = ''
    if len(fechas_date) > 0:
        fecha_menor = min(fechas_date)
        
    if fecha_menor :
        evento["fechaevento"] = fecha_menor
        evento["fechaestimada"] = fecha_menor
    else:
        evento["fechaestimada"] = fechaarticulo 
    
    ###############################################################
    #Buscar otros delitos expuestos usando expresiones regulares y adicionando los resultados a las entidades de Spacy
    # Procesar el texto con SpaCy
    doc = nlp(df_text)
    # Filtrar las entidades para mantener solo 'LOC' y 'PER'
    ents_filtradas = [ent for ent in doc.ents if ent.label_ in ["LOC", "PER"]]
    delitos_encontrados = []
    for delito, patron in patrones_delitos.items():
        # Buscar todas las coincidencias del patrón de delito
        for match in re.finditer(patron, df_text.lower()):
            start, end = match.span()  # Obtener el inicio y fin de la coincidencia
            delitos_encontrados.append((start, end, delito))
            # span = Span(doc, doc.char_span(start, end).start, doc.char_span(start, end).end, label="DELITO")
            # ents_filtradas.append(span)
    
    # Verificar superposición de entidades antes de agregar las nuevas entidades de tipo DELITO
    for start, end, delito in delitos_encontrados:
        span = doc.char_span(start, end, label="DELITO")
        
        # Asegurarse de que el span no es None y no se solape con otras entidades
        if span is not None:
            overlapping = False
            for ent in doc.ents:
                # Verifica si los spans se solapan
                if ent.start < span.end and span.start < ent.end:
                    overlapping = True
                    break
            if not overlapping:
                ents_filtradas.append(span)

    # Actualizar las entidades del documento con las nuevas entidades detectadas y filtradas
    doc.ents = ents_filtradas
    
    municipio = ""
    departamento = ""
    paisEncontrado = ""
    delitos_relacionados = []
    personas_involucradas = []
    for ent in doc.ents:
        if ent.label_ == "DELITO":
            delito_normalizado = normalizar_delito(ent.text)
            delitos_relacionados.append(delito_normalizado)
        elif ent.label_ == "LOC": # Verificar cada localización detectada
            tipo = verificar_localizacion(ent.text)
            if tipo == "Municipio" and municipio == "": #Tomar como ubicacion del evento el primer municipio o departamento mencionado en el texto
                municipio = ent.text
                departamento = obtener_departamento(municipio)
            elif tipo == "Departamento" and departamento == "":
                municipio = "Sin especificar"
                departamento = ent.text
            elif ent.text in paises :
                paisEncontrado = ent.text
        elif ent.label_ == "PER": # Verificar cada persona detectada
            persona_detectada = ent.text
            if persona_detectada not in personas_involucradas and persona_detectada.lower() not in palabrasExcluir and persona_detectada.find("http") == -1:
                personas_involucradas.append(persona_detectada)
    
    # Adicionar al diccionario de eventos de asesinatos los delitos relacionados si existen
    delitos_sinduplicados = list(set(delitos_relacionados))
    if len(delitos_sinduplicados) > 0:
        evento["delitos_relacionados"] = delitos_sinduplicados
    
    # Adicionar al diccionario de eventos la ubicacion del evento si existe
    if paisEncontrado != "":
        evento["pais"] = "Colombia" if paisEncontrado == "Colombia" or departamento != "" else "Otros Paises"

    if departamento != "":
        evento["pais"] = "Colombia"
        evento["departamento"] = departamento
        evento["municipio"] = municipio

    # Adicionar al diccionario de eventos de asesinatos las personas relacionadas si existen
    personas_involucradas_sinduplicados = list(set(personas_involucradas))
    personas_involucradas_sinduplicados.sort(key=len, reverse=True)
    personas_involucradas_procesado = []

    # Iteramos sobre cada persona en la lista ordenada
    for persona in personas_involucradas_sinduplicados:
        # Comprobamos si 'persona' no está contenida en ninguna de las ya añadidas a resultados_finales
        if not any(persona in personaB for personaB in personas_involucradas_procesado):
            personas_involucradas_procesado.append(persona)
    
    if len(personas_involucradas_procesado) > 0:
        evento["personas_involucradas"] = personas_involucradas_procesado
    ##################################################################################################
    lstEventos.append(evento)
    #print(evento)

#################################################################################################
# Escribir los datos al archivo JSON
with open("C:/Users/Asus/TFM_CREDITOS/TFM2/Pruebas_Erika/noticias_estandarizadasCol.json", "w", encoding="utf-8") as archivo:
    json.dump(lstEventos, archivo, ensure_ascii=False, indent=4)