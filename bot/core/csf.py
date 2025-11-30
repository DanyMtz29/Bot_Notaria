# bot/core/csf.py
from __future__ import annotations
import re
from typing import Optional, Tuple, Iterable
from loguru import logger
from bot.core.csf_ocr import ExtractorCSF

try:
    import fitz  # PyMuPDF
except Exception as e:  # pragma: no cover
    fitz = None
    logger.error("PyMuPDF (fitz) no está disponible: {}", e)

# ...
try:
    from .csf_ocr import CSFScanner   # <— EasyOCR (sin Tesseract)
except Exception:
    CSFScanner = None
    logger.warning("CSFScanner no disponible.")

# ...

_CSF_SCANNER = None

def _get_csf_scanner():
    """
    Inicializa CSFScanner una sola vez y reutiliza la misma instancia.
    Esto evita el costo brutal de cargar EasyOCR en cada PDF.
    """
    global _CSF_SCANNER

    # Si ya está cargado, lo reusamos
    if _CSF_SCANNER is not None:
        return _CSF_SCANNER

    # Si no está disponible la clase, no hay nada que hacer
    if 'CSFScanner' not in globals() or CSFScanner is None:
        logger.warning("CSFScanner no está disponible (csf_ocr no se pudo importar).")
        return None

    try:
        _CSF_SCANNER = CSFScanner(langs=("es", "en"), gpu=False)
    except Exception as e:
        logger.error("Error inicializando CSFScanner: {}", e)
        _CSF_SCANNER = None

    return _CSF_SCANNER

def _norm_upper(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return " ".join(s.replace("\xa0", " ").split()).upper()

# >>> NEW: detectar si el PDF tiene texto seleccionable
def _pdf_has_selectable_text(pdf_path: str) -> bool:
    if fitz is None:
        return False
    try:
        doc = fitz.open(pdf_path)
        try:
            for page in doc:
                txt = page.get_text("text") or ""
                if txt.strip():
                    return True
        finally:
            doc.close()
    except Exception:
        return False
    return False

def _tokens_right_of(page, etiqueta: str) -> Optional[str]:
    rects = page.search_for(etiqueta)
    if not rects:
        return None
    r = rects[0]
    y0, y1 = r.y0 - 2, r.y1 + 2
    tokens = []
    for x0, y0w, x1, y1w, text, *_ in page.get_text("words"):
        midy = (y0w + y1w) / 2.0
        if y0 <= midy <= y1 and x0 >= r.x1 - 1:
            tokens.append((x0, text))
    if not tokens:
        return None
    tokens.sort(key=lambda t: t[0])
    return " ".join(t[1] for t in tokens).strip() or None

def _first_nonempty(values: Iterable[Optional[str]]) -> Optional[str]:
    for v in values:
        if v:
            return v
    return None

def _extract_positional_fields(pdf_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if fitz is None:
        logger.error("No se puede leer {} porque PyMuPDF no está instalado.", pdf_path)
        return None, None, None
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.exception("No se pudo abrir PDF {}: {}", pdf_path, e)
        return None, None, None

    rfc = idcif = nombres = ap1 = ap2 = None

    RFC_LABELS = ("RFC:", "RFC :")
    IDCIF_LABELS = ("idCIF:", "idCIF :", "idCIF")
    NOMBRES_LABELS = ("Nombre (s):", "Nombre(s):", "Nombre(s) :", "Nombre (s) :")
    AP1_LABELS = ("Primer Apellido:", "Primer Apellido :", "Apellido paterno:", "Apellido paterno :")
    AP2_LABELS = ("Segundo Apellido:", "Segundo Apellido :", "Apellido materno:", "Apellido materno :")

    try:
        for page in doc:
            if not rfc:
                for lab in RFC_LABELS:
                    rfc = _tokens_right_of(page, lab) or rfc
                    if rfc: break
            if not idcif:
                for lab in IDCIF_LABELS:
                    idcif = _tokens_right_of(page, lab) or idcif
                    if idcif: break
            if not nombres:
                for lab in NOMBRES_LABELS:
                    nombres = _tokens_right_of(page, lab) or nombres
                    if nombres: break
            if not ap1:
                for lab in AP1_LABELS:
                    ap1 = _tokens_right_of(page, lab) or ap1
                    if ap1: break
            if not ap2:
                for lab in AP2_LABELS:
                    ap2 = _tokens_right_of(page, lab) or ap2
                    if ap2: break
        doc.close()
    except Exception as e:
        logger.exception("Error leyendo tokens posicionales en {}: {}", pdf_path, e)
        try:
            doc.close()
        except Exception:
            pass
        return None, None, None

    rfc = _norm_upper(rfc)
    idcif = _norm_upper(idcif)
    nombres = _norm_upper(nombres)
    ap1 = _norm_upper(ap1)
    ap2 = _norm_upper(ap2)

    nombre_completo = None
    if ap1 or ap2 or nombres:
        partes = [p for p in (nombres, ap1, ap2) if p]
        nombre_completo = " ".join(partes) if partes else None

    if nombre_completo:
        nombre_completo = re.sub(
            r"\b(FECHA|ESTATUS|NOMBRE\s+COMERCIAL|DOMICILIO|C[ÓO]DIGO|REG[IÍ]MEN|RFC|CURP|LUGAR|ENTIDAD|MUNICIPIO|COLONIA|CALLE)\b.*",
            "",
            nombre_completo,
            flags=re.IGNORECASE,
        ).strip()
        if re.search(r"\d", nombre_completo) or len(nombre_completo.split()) < 2:
            nombre_completo = None

    return rfc, idcif, nombre_completo

def extract_csf_fields(path: str):
    """
    Extrae RFC, idCIF y nombre a partir de una CSF.
    1) Intenta lectura posicional con PyMuPDF (texto seleccionable).
    2) Si no hay texto o falta algo, hace fallback a EasyOCR (CSFScanner) reutilizable.
    """
    # 1) Intentar lectura posicional si hay texto
    has_text = _pdf_has_selectable_text(path)
    rfc = idcif = nombre = None

    # Logs suaves, sin prints en consola
    logger.debug("Analizando CSF {} (tiene texto seleccionable: {})", path, has_text)

    if has_text:
        try:
            rfc, idcif, nombre = _extract_positional_fields(path)
            logger.debug("CSF posicional -> RFC={}, idcif={}, nombre={}", rfc, idcif, nombre)
        except Exception as e:
            logger.warning("Error en extracción posicional de CSF {}: {}", path, e)

    # 2) Fallback a EasyOCR si no hay texto o faltó todo
    if (not has_text) or (not any([rfc, idcif, nombre])):
        extr = ExtractorCSF()
        datos = extr.extraer_datos_csf(path)
        rfc = datos.get("rfc","")
        idcif = datos.get("idcif", "")
        nombre = datos.get("nombre_completo","")

    return rfc, idcif, nombre