from dotenv import load_dotenv
from bot.utils.common_imports import *
from bot.core.browser import make_driver

from bot.pages.login_page import LoginPage
from bot.Proceso.procesar_actos import procesar_actos

def proceso_por_abogado(headless: bool) -> None:
    # Cargar variables de entorno (.env) una sola vez para este proceso
    load_dotenv("bot/config/.env")

    user = os.getenv("PORTAL_USER", "")
    pwd  = os.getenv("PORTAL_PASS", "")
    abogados_root = os.getenv("LOCAL_ACTOS_ROOT", "")

    logger.info("\n\n")

    if not (user and pwd and abogados_root):
        logger.error("Faltan PORTAL_URL/USER/PASS y/o ACTOS_ROOT en .env")
        return
    
    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=7)

    LoginPage(driver,wait).login(user,pwd)
    logger.success("Login OK")

    for abogado in os.listdir(abogados_root):
        procesar_actos(driver,wait,abogado,os.path.abspath(os.path.join(abogados_root,abogado)))
