# bot/core/csf.py
from __future__ import annotations
import re
from typing import Optional, Tuple, Iterable
from loguru import logger

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

# =============== API pública (con fallback a OCR) ===============
def extract_csf_fields(path: str):
    # 1) intentar lectura posicional si hay texto
    has_text = _pdf_has_selectable_text(path)
    rfc = idcif = nombre = None

    if has_text:
        print("TIENE TEXTO!!")
    else:
        print("NO TIENE TEXTO!!")

    if has_text:
        # print(f"INPUT: {path}")
        rfc, idcif, nombre = _extract_positional_fields(path)
        # logger.info(f"RFC: {rfc}, Nombre: {nombre}, IDCIF: {idcif}")

    # 2) fallback a EasyOCR si no hay texto o faltó todo
    if (not has_text) or (not any([rfc, idcif, nombre])):
        # print(f"Entra aca: {path}")
        if CSFScanner is not None:
            logger.info("Usando EasyOCR fallback (sin Tesseract) en {}", path)
            csf = CSFScanner(langs=("es","en"), gpu=False)
            nombre, rfc, idcif = csf.scan(path)
            # rfc = rfc or r2
            # idcif = idcif or i2
            # nombre = nombre or n2
        else:
            logger.warning("No está disponible CsfEasyOCRExtractor.")

    return rfc, idcif, nombre