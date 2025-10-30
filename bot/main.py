# bot/main.py
import os
import json
from datetime import datetime
from urllib.parse import urlsplit
from typing import List, Tuple, Optional, Dict, Any

import typer
from loguru import logger
from dotenv import load_dotenv

from bot.pages.uif_modal import UifModal
from bot.pages.customer_detail_page import CustomerDetailPage
from bot.pages.customers_cif_modal import CustomersCifModal
from bot.pages.clients_row_actions import ClientsRowActions
from bot.pages.customers_create_confirm_modal import CustomersCreateConfirmModal
from bot.core.browser import make_driver
from bot.pages.login_page import LoginPage
from bot.pages.dashboard_page import DashboardPage
from bot.pages.clients_page import ClientsPage
from bot.core.acto_scanner import scan_acto_folder

app = typer.Typer(add_completion=False, no_args_is_help=False)

# =========================
# Helpers de serialización
# =========================
def _to_jsonable(obj):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(x) for x in obj]
    try:
        return {k: _to_jsonable(v) for k, v in obj.__dict__.items()}
    except Exception:
        return str(obj)

# =========================
# Helpers genéricos (safe get)
# =========================
def _get(obj: Any, key: str, default=None):
    """Obtiene atributo o key (insensible a mayúsculas) de dict/obj."""
    if obj is None:
        return default
    # dict exacto
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        # búsqueda insensible a mayúsculas
        lk = key.lower()
        for k, v in obj.items():
            if str(k).lower() == lk:
                return v
        return default
    # objeto con atributo
    if hasattr(obj, key):
        return getattr(obj, key)
    # intento insensible a mayúsculas
    for k in dir(obj):
        if k.lower() == key.lower():
            try:
                return getattr(obj, k)
            except Exception:
                break
    return default

# =========================
# Helpers de rutas/acto
# =========================
def _origin_of(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}"

def _find_first_acto_without_cache(root_dir: str) -> Optional[str]:
    """
    Regresa la ruta de la primera carpeta de acto que NO tenga '_cache_bot'.
    """
    if not os.path.isdir(root_dir):
        logger.error(f"Root inválido: {root_dir}")
        return None

    for name in sorted(os.listdir(root_dir)):
        full = os.path.join(root_dir, name)
        if not os.path.isdir(full):
            continue
        cache_dir = os.path.join(full, "_cache_bot")
        if not os.path.exists(cache_dir):
            logger.info(f"Acto elegible: {full}")
            return full
        else:
            logger.debug(f"SKIP (ya tiene _cache_bot): {full}")
    return None

