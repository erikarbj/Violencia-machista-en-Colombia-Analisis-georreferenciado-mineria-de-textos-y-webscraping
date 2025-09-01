
# librerias
from datetime import datetime
from lxml import html
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os
import pandas as pd
import requests
import time

origen = "elespectador"

# Invocar el servicio webArchive
url = 'https://web.archive.org/cdx/search/cdx'
parametros = {'url': 'www.elespectador.com', 'from': '20160101', 'to': '20251231'}

try:
    respuesta = requests.get(url, params=parametros, timeout=100)
    respuesta.raise_for_status()
    rtaWebArchive = respuesta.text
except requests.exceptions.RequestException as e:
    raise Exception(f"Error en la solicitud: {e}")

lstSnapWebArchive = rtaWebArchive.strip().split('\n')

snapShotsWebArchive = {}
for snap in lstSnapWebArchive:
    snapFecha = snap.split(' ')[1]
    fecha = datetime.strptime(snapFecha, "%Y%m%d%H%M%S")
    snapShotsWebArchive[fecha.date()] = snapFecha

urlsArticulos = {}

start_time = datetime.now()
for fecha, item in snapShotsWebArchive.items():
    print(f"Fecha: {fecha}, Último item: {item}")
    
    linkPagina = f'https://web.archive.org/web/{item}/https://www.elespectador.com/'
    try:
        respuesta = requests.get(linkPagina, timeout=100)
        respuesta.raise_for_status()
        rtaHtml = html.fromstring(respuesta.text)
    except requests.exceptions.RequestException as e:
        print(f"Error en item {item}: {e}")
        time.sleep(30)
        continue

    enlaces = rtaHtml.xpath('//a')

    palabras_clave = ["abuso sexual","acoso sexual","acoso callejero","agresion sexual","ciberviolencia","feminicidio","grooming","explotacion sexual","matrimonio forzado","mutilacion genital","sumision quimica","trata de mujeres","violencia machista","machismo","violacion","violaciones","violencia bajo el efecto de sustancias","violencia de genero","violencia digital","violencia domestica","violencia familiar","violencia intrafamiliar","violencia economica","violencia vicaria","violencia psicologica","violencia sexual","violencia sobre la salud sexual y reproductiva","misoginia","asesinatos de mujeres","dominacion masculina","techo de cristal","violencia contra la mujer","violencia docente","violencia en la comunidad","violencia familiar","violencia fisica","violencia institucional","violencia laboral","violencia patrimonial","discriminacion contra la mujer","estupro","hostigamiento sexual","microagresiones","sexismo","violencia simbolica","acoso laboral","acceso carnal violento","acto sexual violento","induccion a la prostitucion","constreÃ±imiento a la prostitucion","violencia sexual cibernetica","pornografia"]
    for element in enlaces:
        href = element.get('href')
        if href and any(palabra in element.text_content().lower() for palabra in palabras_clave):
            if href.startswith('/web/'):  # link archivado
                recortado = href[href.find('http'):]
                if recortado.startswith('http'):
                    urlsArticulos[recortado.replace('http:', 'https:')] = item

archivoControl = [f"Fecha: {snap}, Artículo: {articulo}" for articulo, snap in urlsArticulos.items()]
df = pd.DataFrame({'': archivoControl})
df.to_csv('log_ejecuciones/archivoControlEspectadoor_2016.csv', index=False)

end_time = datetime.now()
print(f'Duration Extraccion Urls: {end_time - start_time}')

# Inicializa webDriver Chrome 
options = webdriver.ChromeOptions()
options.add_argument('--disable-extensions')
options.add_argument('--blink-settings=imagesEnabled=false')

s = Service(os.path.dirname(os.path.abspath(__file__)) + '/chromedriver.exe')
driver = webdriver.Chrome(options=options, service=s)
count = 0
articuloError = []

for articulo, snap in urlsArticulos.items():
    linkArticulo = f'https://web.archive.org/web/{snap}/{articulo}'
    try:
        driver.get(linkArticulo)
        WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        if "Wayback Machine" in driver.title and ("has not been archived" in driver.page_source or "is not available" in driver.page_source):
            articuloError.append(f"Not archived: {linkArticulo}")
            continue

    except Exception as e:
        articuloError.append(f"Error loading: {linkArticulo} - {str(e)}")
        continue

    titulo = "NONE"
    subtitulo = "NONE"
    contenido = []
    articulo_texto = []

    posibles_selectores_titulo = [
        (By.TAG_NAME, "h1"),
        (By.TAG_NAME, "h2"),
        (By.CSS_SELECTOR, ".article-title"),
        (By.CSS_SELECTOR, ".title"),
        (By.CSS_SELECTOR, "[itemprop='headline']"),
        (By.CSS_SELECTOR, "header h1")
    ]

    for by, selector in posibles_selectores_titulo:
        try:
            element = driver.find_element(by, selector)
            if element.is_displayed():
                titulo = element.text
                break
        except NoSuchElementException:
            continue

    if titulo == "NONE":
        for by, selector in posibles_selectores_titulo[1:]:
            try:
                element = driver.find_element(by, selector)
                if element.is_displayed():
                    subtitulo = element.text
                    break
            except NoSuchElementException:
                continue

    posibles_selectores_contenido = [
        (By.CLASS_NAME, "articulo-contenido"),
        (By.CLASS_NAME, "article-content"),
        (By.CLASS_NAME, "paragraph"),
        (By.CSS_SELECTOR, "[itemprop='articleBody']"),
        (By.CLASS_NAME, "contenido"),
        (By.TAG_NAME, "article")
    ]

    for by, selector in posibles_selectores_contenido:
        try:
            contenedores = driver.find_elements(by, selector)
            for contenedor in contenedores:
                if contenedor.is_displayed():
                    try:
                        parrafos = contenedor.find_elements(By.TAG_NAME, "p")
                        for p in parrafos:
                            texto = p.text.strip()
                            if texto and not texto.startswith(('(', '-', '©', 'Lea también:')):
                                contenido.append(texto)
                    except:
                        texto = contenedor.text.strip()
                        if texto:
                            lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
                            contenido.extend(lineas)
            if contenido:
                break
        except NoSuchElementException:
            continue

    if (titulo != "NONE" or contenido) and not (subtitulo == "Hrm." and titulo == "NONE"):
        articulo_texto.append(titulo)
        articulo_texto.append(subtitulo)
        articulo_texto.extend(contenido)

        try:
            df = pd.DataFrame({linkArticulo: articulo_texto})
            df.to_csv(f'articulos_x_procesar/{origen}_{snap}_{count}.csv', index=False)
            count += 1
        except Exception as e:
            articuloError.append(f"Error saving: {linkArticulo} - {str(e)}")
    else:
        articuloError.append(f"No content: {linkArticulo}")

driver.quit()

if articuloError:
    df3 = pd.DataFrame({'Errores': articuloError})
    df3.to_csv('log_ejecuciones/articulosErrorEspectadoor_2016.csv', index=False)