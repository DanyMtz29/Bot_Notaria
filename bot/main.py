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

# === Escaneo de actos
from bot.core.acto_scanner import (
    scan_acto_folder,
    KNOWN_ROLES,
    INMUEBLE_DIR_NAMES,
)

app = typer.Typer(add_completion=False)

def _load_env_any():
    # intenta bot/config/.env, si no .env del proyecto
    loaded = load_dotenv("bot/config/.env")
    if not loaded:
        load_dotenv(".env")

def _looks_like_acto_dir(path: str) -> bool:
    """Heurística: si adentro hay alguna carpeta de rol conocido o 'Inmueble(s)'. """
    if not os.path.isdir(path):
        return False
    try:
        subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except Exception:
        return False
    names = set(subdirs)
    if names & INMUEBLE_DIR_NAMES:
        return True
    if names & KNOWN_ROLES:
        return True
    return False

def _resolve_paths(
    acto_dir: str | None,
    root: str | None,
    nombre_carpeta: str | None,
    scan_all: bool
):
    """
    Devuelve (mode, actos):
      - mode: "single" o "multi"
      - actos: lista de paths de actos a escanear
    Prioridades:
      1) --acto-dir
      2) --root + --nombre-carpeta
      3) Solo --root:
         - si root parece acto -> single
         - si --all -> multi (todos subdirs que parezcan acto)
      4) Solo variables .env:
         - LOCAL_ACTO_DIR -> single
         - LOCAL_ACTOS_ROOT:
             - si parece acto -> single
             - si --all -> multi
             - error si no hay forma de decidir un acto concreto
    """
    _load_env_any()

    if not acto_dir:
        acto_dir = os.getenv("LOCAL_ACTO_DIR", "") or None
    if not root:
        root = os.getenv("LOCAL_ACTOS_ROOT", "") or None

    # 1) acto-dir directo
    if acto_dir:
        acto_dir = os.path.abspath(acto_dir)
        if not os.path.isdir(acto_dir):
            raise typer.BadParameter(f"--acto-dir no existe: {acto_dir}")
        return "single", [acto_dir]

    # 2) root + nombre_carpeta
    if root and nombre_carpeta:
        acto = os.path.join(os.path.abspath(root), nombre_carpeta)
        if not os.path.isdir(acto):
            raise typer.BadParameter(f"No existe el acto: {acto}")
        return "single", [acto]

    # 3) solo root
    if root:
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise typer.BadParameter(f"--root no existe: {root}")
        if _looks_like_acto_dir(root):
            return "single", [root]
        if scan_all:
            # escanea todos los subdirs que parezcan acto
            try:
                candidatos = []
                for d in os.listdir(root):
                    full = os.path.join(root, d)
                    if os.path.isdir(full) and _looks_like_acto_dir(full):
                        candidatos.append(full)
                if not candidatos:
                    raise typer.BadParameter("No se encontraron actos dentro de --root.")
                return "multi", candidatos
            except Exception as e:
                raise typer.BadParameter(f"Error listando actos en --root: {e}")
        # sin nombre_carpeta ni --all, no sabemos cuál acto elegir
        raise typer.BadParameter(
            "Ambiguo: --root no es un acto y no diste --nombre-carpeta ni --all.\n"
            "Soluciones: usa --nombre-carpeta, o --all, o define LOCAL_ACTO_DIR, o pasa --acto-dir."
        )

    # 4) solo .env
    if nombre_carpeta:
        if not root:
            raise typer.BadParameter("Diste --nombre-carpeta pero no --root, y no hay LOCAL_ACTOS_ROOT en .env.")
    if root and not _looks_like_acto_dir(root) and not scan_all:
        raise typer.BadParameter(
            "LOCAL_ACTOS_ROOT no parece un acto. Usa --all o especifica --nombre-carpeta."
        )

    # intenta LOCAL_ACTO_DIR
    if not root and not nombre_carpeta:
        env_acto = os.getenv("LOCAL_ACTO_DIR", "")
        if env_acto:
            env_acto = os.path.abspath(env_acto)
            if not os.path.isdir(env_acto):
                raise typer.BadParameter(f"LOCAL_ACTO_DIR no existe: {env_acto}")
            return "single", [env_acto]

    # intenta LOCAL_ACTOS_ROOT
    env_root = root or os.getenv("LOCAL_ACTOS_ROOT", "")
    if env_root:
        env_root = os.path.abspath(env_root)
        if not os.path.isdir(env_root):
            raise typer.BadParameter(f"LOCAL_ACTOS_ROOT no existe: {env_root}")
        if _looks_like_acto_dir(env_root):
            return "single", [env_root]
        if scan_all:
            candidatos = []
            for d in os.listdir(env_root):
                full = os.path.join(env_root, d)
                if os.path.isdir(full) and _looks_like_acto_dir(full):
                    candidatos.append(full)
            if not candidatos:
                raise typer.BadParameter("No se encontraron actos dentro de LOCAL_ACTOS_ROOT.")
            return "multi", candidatos
        raise typer.BadParameter(
            "Ambiguo: LOCAL_ACTOS_ROOT no es un acto. Usa --all o especifica --nombre-carpeta."
        )

    # Nada aplicó
    raise typer.BadParameter(
        "No se proporcionó --acto-dir ni --root/--nombre-carpeta. "
        "Alternativas: define LOCAL_ACTO_DIR o LOCAL_ACTOS_ROOT en .env."
    )

