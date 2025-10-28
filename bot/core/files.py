# bot/core/files.py
from __future__ import annotations
import os
import re
import unicodedata
from typing import Optional, List, Iterable
from loguru import logger

CSF_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
DOC_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}

def _strip_accents(s: str) -> str:
    if not s:
        return s
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))

def _normalize_name(name: str) -> str:
    """
    Normaliza nombres de archivo para facilitar coincidencias:
    - minúsculas
    - sin acentos
    - separadores no alfanum -> espacio
    - además genera una forma 'aplastada' sin espacios/guiones para detectar acrónimos (acta_nac -> actanac)
    """
    base = _strip_accents(name).lower()
    # reemplaza cualquier no alfanum por espacio
    tokens_line = re.sub(r"[^a-z0-9]+", " ", base).strip()
    # forma aplastada sin espacios
    squashed = re.sub(r"\s+", "", tokens_line)
    return tokens_line, squashed

class ActosFinder:
    @staticmethod
    def compraventa_path(root_dir: str, nombre_carpeta: str = "Compraventa Daniel") -> str:
        import os
        return os.path.join(os.path.abspath(root_dir), nombre_carpeta)

    @staticmethod
    def ensure_dir(path: str, label: str) -> bool:
        import os
        from loguru import logger
        if not os.path.isdir(path):
            logger.error("No existe la carpeta {} -> {}", label, path)
            return False
        logger.debug("Carpeta {} OK -> {}", label, path)
        return True

    @staticmethod
    def _pick_best(paths: list[str]) -> str | None:
        if not paths:
            return None
        # Prioriza PDF; luego orden alfabético estable
        paths.sort(key=lambda p: (0 if p.lower().endswith(".pdf") else 1, p.lower()))
        return paths[0]

    # ---------- Motor de coincidencias flexible ----------
    @staticmethod
    def _match_name(filename: str,
                    any_of: list[str] = None,
                    all_of: list[str] = None,
                    regexes: list = None) -> bool:
        """
        Orden correcto:
        1) Normaliza nombre (tokens_line y squashed).
        2) Si hay regexes y cualquiera hace match en tokens_line o squashed -> ACEPTA (prioridad).
        3) Si no hubo regex match, evalúa any_of/all_of de forma flexible.
        """
        import re
        any_of = any_of or []
        all_of = all_of or []
        regexes = regexes or []

        # Normalización (usa tus helpers si están fuera de la clase)
        tokens_line, squashed = _normalize_name(filename)  # p.ej. "acta nac" y "actanac"
        tokens_line_words = tokens_line.split()

        # 1) PRIORIDAD: regexes
        for rx in regexes:
            if rx.search(tokens_line) or rx.search(squashed):
                return True

        # 2) any_of: basta con que uno esté en tokens_line o en la forma aplastada
        if any_of:
            hit_any = any(tok in tokens_line or tok in squashed for tok in any_of)
            if not hit_any:
                return False

        # 3) all_of: todos deben estar presentes (tokens_line o squashed)
        if all_of:
            if not all(tok in tokens_line or tok in squashed for tok in all_of):
                return False

        # Si no hubo restricciones o ya pasaron, acepta
        return bool(any_of or all_of)

    @staticmethod
    def _find_by_criteria(folder: str,
                          exts: set[str],
                          any_of: list[str] = None,
                          all_of: list[str] = None,
                          regexes: list = None) -> str | None:
        import os
        from loguru import logger
        any_of = any_of or []
        all_of = all_of or []
        regexes = regexes or []

        candidates: list[str] = []
        try:
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if not os.path.isfile(full):
                    continue
                _, ext = os.path.splitext(name)
                if exts and ext.lower() not in exts:
                    continue
                if ActosFinder._match_name(name, any_of=any_of, all_of=all_of, regexes=regexes):
                    candidates.append(full)
        except Exception as e:
            logger.exception("Error leyendo {}: {}", folder, e)
            return None
        return ActosFinder._pick_best(candidates)

    # ---------- CSF ----------
    @staticmethod
    def find_csf_in_comprador(comprador_dir: str) -> str | None:
        import re
        from loguru import logger
        if not ActosFinder.ensure_dir(comprador_dir, "Comprador"):
            return None

        regexes = [
            re.compile(r"\bcsf\b"),
            re.compile(r"constancia\s+de\s+situacion\s+fiscal"),
            re.compile(r"cedula\s+de\s+identificacion\s+fiscal"),
            re.compile(r"\bcedula\s+fiscal\b"),
        ]
        path = ActosFinder._find_by_criteria(
            comprador_dir, DOC_EXTS, regexes=regexes
        )
        if path:
            logger.info("CSF localizado: {}", path)
        else:
            logger.warning("No se encontró archivo de CSF en {}", comprador_dir)
        return path

    # ---------- CURP ----------
    @staticmethod
    def find_curp(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bcurp\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    # ---------- ACTA DE NACIMIENTO ----------
    @staticmethod
    def find_acta_nacimiento(folder: str) -> str | None:
        import re
        # Acepta explícitos y acrónimos: acta_nac / acta-nac / actanac
        regexes = [
            re.compile(r"\bacta\s+de\s+nacimiento\b"),
            re.compile(r"\bacta\s+nacimiento\b"),
            re.compile(r"\bacta[_\- ]*nac\b"),
            re.compile(r"\bactanac\b"),
        ]
        # Nota: ya no exigimos 'nacimiento' en all_of; los regexes lo cubren
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    # ---------- INE / Identificación ----------
    @staticmethod
    def find_ine(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bine\b"),
            re.compile(r"\bife\b"),
            re.compile(r"\bidentificacion\b"),
            re.compile(r"\bidentificacion\s+oficial\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    # ---------- Comprobante de domicilio (opcional) ----------
    @staticmethod
    def find_comprobante_domicilio(folder: str) -> str | None:
        import re
        # A) Nombre explícito y acrónimos
        regexes = [
            re.compile(r"\bcomprobante\s+de\s+domicilio\b"),
            re.compile(r"\bcomp[_\- ]*dom\b"),   # comp_dom / comp-dom / comp dom
            re.compile(r"\bcompdom\b"),
        ]
        p = ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)
        if p:
            return p

        # B) Recibos típicos usados como comprobante
        return ActosFinder._find_by_criteria(
            folder, DOC_EXTS,
            any_of=["cfe", "luz", "agua", "predial", "telmex", "telefono", "telefono", "izzi", "megacable", "infinitum"]
        )