# bot/main.py
import os
import json
from datetime import datetime
from urllib.parse import urlsplit
from typing import List, Tuple, Optional, Dict, Any, Set

import typer
import time
from loguru import logger
from dotenv import load_dotenv

from bot.pages.uif_modal import UifModal
from bot.pages.projects_documents import ProjectsDocumentsPage
from bot.pages.customer_detail_page import CustomerDetailPage
from bot.pages.projects_parts import ProjectsPartesPage
from bot.pages.customers_cif_modal import CustomersCifModal
from bot.pages.customers_create_confirm_modal import CustomersCreateConfirmModal
from bot.core.browser import make_driver
from bot.pages.login_page import LoginPage
from bot.pages.dashboard_page import DashboardPage
from bot.pages.clients_page import ClientsPage
from bot.pages.projects_page import ProjectsPage
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

def _flatten_all_parties(pf_list: List[Dict[str, str]], pm_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Junta PF y PM en una sola lista y agrega nombre_upper.
    Evita duplicados por (tipo, nombre_upper).
    """
    out: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    for src in (pf_list or []):
        d = dict(src)
        d["nombre_upper"] = (d.get("nombre") or "").upper().strip()
        key = (d.get("tipo",""), d["nombre_upper"])
        if d["nombre_upper"] and key not in seen:
            seen.add(key)
            out.append(d)

    for src in (pm_list or []):
        d = dict(src)
        d["nombre_upper"] = (d.get("nombre") or "").upper().strip()
        key = (d.get("tipo",""), d["nombre_upper"])
        if d["nombre_upper"] and key not in seen:
            seen.add(key)
            out.append(d)

    return out

def _safe_pdf_name(party: Dict[str, str]) -> str:
    base = f"{party.get('tipo','')}_{party.get('rol','')}_{party.get('nombre_upper','')}".strip("_")
    # Limpia caracteres raros para nombre de archivo
    cleaned = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in base)
    return cleaned.replace("  ", " ").replace(" ", "_")

# =========================
# Flujo por PARTE
# =========================
def _process_party(driver, wait, base: str, party: Dict[str, str]) -> None:
    """
    Para una parte:
      - busca por nombre en Clientes
      - si existe: abre detalle y saca UIF
      - si no existe: crea por IdCIF y luego saca UIF
    """
    cp = ClientsPage(driver, wait)
    cp.open_direct(base)
    cp.assert_loaded()

    logger.info(f"[{party.get('tipo')}/{party.get('rol') or '-'}] Buscando en Clientes: {party['nombre_upper']}")
    found = cp.search_by_name(party["nombre_upper"], timeout=12)

    if found:
        logger.success("Cliente EXISTE en consola")
        try:
            cp.click_first_view()
            logger.info("Detalle de cliente abierto (lupita).")
            cdp = CustomerDetailPage(driver, wait)
            cdp.click_busqueda_uif(timeout=20)

            uif = UifModal(driver, wait)
            # Ejecuta el flujo estándar: buscar de nuevo + descargar comprobante
            uif.buscar_de_nuevo_y_descargar(timeout_busqueda=40, timeout_descarga=60)
            UifModal(driver, wait).renombrar_ultimo_pdf(_safe_pdf_name(party))
            logger.success("UIF descargado y renombrado.")
        finally:
            # Regresa a Clientes para el siguiente ciclo
            cp.open_direct(base)
            cp.assert_loaded()
        return

    # === NO EXISTE: crear por IdCIF ===
    logger.info("Cliente NO existe; creando por IdCIF...")
    cp.click_new()
    logger.success("Formulario 'Nuevo Cliente' abierto.")
    cp.click_crear_por_idcif()
    logger.success("Flujo 'Crear por IdCIF' abierto.")

    rfc = (party.get("rfc") or "").strip()
    idcif = (party.get("idcif") or "").strip()

    modal = CustomersCifModal(driver, wait)
    modal.fill_and_consult(rfc, idcif)

    # Crear cliente y confirmar (descomenta si deseas crear realmente)
    try:
        modal.click_create_customer(timeout=25)
        confirm = CustomersCreateConfirmModal(driver, wait)
        confirm.confirm_without_email(timeout=25)
        logger.success("Cliente creado por IdCIF.")
    except Exception as e:
        logger.warning(f"No se pudo completar creación automática (quizá ya existe o faltan datos): {e}")

    # Regresar a Clientes y abrir detalle del recién creado/buscado
    cp.open_direct(base)
    cp.assert_loaded()
    _ = cp.search_by_name(party["nombre_upper"], timeout=10)
    try:
        cp.click_first_view()
        logger.info("Detalle de cliente abierto (post-creación).")
        cdp = CustomerDetailPage(driver, wait)
        cdp.click_busqueda_uif(timeout=20)

        uif = UifModal(driver, wait)
        uif.buscar_de_nuevo_y_descargar(timeout_busqueda=40, timeout_descarga=60)
        UifModal(driver, wait).renombrar_ultimo_pdf(_safe_pdf_name(party))
        logger.success("UIF descargado y renombrado (post-creación).")
    finally:
        cp.open_direct(base)
        cp.assert_loaded()

def _fill_new_project_fields(driver, wait, cliente_principal, pf_list,pm_list, acto_nombre):
    """
    data_json ej:
    {
      "abogado": "BOT SINGRAFOS BOTBI",
      "cliente_principal": "DANIEL ARNULFO JUAREZ MARTINEZ",
      "descripcion": "Proyecto auto generado por Botbi",
      "acto": "ADJUDICACION JUDICIAL"   # o el que venga en tu JSON
    }
    """

    pp = ProjectsPage(driver, wait)
    pp.create_project(
        abogado="BOT SINGRAFOS BOTBI",
        cliente=cliente_principal,
        descripcion=("\"PRUEBA BOTBI, ADJUDICACION - DANIEL\""),
        acto=acto_nombre
    )

    clientes = []
    for cl in pf_list:
        clientes.append(cl)
    for cl in pm_list:
        clientes.append(cl)

    print("CLIENTES\n")
    print(clientes)

    #partes = ProjectsPartesPage(driver, wait)    
    #for cl in pf_list:
    #    partes.click_agregar()
    #    partes.escribir_busqueda_directorio(driver,wait,nombre=cl.get("nombre"))
    #    partes.seleccionar_rol(rol_texto=cl.get("rol"))
    #    partes.guardar_parte()
    #    time.sleep(1)

    #Apartado de documentos
    docs = ProjectsDocumentsPage(driver, wait)
    docs.open_documents_tab()
    #docs.set_faltante_by_description("Aviso preventivo", marcar=True)
    #docs.set_faltante_by_description("Escritura Antecedente", marcar=True)

    #Seleccionar botones
    #docs.click_subir_documentos()
    #docs.click_importar_documentos()
    #docs.subir_documentos([
    #    r"C:\Users\mdani\OneDrive\Desktop\Actos_Ejemplo\Pruebas\ESC. Adjudicacion - Daniel\Adquiriente\Daniel Juarez\CSF.pdf"
    #])
    ruta_abs = r"C:\Users\mdani\OneDrive\Desktop\Actos_Ejemplo\Pruebas\ESC. Adjudicacion - Daniel\Adquiriente\Daniel Juarez\CSF.pdf"
    docs.upload_anexo(ruta_abs)    # realmente sube el archivo
    docs.set_tipo_documento_anexo("CSF.pdf", "Constancia de identificación fiscal (compareciente o partes)")
    docs.set_cliente_anexo("CSF.pdf", "DANIEL ARNULFO JUAREZ MARTINEZ")

    # (Opcional) ver qué descripciones detecta el grid completo:
    #print(docs.list_all_required_descriptions())

    #Por si no se pono automaticamente lo de moral
    # time.sleep(1)
    # if( is_moral ):#Marcar como persona moral
    #     partes.marcar_persona_moral()

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
            "cliente_principal": getattr(extraction, "cliente_principal")
        }

        """
        # 5) Ir a Clientes (una sola vez para obtener base) y PROCESAR TODAS LAS PARTES
        cur = driver.current_url
        base = _origin_of(cur)  # p.ej. https://not84.singrafos.com

        all_parties = _flatten_all_parties(acto_ctx["pf"], acto_ctx["pm"])
        if not all_parties:
            logger.warning("No hay PARTES (PF/PM) para buscar/crear y sacar UIF.")
            return

        logger.info(f"Procesando {len(all_parties)} parte(s) del acto: {acto_ctx['acto_nombre']}")
        for idx, party in enumerate(all_parties, start=1):
            logger.info(f"===== PARTE {idx}/{len(all_parties)} :: {party.get('tipo')} | {party.get('rol') or '-'} | {party.get('nombre_upper')} =====")
            try:
                _process_party(driver, wait, base, party)
            except Exception as e:
                logger.exception(f"Error procesando parte [{party.get('nombre_upper')}]: {e}")

        logger.success("Todas las partes del acto han sido procesadas.")
        # (Más adelante: iterar actos/proyectos; por ahora solo el primero sin _cache_bot)
        """
        _fill_new_project_fields(driver,wait,acto_ctx["cliente_principal"],acto_ctx["pf"],acto_ctx["pm"], acto_ctx["acto_nombre"])
        

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