def _ensure_cache_and_write_json(acto_dir: str, extraction) -> str:
    """
    Crea /_cache_bot si no existe y guarda la extracción como JSON.
    Regresa la ruta del JSON.
    """
    cache_dir = os.path.join(acto_dir, "_cache_bot")
    os.makedirs(cache_dir, exist_ok=True)

    payload = {
        "acto_dir": acto_dir,
        "acto_nombre": getattr(extraction, "acto_nombre", os.path.basename(acto_dir)),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data": _to_jsonable(extraction),
    }
    out_json = os.path.join(cache_dir, "acto.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.success(f"JSON generado: {out_json}")
    return out_json

# =========================
# Helpers de PARTES (PF/PM)
# =========================
def _pf_to_dict(pf_obj) -> Optional[Dict[str, str]]:
    try:
        rol = _get(pf_obj, "rol", "") or ""
        persona = _get(pf_obj, "persona")
        nombre = (_get(persona, "nombre") or _get(pf_obj, "nombre") or "").strip()
        rfc = (_get(persona, "rfc") or _get(pf_obj, "rfc") or "").strip()
        idcif = (
            _get(persona, "idcif")
            or _get(persona, "IdCIF")
            or _get(persona, "IDCIF")
            or _get(pf_obj, "idcif")
            or ""
        )
        if not nombre:
            return None
        return {"tipo": "PF", "rol": rol, "nombre": nombre, "rfc": rfc, "idcif": str(idcif).strip()}
    except Exception:
        return None

def _pm_to_dict(pm_obj) -> Optional[Dict[str, str]]:
    try:
        rol = _get(pm_obj, "rol", "") or ""
        # En PM el nombre suele ser la razón social
        nombre = (_get(pm_obj, "nombre") or _get(pm_obj, "razon_social") or "").strip()
        rfc = (_get(pm_obj, "rfc") or "").strip()
        idcif = (_get(pm_obj, "idcif") or _get(pm_obj, "IdCIF") or _get(pm_obj, "IDCIF") or "").strip()
        if not nombre:
            return None
        return {"tipo": "PM", "rol": rol, "nombre": nombre, "rfc": rfc, "idcif": idcif}
    except Exception:
        return None

def _extract_partes_pf_pm(extraction) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Devuelve:
      - pf_list: [{'tipo':'PF','rol':..,'nombre':..,'rfc':..,'idcif':..}, ...]
      - pm_list: [{'tipo':'PM','rol':..,'nombre':..,'rfc':..,'idcif':..}, ...]
    """
    pf_list: List[Dict[str, str]] = []
    for pf in getattr(extraction, "partes_pf", []) or []:
        d = _pf_to_dict(pf)
        if d:
            pf_list.append(d)

    pm_list: List[Dict[str, str]] = []
    for pm in getattr(extraction, "partes_pm", []) or []:
        d = _pm_to_dict(pm)
        if d:
            pm_list.append(d)

    return pf_list, pm_list

def _print_partes_console(pf_list: List[Dict[str, str]], pm_list: List[Dict[str, str]], acto_nombre: str):
    logger.info(f"== PARTES EXTRAÍDAS (sin inmuebles) :: {acto_nombre} ==")
    if pf_list:
        logger.info("Personas Físicas (PF):")
        for d in pf_list:
            logger.info(f"  - {d.get('rol') or 'ROL'} :: {d.get('nombre')} | RFC: {d.get('rfc') or '-'} | IdCIF: {d.get('idcif') or '-'}")
    else:
        logger.info("Personas Físicas (PF): [ninguna]")

    if pm_list:
        logger.info("Personas Morales (PM):")
        for d in pm_list:
            logger.info(f"  - {d.get('rol') or 'ROL'} :: {d.get('nombre')} | RFC: {d.get('rfc') or '-'} | IdCIF: {d.get('idcif') or '-'}")
    else:
        logger.info("Personas Morales (PM): [ninguna]")

def _pick_one_party(pf_list: List[Dict[str, str]], pm_list: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Elige una sola parte para la prueba:
      - Prioriza PF; si no hay, usa PM.
    Regresa un dict con campos: tipo, nombre, nombre_upper, rfc, idcif, rol.
    """
    party = None
    if pf_list:
        party = pf_list[0]
    elif pm_list:
        party = pm_list[0]
    if party:
        party = dict(party)  # copia
        party["nombre_upper"] = (party.get("nombre") or "").upper().strip()
    return party

# =========================
# Pipeline (reutilizable)
# =========================
def _pipeline(headless: bool):
    load_dotenv("bot/config/.env")

    url = os.getenv("PORTAL_URL", "")
    user = os.getenv("PORTAL_USER", "")
    pwd  = os.getenv("PORTAL_PASS", "")
    actos_root = os.getenv("LOCAL_ACTOS_ROOT", "")

    if not (url and user and pwd and actos_root):
        logger.error("Faltan PORTAL_URL/USER/PASS y/o ACTOS_ROOT en .env")
        raise typer.Exit(code=2)

    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=10)

    try:
        # 1) Login
        LoginPage(driver, wait).login(url, user, pwd)
        DashboardPage(driver, wait).assert_loaded()
        logger.info("Login OK")

        # 2) Buscar primer acto sin cache
        target_acto = _find_first_acto_without_cache(actos_root)
        if not target_acto:
            logger.warning("No hay actos nuevos (todos tienen _cache_bot). Nada que hacer.")
            return

        # 3) Escanear y guardar JSON
        extraction = scan_acto_folder(target_acto, acto_nombre=os.path.basename(target_acto))
        json_path = _ensure_cache_and_write_json(target_acto, extraction)

        # 4) PF/PM -> consola y contexto
        pf_list, pm_list = _extract_partes_pf_pm(extraction)
        _print_partes_console(
            pf_list, pm_list,
            getattr(extraction, "acto_nombre", os.path.basename(target_acto))
        )
        acto_ctx = {
            "json_path": json_path,
            "pf": pf_list,
            "pm": pm_list,
            "acto_dir": target_acto,
            "acto_nombre": getattr(extraction, "acto_nombre", os.path.basename(target_acto)),
        }

        # 5) Ir a Clientes y buscar UNA parte (en MAYÚSCULAS)
        cur = driver.current_url
        base = _origin_of(cur)  # p.ej. https://not84.singrafos.com
        cp = ClientsPage(driver, wait)
        cp.open_direct(base)
        cp.assert_loaded()
        logger.info("Página de Clientes abierta.")

        party = _pick_one_party(acto_ctx["pf"], acto_ctx["pm"])
        if not party:
            logger.warning("No hay PARTES (PF/PM) para buscar en clientes.")
            return

        logger.info(f"Buscando en Clientes ({party['tipo']}): {party['nombre_upper']}")
        found = cp.search_by_name(party["nombre_upper"], timeout=12)
        if found:
            logger.success("Ya existe en la consola")
            first = cp.first_row_client_text() or "(sin texto en primera fila)"
            logger.info(f"Primera fila (columna Cliente): {first}")

            # Abrir el detalle del cliente (lupita)
            cp.click_first_view()
            logger.info("ABRIO LUPITA")

            # 👉 Búsqueda UIF
            cdp = CustomerDetailPage(driver, wait)
            cdp.click_busqueda_uif(timeout=20)

            uif = UifModal(driver, wait)
            # 1) 'Buscar de nuevo'  2) Esperar y 3) Clic en 'Descargar Comprobante' (gris)
            uif.buscar_de_nuevo_y_descargar(timeout_busqueda=40, timeout_descarga=60)
            logger.info("Flujo UIF completado (buscar de nuevo + descargar comprobante).")
            # 1) 'Buscar de nuevo'
            # uif.click_buscar_de_nuevo(timeout=45)
            # # 2) Espera y clic en 'Descargar Comprobante' (botón inferior)
            # uif.click_descargar_comprobante(timeout=60)
            logger.info("Flujo UIF completado (buscar de nuevo + descargar comprobante).")
        else:
            # ←—— NO EXISTE -> crear por IdCIF
            logger.info("No existe; creando cliente...")
            cp.click_new()
            logger.success("Formulario de 'Nuevo Cliente' abierto.")
            cp.click_crear_por_idcif()
            logger.success("Se abrió el flujo 'Crear por IdCIF'.")

            rfc = (party.get("rfc") or "").strip()
            idcif = (party.get("idcif") or "").strip()

            modal = CustomersCifModal(driver, wait)
            modal.fill_and_consult(rfc, idcif)

            # NUEVO: crear cliente
            #modal.click_create_customer(timeout=25)

            #Confirmar modal
            #confirm = CustomersCreateConfirmModal(driver, wait)
            #confirm.confirm_without_email(timeout=25)
            cp = ClientsPage(driver, wait)
            cp.open_direct(base)
            cp.assert_loaded()
            logger.info("Página de Clientes abierta.")
        


    finally:
        input("INTRODUCE: ")
        pass
        # driver.quit()

# =========================
# CLI
# =========================
@app.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    headless: bool = typer.Option(False, help="Ejecuta navegador en modo headless"),
):
    """
    Sin subcomando: ejecuta el pipeline por defecto.
    Con subcomando `run`: hace lo mismo.
    """
    if ctx.invoked_subcommand is None:
        _pipeline(headless=headless)

@app.command("run")
def run(
    headless: bool = typer.Option(False, help="Ejecuta navegador en modo headless"),
):
    """Ejecuta el pipeline principal (alias)."""
    _pipeline(headless=headless)

if __name__ == "__main__":
    app()
