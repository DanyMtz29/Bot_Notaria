from dotenv import load_dotenv
from bot.utils.common_imports import *

from bot.pages.login_page import LoginPage
from bot.Proceso.procesar_actos import procesar_actos

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

def make_driver(headless: bool = False, page_load_timeout: int = 60, wait_timeout: int = 20):
    opts = Options()
    if headless:
        # Headless moderno de Chrome
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    download_dir = os.path.join(os.getcwd(), "bot", "_cache_bot")

    prefs = {
        "download.default_directory": download_dir,
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
    abogados_root = os.getenv("LOCAL_ACTOS_ROOT", "")
    
    if not (user and pwd and abogados_root):
        logger.error("Faltan PORTAL_URL/USER/PASS y/o ACTOS_ROOT en .env")
        return
    
    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=7)

    attempts = 3
    while attempts > 0:
        try:
            LoginPage(driver,wait).login(user,pwd)
            break
        except Exception as e:
            attempts -= 1
            logger.error(f"Error en login: {e}. Reintentando... ({attempts} intentos restantes)")
            time.sleep(2)
        

    for abogado in os.listdir(abogados_root):
        procesar_actos(driver,wait,abogado,os.path.abspath(os.path.join(abogados_root,abogado)))