def _write_scan_json(acto_path: str, data: dict, out_json: str | None):
    cache_dir = os.path.join(acto_path, "_cache_bot")
    os.makedirs(cache_dir, exist_ok=True)
    out_path = out_json or os.path.join(cache_dir, "acto_scan.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.success("Acto escaneado OK -> {}", out_path)
    print(out_path)
    return out_path

# ===================== Comandos existentes =====================

def _load_env_portal():
    _load_env_any()
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
    url, user, pwd = _load_env_portal()
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
    url, user, pwd = _load_env_portal()
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
    url, user, pwd = _load_env_portal()
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

# ========= Chequeo docs comprador (se queda igual) =========
@app.command("check-compraventa-docs")
def check_compraventa_docs(
    headless: bool = typer.Option(False, help="Para login de evidencia, no navega más."),
    root: str = typer.Option(None, help="Ruta base si no usas LOCAL_ACTOS_ROOT"),
    nombre_carpeta: str = typer.Option("Compraventa Daniel"),
    screenshot: str = typer.Option("bot/logs/login_dashboard.png")
):
    url, user, pwd = _load_env_portal()
    os.makedirs(os.path.dirname(screenshot), exist_ok=True)

    if not root:
        _load_env_any()
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

    csf_path = ActosFinder.find_csf_in_comprador(comprador_dir)
    if not csf_path:
        print("No se encontró CSF. No se puede continuar.")
        raise typer.Exit(code=6)

    rfc, idcif, nombre = csf_parser.extract_csf_fields(csf_path)

    person = PersonDocs(nombre=nombre, rfc=rfc, idcif=idcif)
    person.paths["CSF"] = csf_path
    person.paths["CURP"] = ActosFinder.find_curp(comprador_dir)
    person.paths["ACTA_NAC"] = ActosFinder.find_acta_nacimiento(comprador_dir)
    person.paths["INE"] = ActosFinder.find_ine(comprador_dir)
    person.paths["COMP_DOMICILIO"] = ActosFinder.find_comprobante_domicilio(comprador_dir)

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

# ========= NUEVO: Escaneo integral del/los ACTO(s) =========
@app.command("scan-acto")
def scan_acto(
    acto_dir: str = typer.Option(None, help="Ruta ABSOLUTA del ACTO a escanear."),
    root: str = typer.Option(None, help="Carpeta raíz que contiene actos (si no usas --acto-dir)."),
    nombre_carpeta: str = typer.Option(None, help="Nombre de carpeta del acto dentro de --root."),
    out_json: str = typer.Option(None, help="Ruta JSON de salida; default *_cache_bot/acto_scan.json en cada acto"),
    all: bool = typer.Option(False, "--all", help="Escanear TODOS los actos dentro de --root o LOCAL_ACTOS_ROOT")
):
    """
    Escanea uno o varios ACTOS y genera acto_scan.json en cada carpeta de acto.
    Resolución de rutas:
      - --acto-dir
      - --root + --nombre-carpeta
      - --root  (si root ya es acto; o con --all para todos)
      - .env: LOCAL_ACTO_DIR | LOCAL_ACTOS_ROOT (con --all para todos)
    """
    mode, actos = _resolve_paths(
        acto_dir=acto_dir,
        root=root,
        nombre_carpeta=nombre_carpeta,
        scan_all=all
    )

    for a in actos:
        name = os.path.basename(a)
        extraction = scan_acto_folder(a, acto_nombre=name)
        data = extraction.to_dict()
        _write_scan_json(a, data, out_json)

    print(f"\nListo. Escaneados: {len(actos)} acto(s).\n")

@app.command("hello")
def hello():
    print("CLI OK")

if __name__ == "__main__":
    app()
