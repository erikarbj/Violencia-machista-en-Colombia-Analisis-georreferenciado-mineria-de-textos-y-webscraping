#librerias
from datetime import datetime
from lxml import html
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import os
import pandas as pd
import requests
import time

origen = "elheraldo"

# Invocar el servicio webArchive para obtener los resultados del historico
url = 'https://web.archive.org/cdx/search/cdx'
parametros = {'url': 'www.elheraldo.co', 'from': '20160101', 'to': '20251231' }
headers = {'Accept': '*/*'}

rtaWebArchive = ''
try:
    respuesta = requests.get(url, params=parametros, timeout=100)

    if respuesta.status_code == 200:
        rtaWebArchive = respuesta.text
    else:
        raise Exception(f"Error: Código de estado {respuesta.status_code}")

except requests.exceptions.RequestException as e:
    raise Exception(f"Error en la solicitud: {e}")


lstSnapWebArchive = rtaWebArchive.strip().split('\n')

snapShotsWebArchive = {}
for snap in lstSnapWebArchive:
    snapFecha = snap.split(' ')[1]
    fecha = datetime.strptime(snapFecha, "%Y%m%d%H%M%S")
    snapShotsWebArchive[fecha.date()] = snapFecha

urlsArticulos = {}
urlsArticulosV1 = {}
errores = 0
snapError = []
start_time = datetime.now()
# Extracción y almacenamiento de datos de cada página
for fecha, item in snapShotsWebArchive.items():
    
    print(f"Fecha: {fecha}, Último item: {item}")
    
    rtaHtmlSeccionJusticia = ''
    
    linkArticulo = 'https://web.archive.org/web/' + item + '/https://www.elheraldo.co/'
    try:
        respuesta = requests.get(linkArticulo, timeout=100)

        if respuesta.status_code == 200:
            rtaHtmlSeccionJusticia = html.fromstring(respuesta.text)
        else:
            errores += 1
            snapError.append(f"item: {item}")
            print(f"item Error: {item}")
            continue

    except requests.exceptions.RequestException as e:
        errores += 1
        snapError.append(f"item: {item}")
        print(f"item Error: {item}")
        time.sleep(30)
        continue
    
    # Obtener todos los link de la sección
    enlacesEncontrados = rtaHtmlSeccionJusticia.xpath('//a')
    
    # Filtrar URLs en los links que contengan la raíz de palabra ó palabras clave
    palabras_clave = ["abuso sexual","acoso sexual","acoso callejero","agresion sexual","ciberviolencia","feminicidio","grooming","explotacion sexual","matrimonio forzado","mutilacion genital","sumision quimica","trata de mujeres","violencia machista","machismo","violacion","violaciones","violencia bajo el efecto de sustancias","violencia de genero","violencia digital","violencia domestica","violencia familiar","violencia intrafamiliar","violencia economica","violencia vicaria","violencia psicologica","violencia sexual","violencia sobre la salud sexual y reproductiva","misoginia","asesinatos de mujeres","dominacion masculina","techo de cristal","violencia contra la mujer","violencia docente","violencia en la comunidad","violencia familiar","violencia fisica","violencia institucional","violencia laboral","violencia patrimonial","discriminacion contra la mujer","estupro","hostigamiento sexual","microagresiones","sexismo","violencia simbolica","acoso laboral","acceso carnal violento","acto sexual violento","induccion a la prostitucion","constreÃ±imiento a la prostitucion","violencia sexual cibernetica","pornografia"]
    linksInteres = [
        element.get('href') 
        for element in enlacesEncontrados 
        if any(palabra in element.text_content().lower() for palabra in palabras_clave)
    ]

    # Referencias de las páginas 
    for link in linksInteres:
        link = link[20:]
        link = link[link.find('http'):]
        if link.find('www') > 0 :
            urlsArticulos[link.replace("http:", "https:")] = item

archivoControl = []
for articulo, snap in urlsArticulos.items():
    archivoControl.append(f"Fecha: {snap}, Artículo: {articulo}")
    
df = pd.DataFrame({'':archivoControl})
df.to_csv('log_ejecuciones/archivoControlHeraldo_2022V1.csv', index=False)

df2 = pd.DataFrame({'':snapError})
df2.to_csv('log_ejecuciones/erroresHeraldo_2022V1.csv', index=False)

end_time = datetime.now()
print('Duration Extraccion Urls: {}'.format(end_time - start_time))

# Inicializa webDriver Chrome 
options = webdriver.ChromeOptions()
options.add_argument('--disable-extensions')
options.add_argument('--blink-settings=imagesEnabled=false')

s = Service(os.path.dirname(os.path.abspath(__file__)) + '/chromedriver.exe')
driver = webdriver.Chrome(options= options, service = s)
count = 0
articuloError = []

for articulo, snap in urlsArticulos.items():
    linkArticulo = 'https://web.archive.org/web/' + snap +'/'+ articulo
    try:
        # Link de la página
        driver.get(linkArticulo)
        
        # Esperar a que la página cargue completamente
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            articuloError.append(f"Timeout: {linkArticulo}")
            continue
            
        # Verificar si es una página de error de Wayback Machine
        if "Wayback Machine" in driver.title and ("has not been archived" in driver.page_source or "is not available" in driver.page_source):
            articuloError.append(f"Not archived: {linkArticulo}")
            continue
    
    except Exception as e:
        articuloError.append(f"Error loading: {linkArticulo} - {str(e)}")
        continue
    
    # definicion variables de trabajo
    titulo = "NONE"
    subtitulo = "NONE"
    contenido = []
    articulo_texto = []

    # Buscar título de forma más flexible
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
    
    # Buscar subtítulo si no se encontró título
    if titulo == "NONE":
        for by, selector in posibles_selectores_titulo[1:]:  # Omite h1 ya que se probó primero
            try:
                element = driver.find_element(by, selector)
                if element.is_displayed():
                    subtitulo = element.text
                    break
            except NoSuchElementException:
                continue

    # Buscar contenido del artículo
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
                    # Intentar diferentes métodos para extraer párrafos
                    try:
                        parrafos = contenedor.find_elements(By.TAG_NAME, "p")
                        for p in parrafos:
                            texto = p.text.strip()
                            if texto and not texto.startswith(('(', '-', '©', 'Lea también:')):
                                contenido.append(texto)
                    except:
                        # Si no encuentra párrafos, intentar con el texto directo
                        texto = contenedor.text.strip()
                        if texto:
                            lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
                            contenido.extend(lineas)
            
            if contenido:  # Si encontramos contenido, salir del bucle
                break
                
        except NoSuchElementException:
            continue
    
    # Si encontramos título o contenido, guardar el artículo
    if (titulo != "NONE" or contenido) and not (subtitulo == "Hrm." and titulo == "NONE"):
        articulo_texto.append(titulo)
        articulo_texto.append(subtitulo)
        articulo_texto.extend(contenido)
        
        # exportar datos a .csv
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
    df3.to_csv('log_ejecuciones/articulosErrorHeraldo_2022V1.csv', index=False)