# bot/core/faltantes.py
from __future__ import annotations
import os
import re
import ast
import json
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from loguru import logger

# Reusa tus detectores del proyecto
from bot.core.files import ActosFinder


class FaltantesService:
    """
    Servicio para leer/actualizar el JSON de 'papeleria_faltante.json',
    resolver carpetas (PF/PM/INM) con fuzzy matching de nombres,
    y detectar documentos presentes (detector + patrón regex en nombres de archivo).
    """

    FILENAME = "papeleria_faltante.json"
    CACHE_DIRNAME = "_cache_bot"
    VALID_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".webp",
                  ".doc", ".docx", ".xls", ".xlsx"}

    # --------------------- Mapeo: nombre visible -> detector ActosFinder ---------------------
    DOC_CHECKS: Dict[str, callable] = {
        # PERSONA (PF)
        "CURP (compareciente o partes)": ActosFinder.find_curp,
        "Identificación oficial (compareciente o partes)": ActosFinder.find_ine,
        "Comprobante de Domicilio (compareciente o partes)": ActosFinder.find_comprobante_domicilio,
        "Acta de nacimiento (compareciente o partes)": ActosFinder.find_acta_nacimiento,
        "Constancia de identificación fiscal (compareciente o partes)": ActosFinder.find_csf_in_folder,

        # SOCIEDAD (PM)
        "Acta constitutiva (antecedente)": ActosFinder.find_acta_constitutiva,
        "Poder del representante legal": ActosFinder.find_poder_representante,
        "Asambleas antecedente de la sociedad": ActosFinder.find_asambleas,

        # INMUEBLE (INM)
        "Escritura Antecedente (Inmueble)": ActosFinder.find_escritura_antecedente,
        "Recibo de pago del impuesto predial": ActosFinder.find_recibo_predial,
        "Avalúo Catastral": ActosFinder.find_avaluo_catastral,
        "Avalúo Comercial": ActosFinder.find_avaluo_comercial,
        "Avalúo Referido": ActosFinder.find_avaluo_referido,
        "Aviso preventivo": ActosFinder.find_aviso_preventivo,
        "Solicitud de Avalúo": ActosFinder.find_solicitud_avaluo,
        "Plano": ActosFinder.find_plano,
        "Título de Propiedad": ActosFinder.find_titulo_propiedad,
        "No Adeudo Agua": ActosFinder.find_no_adeudo_agua,
        "Lista Nominal": ActosFinder.find_lista_nominal,
    }

    # --------------------- Fallback por regex en nombres de archivo ---------------------
    DOC_PATTERNS: Dict[str, re.Pattern] = {
        # PERSONA (PF)
        "CURP (compareciente o partes)": re.compile(r"\bcurp\b", re.I),
        "Identificación oficial (compareciente o partes)": re.compile(r"\b(ine|identificaci[oó]n|ife)\b", re.I),
        "Comprobante de Domicilio (compareciente o partes)": re.compile(
            r"\b(comprobante.*domicilio|recibo.*(luz|agua|tel[eé]fono|cfe|cable))\b", re.I),
        "Acta de nacimiento (compareciente o partes)": re.compile(r"\bacta.*nacimiento\b", re.I),
        "Constancia de identificación fiscal (compareciente o partes)": re.compile(
            r"\b(csf|constancia.*(fiscal|rfc)|c[eé]dula.*fiscal)\b", re.I),

        # SOCIEDAD (PM)
        "Acta constitutiva (antecedente)": re.compile(r"\b(acta.*constitutiva|constitutiva)\b", re.I),
        "Poder del representante legal": re.compile(r"\b(poder|poder.*representante)\b", re.I),
        "Asambleas antecedente de la sociedad": re.compile(r"\b(asamblea|asambleas)\b", re.I),

        # INMUEBLE (INM)
        "Escritura Antecedente (Inmueble)": re.compile(r"\b(escritura.*antecedente|escritura)\b", re.I),
        "Recibo de pago del impuesto predial": re.compile(r"\b(predial|recibo.*predial)\b", re.I),
        "Avalúo Catastral": re.compile(r"\b(avalu[oó].*catastral)\b", re.I),
        "Avalúo Comercial": re.compile(r"\b(avalu[oó].*comercial)\b", re.I),
        "Avalúo Referido": re.compile(r"\b(avalu[oó].*referido)\b", re.I),
        "Aviso preventivo": re.compile(r"\b(aviso.*preventivo)\b", re.I),
        "Solicitud de Avalúo": re.compile(r"\b(solicitud.*avalu[oó])\b", re.I),
        "Plano": re.compile(r"\b(plano|planos)\b", re.I),
        "Título de Propiedad": re.compile(r"\b(t[ií]tulo.*propiedad)\b", re.I),
        "No Adeudo Agua": re.compile(r"\b(no.*adeudo.*agua)\b", re.I),
        "Lista Nominal": re.compile(r"\b(lista.*nominal)\b", re.I),
    }

    INM_DIR_NAMES = ("Inmueble", "Inmuebles")

    # =====================================================================
    # ---------------------------- API PÚBLICA ----------------------------
    # =====================================================================

    @classmethod
    def procesar_proyecto(cls, project_dir: str) -> Tuple[Dict[str, List[Tuple[str, str]]], dict]:
        """
        Lee _cache_bot/papeleria_faltante.json si existe y:
         - Si la fecha <= 15 días: valida qué docs ya existen en disco y los quita de faltantes.
         - Devuelve:
             archivos_para_subir: { key_str : [(nombre_doc, ruta_abs), ...] }
             json_actualizado: dict final (guardado en el archivo). Si queda completo, sólo tendrá 'Fecha de registro'.
        NO sube nada al portal: sólo resuelve rutas y limpia el JSON.
        """
        cache_dir = os.path.join(project_dir, cls.CACHE_DIRNAME)
        data = cls._leer_json_faltantes(cache_dir)
        if not data:
            logger.info("No hay JSON de faltantes en {}", cache_dir)
            return {}, {}

        fecha = data.get("Fecha de registro")
        if not fecha or not cls._dentro_de_15_dias(fecha):
            logger.info("JSON fuera de ventana (15 días) o sin fecha. Se regresa intacto.")
            return {}, data

        descripcion = data.get("Descripcion del proyecto","")
        contadores_prev = data.get("Contadores",{})
        contadores_new = contadores_prev.copy()
        archivos_para_subir: Dict[str, List[Tuple[str, str]]] = {}

        nuevo_data: dict = {"Fecha de registro": fecha}
        nuevo_data["Descripcion del proyecto"] = descripcion

        for k, faltantes in data.items():
            if k == "Fecha de registro":
                continue
            if not isinstance(faltantes, list):
                continue
            if not faltantes:
                continue

            try:
                tipo, nombre, rol = cls._parse_tuple_key(k)
            except Exception as e:
                logger.warning("No pude parsear la llave '{}': {}", k, e)
                nuevo_data[k] = faltantes
                continue

            entity_folder = cls._resolver_folder_entity(project_dir, tipo, nombre, rol)
            if not entity_folder:
                # No hay carpeta local para ese ente, conserva faltantes
                nuevo_data[k] = faltantes
                continue

            still_missing, encontrados = cls._check_docs_in_folder(entity_folder, faltantes)
            #print(f"Contadores despues de check: {contadores}")
            
            if encontrados:
                archivos_para_subir[k] = [(n, ruta) for n, ruta in encontrados.items()]
                #Para filtrar los encontrados en el JSON
                for archivo_portal in encontrados.keys():
                    contadores_new[archivo_portal]-=1
                    if contadores_new[archivo_portal] == 0: del contadores_new[archivo_portal]

            if still_missing:
                nuevo_data[k] = still_missing
        #Se guarda la nueva data si se actualizo
        if contadores_new:
            nuevo_data["Contadores"] = contadores_new

        #cls._guardar_json_faltantes(cache_dir, nuevo_data)
        return descripcion, archivos_para_subir, contadores_prev, nuevo_data

    # =====================================================================
    # -------------------------- UTIL DE ARCHIVO ---------------------------
    # =====================================================================

    @classmethod
    def _leer_json_faltantes(cls, cache_dir: str) -> Optional[dict]:
        path = os.path.join(cache_dir, cls.FILENAME)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _guardar_json_faltantes(cls, cache_dir: str, data: dict) -> None:
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, cls.FILENAME)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _dentro_de_15_dias(iso: str) -> bool:
        try:
            t0 = datetime.fromisoformat(iso)
            return datetime.now() - t0 <= timedelta(days=15)
        except Exception:
            return True  # si fecha inválida, procesamos por seguridad

    # =====================================================================
    # -------------------------- PARSEO DE CLAVE ---------------------------
    # =====================================================================

    @staticmethod
    def _parse_tuple_key(key_str: str) -> Tuple[str, str, str]:
        """
        Convierte: "('PF', 'NOMBRE PF', 'Comprador')" -> ('PF','NOMBRE PF','Comprador')
        Espera SIEMPRE una tupla de 3.
        """
        try:
            t = ast.literal_eval(key_str)
            if isinstance(t, tuple) and len(t) == 3:
                return t[0], t[1], t[2]
        except Exception:
            pass
        m = re.findall(r"'([^']*)'", key_str)
        if len(m) >= 3:
            return m[0], m[1], m[2]
        raise ValueError(f"Formato de llave no reconocido: {key_str}")

    # =====================================================================
    # ---------------------- RESOLVER CARPETAS (PF/PM/INM) ----------------
    # =====================================================================

    @staticmethod
    def _strip_acc(s: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(ch))

    @classmethod
    def _norm_text(cls, s: str) -> str:
        s = cls._strip_acc(s).lower()
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def _tokens(cls, s: str) -> set:
        stop = {"de", "del", "la", "el", "los", "las", "y", "o", "en", "con", "para", "por",
                "al", "a", "se", "su", "sus", "un", "una", "uno", "unos", "unas"}
        return {t for t in cls._norm_text(s).split() if t and t not in stop}

    @classmethod
    def _score_name_similarity(cls, query_name: str, candidate: str) -> float:
        tq, tc = cls._tokens(query_name), cls._tokens(candidate)
        if not tq or not tc:
            return 0.0
        inter = len(tq & tc)
        union = len(tq | tc)
        jacc = inter / union
        bonus = 0.0
        # primer token coincide
        if tq and next(iter(tq)) in tc:
            bonus += 0.15
        # últimos tokens (apellidos)
        q_last = list(tq)[-1]
        if q_last in tc:
            bonus += 0.15
        if len(tq) >= 2 and list(tq)[-2] in tc:
            bonus += 0.10
        return jacc + bonus

    @classmethod
    def _fuzzy_best_match_subdir(cls, base_dir: str, target_name: str, min_score: float = 0.25) -> Optional[str]:
        if not os.path.isdir(base_dir):
            return None
        best, best_score = None, 0.0
        for d in os.listdir(base_dir):
            full = os.path.join(base_dir, d)
            if not os.path.isdir(full):
                continue
            s = cls._score_name_similarity(target_name, d)
            if s > best_score:
                best, best_score = full, s
        return best if best_score >= min_score else None

    @classmethod
    def _buscar_dir_inmueble(cls, project_dir: str, nombre_inmueble: str) -> Optional[str]:
        for base in cls.INM_DIR_NAMES:
            base_path = os.path.join(project_dir, base)
            if os.path.isdir(base_path):
                cand = os.path.join(base_path, nombre_inmueble)
                if os.path.isdir(cand):
                    return cand
                # si no hay subcarpetas con ese nombre, usa /Inmueble(s) directo
                return base_path
        return None

    @classmethod
    def _buscar_dir_persona_o_sociedad(cls, project_dir: str, rol: str, nombre: str) -> Optional[str]:
        # /<ROL>/<NOMBRE> exacto o fuzzy
        rol_dir = os.path.join(project_dir, rol)
        if os.path.isdir(rol_dir):
            exact = os.path.join(rol_dir, nombre)
            if os.path.isdir(exact):
                return exact
            fuzzy = cls._fuzzy_best_match_subdir(rol_dir, nombre)
            if fuzzy:
                return fuzzy

        # fallback: directorios cuyo nombre contenga el rol
        candidates = []
        for d in os.listdir(project_dir):
            full = os.path.join(project_dir, d)
            if os.path.isdir(full) and cls._norm_text(rol) in cls._norm_text(d):
                candidates.append(full)

        for cand in candidates:
            fuzzy = cls._fuzzy_best_match_subdir(cand, nombre)
            if fuzzy:
                return fuzzy

        return None

    @classmethod
    def _resolver_folder_entity(cls, project_dir: str, tipo: str, nombre: str, rol: str) -> Optional[str]:
        t = (tipo or "").upper()
        if t in ("INM", "INMUEBLE"):
            return cls._buscar_dir_inmueble(project_dir, nombre)
        return cls._buscar_dir_persona_o_sociedad(project_dir, rol, nombre)

    # =====================================================================
    # ------------------- DETECCIÓN DE DOCUMENTOS EN DISCO ----------------
    # =====================================================================

    @classmethod
    def _fallback_find_by_pattern(cls, folder: str, doc_name: str, max_depth: int = 3) -> Optional[str]:
        pat = cls.DOC_PATTERNS.get(doc_name)
        if not pat or not folder or not os.path.isdir(folder):
            return None

        base_depth = folder.count(os.sep)
        for root, dirs, files in os.walk(folder):
            # limitar profundidad de búsqueda
            if root.count(os.sep) - base_depth > max_depth:
                dirs[:] = []
                continue

            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in cls.VALID_EXTS:
                    continue
                if pat.search(fn):
                    return os.path.join(root, fn)
        return None

    @classmethod
    def _check_docs_in_folder(cls, folder: str, nombres_docs: List[str]) -> Tuple[List[str], Dict[str, str], Dict[str, int]]:
        """
        Devuelve:
            still_missing -> lista de nombres que aún faltan
            encontrados -> {nombre_doc: ruta}
            contadores -> {nombre_doc: faltantes_restantes}
        """
        still_missing: List[str] = []
        encontrados: Dict[str, str] = {}

        for doc_name in nombres_docs:
            key = (doc_name or "").strip()
            ruta = None

            # 1) Intentar con detector "oficial"
            checker = cls.DOC_CHECKS.get(key)
            if checker:
                try:
                    ruta = checker(folder)
                except Exception:
                    ruta = None

            # 2) Fallback por nombre
            if not ruta:
                ruta = cls._fallback_find_by_pattern(folder, key)

            if ruta:
                encontrados[key] = ruta
            else:
                still_missing.append(doc_name)


        return still_missing, encontrados
