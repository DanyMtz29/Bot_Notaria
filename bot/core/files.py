# bot/core/files.py
from __future__ import annotations
import os
import re
import unicodedata
from typing import Optional, List
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
    - forma 'aplastada' sin espacios/guiones (acta_nac -> actanac)
    """
    base = _strip_accents(name).lower()
    tokens_line = re.sub(r"[^a-z0-9]+", " ", base).strip()
    squashed = re.sub(r"\s+", "", tokens_line)
    return tokens_line, squashed

class ActosFinder:
    @staticmethod
    def compraventa_path(root_dir: str, nombre_carpeta: str = "Compraventa Daniel") -> str:
        return os.path.join(os.path.abspath(root_dir), nombre_carpeta)

    @staticmethod
    def ensure_dir(path: str, label: str) -> bool:
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
                    regexes: list[re.Pattern] = None) -> bool:
        """
        DEVUELVE True SOLO si hay coincidencia real.
        (FIX) Antes regresaba True si existían criterios aunque NO hiciera match,
        provocando que cualquier archivo 'pasara' como si coincidiera.
        """
        any_of = any_of or []
        all_of = all_of or []
        regexes = regexes or []

        tokens_line, squashed = _normalize_name(filename)

        matched = False

        # 1) regexes
        for rx in regexes:
            if rx.search(tokens_line) or rx.search(squashed):
                matched = True
                break

        # 2) any_of
        if any_of and not matched:
            if any(tok in tokens_line or tok in squashed for tok in any_of):
                matched = True

        # 3) all_of
        if all_of:
            if not all(tok in tokens_line or tok in squashed for tok in all_of):
                return False
            else:
                # si ya traíamos matched por regex/any_of o no había, con all_of cumplido vale
                matched = True

        return matched

    @staticmethod
    def _find_by_criteria(folder: str,
                          exts: set[str],
                          any_of: list[str] = None,
                          all_of: list[str] = None,
                          regexes: list[re.Pattern] = None,
                          multiple: bool = False) -> Optional[str] | List[str] | None:
        any_of = any_of or []
        all_of = all_of or []
        regexes = regexes or []

        if not folder or not os.path.isdir(folder):
            return None

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

        if not candidates:
            return None

        if multiple:
            candidates.sort(key=lambda p: (0 if p.lower().endswith(".pdf") else 1, p.lower()))
            return candidates
        return ActosFinder._pick_best(candidates)

    # ===================== GENÉRICOS =====================
    @staticmethod
    def find_csf_in_folder(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bcsf\b"),
            re.compile(r"constancia\s+de\s+situacion\s+fiscal"),
            re.compile(r"cedula\s+de\s+identificacion\s+fiscal"),
            re.compile(r"\bcedula\s+fiscal\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    # ---------- Comprador (legacy de ejemplo) ----------
    @staticmethod
    def find_csf_in_comprador(comprador_dir: str) -> str | None:
        if not ActosFinder.ensure_dir(comprador_dir, "Comprador"):
            return None
        return ActosFinder.find_csf_in_folder(comprador_dir)

    @staticmethod
    def find_curp(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bcurp\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_acta_nacimiento(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bacta\s+de\s+nacimiento\b"),
            re.compile(r"\bacta\s+nacimiento\b"),
            re.compile(r"\bacta[_\- ]*nac\b"),
            re.compile(r"\bactanac\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

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

    @staticmethod
    def find_comprobante_domicilio(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bcomprobante\s+de\s+domicilio\b"),
            re.compile(r"\bcomp[_\- ]*dom\b"),
            re.compile(r"\bcompdom\b"),
        ]
        p = ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)
        if p:
            return p
        # fallback por proveedor (cfe, agua, etc.)
        return ActosFinder._find_by_criteria(
            folder, DOC_EXTS,
            any_of=["cfe", "luz", "agua", "predial", "telmex", "telefono", "izzi", "megacable", "infinitum"]
        )

    @staticmethod
    def find_acta_matrimonio(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bacta\s+de\s+matrimonio\b"),
            re.compile(r"\bacta\s+matrimonio\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    # ===================== SOCIEDAD / PM =====================
    @staticmethod
    def find_representante_folder(folder: str) -> Optional[str]:
        if not folder or not os.path.isdir(folder):
            return None
        for name in os.listdir(folder):
            full = os.path.join(folder, name)
            if os.path.isdir(full) and _strip_accents(name).lower() in {"representante", "representante legal"}:
                return full
        return None

    @staticmethod
    def find_acta_constitutiva(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bacta\s+constitutiva\b"),
            re.compile(r"\bconstitutiva\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_poder_representante(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bpoder\b"),
            re.compile(r"\bpoder\s+del\s+representante\b"),
            re.compile(r"\bpoder\s+notarial\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_asambleas(folder: str) -> List[str]:
        import re
        regexes = [
            re.compile(r"\basamblea\b"),
            re.compile(r"\basambleas\b"),
            re.compile(r"\bacta\s+de\s+asamblea\b"),
        ]
        found = ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes, multiple=True)
        return found or []

    @staticmethod
    def find_otros_sociedad(folder: str) -> List[str]:
        """Cualquier doc que no matchee explícitos comunes. Útil para guardarlo en OTROS."""
        try:
            hits = []
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if not os.path.isfile(full):
                    continue
                _, ext = os.path.splitext(name)
                if ext.lower() not in DOC_EXTS:
                    continue
                if not any([
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bcsf\b")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bacta\s+constitutiva\b")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bpoder\b")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\basamblea")]),
                ]):
                    hits.append(full)
            hits.sort(key=lambda p: (0 if p.lower().endswith(".pdf") else 1, p.lower()))
            return hits
        except Exception as e:
            logger.exception("find_otros_sociedad error en {}: {}", folder, e)
            return []

    @staticmethod
    def has_sociedad_docs(folder: str) -> bool:
        return any([
            ActosFinder.find_acta_constitutiva(folder),
            ActosFinder.find_poder_representante(folder),
            len(ActosFinder.find_asambleas(folder)) > 0
        ])

    # ===================== INMUEBLE =====================
    @staticmethod
    def find_escritura_antecedente(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bescritura\s+(de\s+)?antecedente\b"),
            re.compile(r"\bescritura\s+antecedente\b"),
            re.compile(r"\bantecedente\s+escritura\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_cert_libertad_gravamen(folder: str) -> str | None:
        import re
        regexes = [
            re.compile(r"\bcertificado\s+de\s+libertad\s+y?\s*gravamen"),
            re.compile(r"\blibertad\s+y?\s*gravamen\b"),
            re.compile(r"\bcert[_\- ]*libertad\b"),
        ]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_avaluo_catastral(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bavaluo\s+catastral\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_avaluo_comercial(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bavaluo\s+comercial\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_avaluo_referido(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bavaluo\s+referido\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_aviso_preventivo(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\baviso\s+preventivo\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_solicitud_avaluo(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bsolicitud\s+de\s+avaluo\b"), re.compile(r"\bsolicitud\s+avaluo\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_plano(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bplano\b"), re.compile(r"\bplano\s+autorizado\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_recibo_predial(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\b(recibo|pago)\s+predial\b"), re.compile(r"\bpredial\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_titulo_propiedad(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\btitulo\s+de\s+propiedad\b"), re.compile(r"\btitulo\s+propiedad\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_no_adeudo_agua(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\bno\s+adeudo\s+agua\b"), re.compile(r"\b(no\s+)?adeudo\s+agua\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_lista_nominal(folder: str) -> str | None:
        import re
        regexes = [re.compile(r"\blista\s+nominal\b")]
        return ActosFinder._find_by_criteria(folder, DOC_EXTS, regexes=regexes)

    @staticmethod
    def find_otros_inmueble(folder: str) -> List[str]:
        try:
            hits = []
            for name in os.listdir(folder):
                full = os.path.join(folder, name)
                if not os.path.isfile(full):
                    continue
                _, ext = os.path.splitext(name)
                if ext.lower() not in DOC_EXTS:
                    continue
                if not any([
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bescritura")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\blibertad")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bavaluo")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\baviso\s+preventivo")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bsolicitud\s+de\s+avaluo")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bplano")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bpredial")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\btitulo\s+de\s+propiedad|\btitulo\s+propiedad")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\bno\s+adeudo\s+agua|\badeudo\s+agua")]),
                    ActosFinder._match_name(name, regexes=[re.compile(r"\blista\s+nominal")]),
                ]):
                    hits.append(full)
            hits.sort(key=lambda p: (0 if p.lower().endswith(".pdf") else 1, p.lower()))
            return hits
        except Exception as e:
            logger.exception("find_otros_inmueble error en {}: {}", folder, e)
            return []
