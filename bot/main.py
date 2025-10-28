import os
import json
import typer
from loguru import logger
from dotenv import load_dotenv

from bot.core.browser import make_driver
from bot.core.auth import login_smoke
from bot.core.files import ActosFinder
from bot.core import csf as csf_parser
from bot.models.person_docs import PersonDocs

from bot.pages.login_page import LoginPage
from bot.pages.dashboard_page import DashboardPage
from bot.pages.projects_page import ProjectsPage

app = typer.Typer(add_completion=False)

def _load_env():
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
    headless: bool = typer.Option(False),
    screenshot: str = typer.Option("bot/logs/login_ok.png")
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

# ========= NUEVO: validar docs del Comprador y guardar sus rutas =========
@app.command("check-compraventa-docs")
def check_compraventa_docs(
    headless: bool = typer.Option(False, help="Para login de evidencia, no navega más."),
    root: str = typer.Option(None, help="Ruta base si no usas LOCAL_ACTOS_ROOT"),
    nombre_carpeta: str = typer.Option("Compraventa Daniel"),
    screenshot: str = typer.Option("bot/logs/login_dashboard.png")
):
    """
    1) Login (evidencia).
    2) En <root>/<nombre_carpeta>/Comprador:
       - Localiza CSF y extrae RFC, idCIF y NOMBRE.
       - Busca CURP, ACTA de nacimiento, INE, y COMP_DOMICILIO (opcional).
    3) Imprime las rutas encontradas y si cumple esenciales.
    """
    url, user, pwd = _load_env()

    os.makedirs(os.path.dirname(screenshot), exist_ok=True)
    """"
    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=10)
    try:
        LoginPage(driver, wait).login(url, user, pwd)
        driver.save_screenshot(screenshot)
        logger.info("Login OK, screenshot -> {}", screenshot)
    finally:
        driver.quit()
    """
    if not root:
        root = os.getenv("LOCAL_ACTOS_ROOT", "")
        if not root:
            logger.error("No se proporcionó --root ni LOCAL_ACTOS_ROOT en .env")
            raise typer.Exit(code=3)

    acto_dir = ActosFinder.compraventa_path(root, nombre_carpeta)
    comprador_dir = os.path.join(acto_dir, "Comprador")

    if not ActosFinder.ensure_dir(acto_dir, f"Acto '{nombre_carpeta}'"):
        raise typer.Exit(code=4)
    if not ActosFinder.ensure_dir(comprador_dir, "Comprador"):
        raise typer.Exit(code=5)

    # CSF (obligatorio)
    csf_path = ActosFinder.find_csf_in_comprador(comprador_dir)
    if not csf_path:
        print("No se encontró CSF. No se puede continuar.")
        raise typer.Exit(code=6)

    # Extraer campos de la CSF
    rfc, idcif, nombre = csf_parser.extract_csf_fields(csf_path)

    person = PersonDocs(nombre=nombre, rfc=rfc, idcif=idcif)
    person.paths["CSF"] = csf_path

    # Buscar el resto
    person.paths["CURP"] = ActosFinder.find_curp(comprador_dir)
    person.paths["ACTA_NAC"] = ActosFinder.find_acta_nacimiento(comprador_dir)
    person.paths["INE"] = ActosFinder.find_ine(comprador_dir)
    person.paths["COMP_DOMICILIO"] = ActosFinder.find_comprobante_domicilio(comprador_dir)

    # Salida amistosa
    print("\n====== DATOS DEL COMPRADOR ======")
    print(f"Nombre: {person.nombre or '(no detectado)'}")
    print(f"RFC:    {person.rfc or '(no detectado)'}")
    print(f"idCIF:  {person.idcif or '(no detectado)'}")

    print("\n====== RUTAS DE DOCUMENTOS ======")
    for k, v in person.paths.items():
        req = " (opcional)" if k == "COMP_DOMICILIO" else ""
        print(f"{k}{req}: {v or '(no encontrado)'}")

    print("\nEsenciales completos:", "SÍ" if person.essentials_ok() else "NO")
    print("=================================\n")

    # (Opcional) Deja un JSON para reusar rutas al subir
    out_dir = os.path.join(acto_dir, "_cache_bot")
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, "comprador_docs.json")
    data = {
        "nombre": person.nombre,
        "rfc": person.rfc,
        "idcif": person.idcif,
        "paths": person.paths,
        "essentials_ok": person.essentials_ok(),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.success("Rutas guardadas en {}", out_json)

@app.command("hello")
def hello():
    print("CLI OK")

if __name__ == "__main__":
    app()
