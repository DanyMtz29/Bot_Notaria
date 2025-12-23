#Imports indepentientes
import os, time, datetime
from loguru import logger
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

#Imports mios
from Bot.ui_selenium.pages.login_page import LoginPage
from Bot.procesos.procesar_actos import procesar_actos
from Bot.config.rutas import RUTA_PROYECTOS, RUTA_LOGS, RUTA_TEMPORALES, MINIMO_DE_DIAS, CORREOS
from Bot.helpers.logs import tomar_screenshot, registrar_log
from Bot.helpers.json import generar_excel
from Bot.helpers.gmail import enviar_gmail


def make_driver(headless: bool = False, page_load_timeout: int = 60, wait_timeout: int = 20):
    opts = Options()
    if headless:
        # Headless moderno de Chrome
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": RUTA_TEMPORALES,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # fuerza descarga del PDF
    }

    opts.add_experimental_option("prefs", prefs)

    # Selenium Manager resuelve el driver automáticamente
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(page_load_timeout)
    wait = WebDriverWait(driver, wait_timeout)

    return driver, wait

def proceso_por_abogado(headless: bool) -> None:
    # Cargar variables de entorno (.env) una sola vez para este proceso
    load_dotenv("bot/config/.env")

    user = os.getenv("PORTAL_USER", "")
    pwd  = os.getenv("PORTAL_PASS", "")
    
    if not (user and pwd):
        logger.error("Faltan PORTAL_URL/USER/PASS en .env")
        return
    
    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=7)
    
    fecha = datetime.date.today()

    logs_abogado_raiz = os.path.join(RUTA_LOGS, str(fecha))

    attempts = 3
    while attempts > 0:
        try:
            LoginPage(driver,wait).login(user,pwd)
            break
        except Exception as e:
            tomar_screenshot(logs_abogado_raiz, f"Error en login: {e}. Reintentando... ({attempts} intentos restantes)", "ERROR")
            attempts -= 1
            time.sleep(5)
        
    for abogado in os.listdir(RUTA_PROYECTOS):
        ruta_abogado = os.path.abspath(os.path.join(RUTA_PROYECTOS,abogado))
        procesar_actos(driver,wait,abogado,ruta_abogado, ruta_abogado)
        registrar_log(logs_abogado_raiz, f"ABOGADO {abogado} FINALIZADO CORRECTAMENTE", "SUCCESS")
        try:
            if os.path.exists(os.path.join(ruta_abogado,"bitacora.json")):
                ruta_excel = generar_excel(ruta_abogado)
                enviar_gmail(logs_abogado_raiz,CORREOS[abogado], F"RESUMEN DE PROYECTOS DE HACE {MINIMO_DE_DIAS} DÍAS", 
                            "En el siguiente reporte se adjuntan los documentos faltantes en algunos proyectos","",ruta_excel)
        except Exception as e:
            registrar_log(logs_abogado_raiz, f"Error enviando correo a {abogado}: {e}", "ERROR")
