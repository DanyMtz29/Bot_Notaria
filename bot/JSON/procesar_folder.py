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
from selenium.webdriver.common.keys import Keys
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
            esposa_o_esposo = self._get(pf_obj, "esposa_o_esposo") or self._get(persona, "esposa_o_esposo")
            if esposa_o_esposo:
                esposa_o_esposo = {
                    "esposa_o_esposo": True,
                    "rol": rol,
                    "nombre": self._get(esposa_o_esposo, "nombre", "").strip(),
                    "rfc": self._get(esposa_o_esposo, "rfc", "").strip(),
                    "idcif": self._get(esposa_o_esposo, "idcif", "").strip(),
                    "docs": self._get(esposa_o_esposo, "docs"),
                }
            if not nombre:
                return None
            return {"tipo": "PF", "rol": rol, "nombre": nombre, "rfc": rfc, "idcif": str(idcif).strip(), "docs": docs,
                    "esposa_o_esposo": esposa_o_esposo}
        except Exception:
            return None

    def _pm_to_dict(self, pm_obj) -> Optional[Dict[str, str]]:
        try:
            rol = self._get(pm_obj, "rol", "") or ""
            # En PM el nombre suele ser la razón social
            nombre = (self._get(pm_obj, "nombre") or self._get(pm_obj, "razon_social") or "").strip()
            rfc = (self._get(pm_obj, "rfc") or "").strip()
            idcif = (self._get(pm_obj, "idcif") or self._get(pm_obj, "IdCIF") or self._get(pm_obj, "IDCIF") or "").strip()
            docs = self._get(pm_obj, "docs")
            es_banco = self._get(pm_obj, "es_banco") or False
            carta_instruccion = self._get(pm_obj, "carta_instruccion")
            representante = self._get(pm_obj, "representante")
            if representante:
                representante = {
                    "representante": True,
                    "rol": rol,
                    "nombre": (self._get(representante, "nombre") or "").strip(),
                    "rfc": (self._get(representante, "rfc") or "").strip(),
                    "idcif": (
                        self._get(representante, "idcif")
                        or self._get(representante, "IdCIF")
                        or self._get(representante, "IDCIF")
                        or ""
                    ),
                    "docs": self._get(representante, "docs")
                }
            if not nombre:
                return None
            return {"tipo": "PM", "rol": rol, "nombre": nombre, "rfc": rfc, "idcif": idcif,
                    "docs": docs, "es_banco": es_banco, "carta_instruccion": carta_instruccion,
                    "representante": representante}
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