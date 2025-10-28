import os
import typer
from loguru import logger
from dotenv import load_dotenv

from bot.core.browser import make_driver
from bot.core.auth import login_smoke
from bot.core.files import ActosFinder
from bot.core import csf as csf_parser  # NUEVO import

from bot.pages.login_page import LoginPage
from bot.pages.dashboard_page import DashboardPage
from bot.pages.projects_page import ProjectsPage

app = typer.Typer(add_completion=False)

def _load_env():
    # Intenta primero bot/config/.env; si no existe, .env en raíz del repo
    loaded = load_dotenv("bot/config/.env")
    if not loaded:
        load_dotenv(".env")

    url = os.getenv("PORTAL_URL", "")
    user = os.getenv("PORTAL_USER", "")
    pwd  = os.getenv("PORTAL_PASS", "")
    if not (url and user and pwd):
        logger.error("Faltan PORTAL_URL/USER/PASS en .env")
        raise typer.Exit(code=2)
    return url, user, pwd

@app.command("open-clientes")
def open_clientes(
    headless: bool = typer.Option(False),
    screenshot: str = typer.Option("bot/logs/clientes.png")
):
    url, user, pwd = _load_env()
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)

    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=10)
    try:
        LoginPage(driver, wait).login(url, user, pwd)
        DashboardPage(driver, wait).go_to_clientes()
        driver.save_screenshot(screenshot)
        logger.success("Navegación a Clientes OK -> {}", screenshot)
    finally:
        driver.quit()

@app.command("login-test")
def login_test(
    headless: bool = typer.Option(False, help="Ejecuta el navegador en modo headless"),
    screenshot: str = typer.Option("bot/logs/login_ok.png", help="Ruta del screenshot de evidencia")
):
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)
    try:
        login_smoke(headless=headless, screenshot_path=screenshot)
    except Exception as e:
        logger.exception(e)
        raise typer.Exit(code=1)

@app.command("open-proyectos")
def open_proyectos(
    headless: bool = typer.Option(False),
    screenshot: str = typer.Option("bot/logs/proyectos.png")
):
    url, user, pwd = _load_env()
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)

    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=10)
    try:
        LoginPage(driver, wait).login(url, user, pwd)
        DashboardPage(driver, wait).go_to_proyectos()
        driver.save_screenshot(screenshot)
        logger.success("Navegación a /projects OK -> {}", screenshot)
    finally:
        driver.quit()

@app.command("nuevo-proyecto")
def nuevo_proyecto(
    headless: bool = typer.Option(False),
    screenshot: str = typer.Option("bot/logs/nuevo_proyecto.png")
):
    url, user, pwd = _load_env()
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)

    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=10)
    try:
        LoginPage(driver, wait).login(url, user, pwd)
        DashboardPage(driver, wait).go_to_proyectos()
        ProjectsPage(driver, wait).click_nuevo()
        driver.save_screenshot(screenshot)
        logger.success("Click en '+ Nuevo' OK -> {}", screenshot)
    finally:
        driver.quit()

# =========================
# Verificación CSF + extracción RFC/IDCIF
# =========================
@app.command("check-compraventa-csf")
def check_compraventa_csf(
    headless: bool = typer.Option(False, help="Navegador headless para el login"),
    root: str = typer.Option(None, help="Ruta base donde existe la carpeta del acto (si no, usa LOCAL_ACTOS_ROOT del .env)"),
    nombre_carpeta: str = typer.Option("Compraventa Daniel", help="Nombre de la carpeta del acto"),
    screenshot: str = typer.Option("bot/logs/login_dashboard.png", help="Screenshot post-login (opcional)")
):
    """
    1) Inicia sesión y entra al dashboard.
    2) Valida la existencia de: <root>/<nombre_carpeta>/Comprador
    3) Ubica un archivo CSF dentro de 'Comprador'.
    4) Extrae e imprime RFC e IDCIF.
    """
    url, user, pwd = _load_env()

    # 1) Login (evidencia)
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)
    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=10)
    try:
        LoginPage(driver, wait).login(url, user, pwd)
        driver.save_screenshot(screenshot)
        logger.info("Login OK, screenshot -> {}", screenshot)
    finally:
        driver.quit()

    # 2) Determinar root
    if not root:
        root = os.getenv("LOCAL_ACTOS_ROOT", "")
        if not root:
            logger.error("No se proporcionó --root ni está definida LOCAL_ACTOS_ROOT en .env")
            raise typer.Exit(code=3)

    acto_dir = ActosFinder.compraventa_path(root, nombre_carpeta)
    comprador_dir = os.path.join(acto_dir, "Comprador")

    # 3) Validaciones de carpeta
    if not ActosFinder.ensure_dir(acto_dir, f"Acto '{nombre_carpeta}'"):
        raise typer.Exit(code=4)
    if not ActosFinder.ensure_dir(comprador_dir, "Comprador"):
        raise typer.Exit(code=5)

    # 4) Buscar CSF y reportar
    csf_path = ActosFinder.find_csf_in_comprador(comprador_dir)
    if not csf_path:
        print("No se encontró CSF en la carpeta del Comprador.")
        raise typer.Exit(code=6)

    print(f"CSF encontrado en: {csf_path}")
    logger.success("CSF encontrado en: {}", csf_path)

    # 5) Extraer RFC e IDCIF de la CSF
    rfc, idcif = csf_parser.extract_csf_fields(csf_path)

    # Salida clara en consola
    print("====== EXTRACCIÓN CSF ======")
    print(f"RFC:   {rfc or '(no encontrado)'}")
    print(f"IDCIF: {idcif or '(no encontrado)'}")
    print("============================")

    # También por logger
    logger.info("RFC extraído: {}", rfc)
    logger.info("IDCIF extraído: {}", idcif)

@app.command("hello")
def hello():
    print("CLI OK")

if __name__ == "__main__":
    app()
