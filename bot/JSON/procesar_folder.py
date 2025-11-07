import os
import json
import time

from loguru import logger
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any, Set
from urllib.parse import urlsplit

from bot.pages.uif_modal import UifModal
from bot.pages.clients_page import ClientsPage
from bot.pages.customer_detail_page import CustomerDetailPage
from bot.pages.customers_cif_modal import CustomersCifModal
from bot.pages.customers_create_confirm_modal import CustomersCreateConfirmModal
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class Folder:
    # =========================
    # Helpers de serialización
    # =========================
    def _to_jsonable(self,obj):
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            return {k: self._to_jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._to_jsonable(x) for x in obj]
        try:
            return {k: self._to_jsonable(v) for k, v in obj.__dict__.items()}
        except Exception:
            return str(obj)

    # =========================
    # Helpers genéricos (safe get)
    # =========================
    def _get(self, obj: Any, key: str, default=None):
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
    def _origin_of(self, url: str) -> str:
        p = urlsplit(url)
        return f"{p.scheme}://{p.netloc}"

    def _find_first_acto_without_cache(self,root_dir: str) -> list:#Optional[str]:
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
                return [full,True]
            else:
                logger.debug(f"SKIP (ya tiene _cache_bot): {full}")
                return [full,False]
        return None

    def _ensure_cache_and_write_json(self,acto_dir: str, extraction) -> str:
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
            "data": self._to_jsonable(extraction),
        }
        out_json = os.path.join(cache_dir, "acto.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.success(f"JSON generado: {out_json}")
        return out_json

    # =========================
    # Helpers de PARTES (PF/PM)
    # =========================
    def _pf_to_dict(self,pf_obj) -> Optional[Dict[str, str]]:
        try:
            rol = self._get(pf_obj, "rol", "") or ""
            persona = self._get(pf_obj, "persona")
            nombre = (self._get(persona, "nombre") or self._get(pf_obj, "nombre") or "").strip()
            rfc = (self._get(persona, "rfc") or self._get(pf_obj, "rfc") or "").strip()
            idcif = (
                self._get(persona, "idcif")
                or self._get(persona, "IdCIF")
                or self._get(persona, "IDCIF")
                or self._get(pf_obj, "idcif")
                or ""
            )
            docs = self._get(pf_obj, "docs") or self._get(persona, "docs")
            if not nombre:
                return None
            return {"tipo": "PF", "rol": rol, "nombre": nombre, "rfc": rfc, "idcif": str(idcif).strip(), "docs": docs}
        except Exception:
            return None

    def _pm_to_dict(self, pm_obj) -> Optional[Dict[str, str]]:
        try:
            rol = self._get(pm_obj, "rol", "") or ""
            # En PM el nombre suele ser la razón social
            nombre = (self._get(pm_obj, "nombre") or self._get(pm_obj, "razon_social") or "").strip()
            rfc = (self._get(pm_obj, "rfc") or "").strip()
            idcif = (self._get(pm_obj, "idcif") or self._get(pm_obj, "IdCIF") or self._get(pm_obj, "IDCIF") or "").strip()
            if not nombre:
                return None
            return {"tipo": "PM", "rol": rol, "nombre": nombre, "rfc": rfc, "idcif": idcif}
        except Exception:
            return None

    def _extract_partes_pf_pm(self, extraction) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Devuelve:
        - pf_list: [{'tipo':'PF','rol':..,'nombre':..,'rfc':..,'idcif':..}, ...]
        - pm_list: [{'tipo':'PM','rol':..,'nombre':..,'rfc':..,'idcif':..}, ...]
        """
        #pf_list: List[Dict[str, str]] = []
        pf_list = []
        for pf in getattr(extraction, "partes_pf", []) or []:
            d = self._pf_to_dict(pf)
            if d:
                pf_list.append(d)

        pm_list: List[Dict[str, str]] = []
        for pm in getattr(extraction, "partes_pm", []) or []:
            d = self._pm_to_dict(pm)
            if d:
                pm_list.append(d)

        return pf_list, pm_list

    def _print_partes_console(self, pf_list: List[Dict[str, str]], pm_list: List[Dict[str, str]], acto_nombre: str):
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

    def _flatten_all_parties(self, pf_list: List[Dict[str, str]], pm_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
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

    def _safe_pdf_name(self, party: Dict[str, str]) -> str:
        base = f"{party.get('tipo','')}_{party.get('rol','')}_{party.get('nombre_upper','')}".strip("_")
        # Limpia caracteres raros para nombre de archivo
        cleaned = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in base)
        return cleaned.replace("  ", " ").replace(" ", "_")

    def check(self, xpath):
        try:
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return True;
        except Exception:
            return False

    def press(self, but):
        self.driver.execute_script("arguments[0].click();", but)
    # =========================
    # Flujo por PARTE
    # =========================
    def _process_party(self,lista_uifs:list,driver, wait, base: str, party: Dict[str, str]) -> None:
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

                #CAMBIO DE PORTAL, ACTUALIZACION===========================================
                XPATH_HIST = "//button[contains(@class, 'btn-light') and contains(., 'Comprobante Histórico')]"
                XPATH_BUSCAR = "//button[contains(@class, 'btn-primary') and contains(., 'Buscar de nuevo')]"
                try:
                    # Esperar a que haya al menos un botón de comprobante histórico
                    wait.until(EC.presence_of_element_located((By.XPATH, XPATH_HIST)))
                    botones = driver.find_elements(By.XPATH, XPATH_HIST)
                    boton_hist = botones[-1]  # siempre el último
                except:
                    buscar_btn = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_BUSCAR)))
                    buscar_btn.click()

                    # Esperar a que aparezca al menos un botón de comprobante histórico
                    wait.until(EC.presence_of_element_located((By.XPATH, XPATH_HIST)))
                    time.sleep(1.5)  # pequeño respiro extra por carga dinámica
                    botones = driver.find_elements(By.XPATH, XPATH_HIST)
                    boton_hist = botones[-1]

                # Clic en el último botón encontrado
                wait.until(EC.element_to_be_clickable(boton_hist))
                boton_hist.click()
                time.sleep(3)
                
                lista_uifs.append(UifModal(driver, wait).renombrar_ultimo_pdf(self._safe_pdf_name(party)))
                #lista_uifs[party['nombre_upper']] = UifModal(driver, wait).renombrar_ultimo_pdf(_safe_pdf_name(party))
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

        # Crear cliente y confirmar
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
            lista_uifs.append(UifModal(driver, wait).renombrar_ultimo_pdf(self._safe_pdf_name(party)))
            #lista_uifs[party['nombre_upper']] = UifModal(driver, wait).renombrar_ultimo_pdf(_safe_pdf_name(party))
            logger.success("UIF descargado y renombrado (post-creación).")
        finally:
            cp.open_direct(base)
            cp.assert_loaded()