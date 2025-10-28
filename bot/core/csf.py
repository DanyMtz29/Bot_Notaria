# bot/core/csf.py
from __future__ import annotations
import os
import re
from typing import Optional, Tuple
from loguru import logger

# ========= Lectura de PDF/Imagen =========
def _read_pdf_text_fitz(path: str) -> str:
    try:
        import fitz
    except Exception as e:
        logger.debug("PyMuPDF no disponible: {}", e)
        return ""
    try:
        parts = []
        with fitz.open(path) as doc:
            for p in doc:
                parts.append(p.get_text("text") or "")
        return "\n".join(parts)
    except Exception as e:
        logger.exception("PyMuPDF falló con {}: {}", path, e)
        return ""

def _read_pdf_text_pdfminer(path: str) -> str:
    try:
        from pdfminer.high_level import extract_text
    except Exception as e:
        logger.debug("pdfminer.six no disponible: {}", e)
        return ""
    try:
        return extract_text(path) or ""
    except Exception as e:
        logger.exception("pdfminer.six falló con {}: {}", path, e)
        return ""

def _read_pdf_text_pdfplumber(path: str) -> str:
    try:
        import pdfplumber
    except Exception as e:
        logger.debug("pdfplumber no disponible: {}", e)
        return ""
    try:
        parts = []
        with pdfplumber.open(path) as pdf:
            for pg in pdf.pages:
                parts.append(pg.extract_text() or "")
        return "\n".join(parts)
    except Exception as e:
        logger.exception("pdfplumber falló con {}: {}", path, e)
        return ""

def _read_image_text(path: str) -> str:
    try:
        from PIL import Image
        import pytesseract
    except Exception as e:
        logger.debug("OCR no disponible: {}", e)
        return ""
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang="spa+eng") or ""
    except Exception as e:
        logger.exception("OCR falló con {}: {}", path, e)
        return ""

def read_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        for fn in (_read_pdf_text_fitz, _read_pdf_text_pdfminer, _read_pdf_text_pdfplumber):
            t = fn(path)
            if t and t.strip():
                logger.debug("Texto obtenido con {} ({} chars)", fn.__name__, len(t))
                return t
        logger.warning("No se obtuvo texto del PDF -> {}", path)
        return ""
    elif ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        return _read_image_text(path)
    else:
        logger.error("Extensión no soportada: {}", ext)
        return ""

# ========= Regex =========
RFC_RE = re.compile(r"\b([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3})\b", re.IGNORECASE)
IDCIF_RE = re.compile(r"(?:ID\s*[-_]?\s*CIF|IDCIF)\s*[:\-]?\s*([A-Z0-9\-]{6,30})", re.IGNORECASE)

# Nombre puede venir como:
# - “Nombre, denominación o razón social” en la cabecera (línea siguiente)
# - Sección de datos: "Nombre(s): ....  Primer apellido: ....  Segundo apellido: ...."
NOMBRE_HEADER_RE = re.compile(
    r"Nombre,\s*denominación\s*o\s*razón\s*social\s*\n+([A-ZÁÉÍÓÚÑ\s]+)\n", re.IGNORECASE
)
NOMBRES_RE = re.compile(
    r"Nombre\(s\)\s*:\s*([A-ZÁÉÍÓÚÑ\s]+)\s+Primer\s+apellido\s*:\s*([A-ZÁÉÍÓÚÑ\s]+)\s+Segundo\s+apellido\s*:\s*([A-ZÁÉÍÓÚÑ\s]+)",
    re.IGNORECASE
)

def _clean_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def parse_fields(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Devuelve (RFC, idCIF, NOMBRE_COMPLETO)."""
    rfc = None
    idcif = None
    nombre = None

    # RFC
    rfcs = RFC_RE.findall(text or "")
    if rfcs:
        rfcs = [r.upper() for r in rfcs]
        prefer = [r for r in rfcs if len(r) in (12, 13)]
        rfc = (prefer or rfcs)[0]

    # idCIF
    m = IDCIF_RE.search(text or "")
    if m:
        idcif = _clean_spaces(m.group(1).upper())

    # Nombre por header
    mh = NOMBRE_HEADER_RE.search(text or "")
    if mh:
        nombre = _clean_spaces(mh.group(1).upper())
    else:
        # Nombre(s) + apellidos
        mn = NOMBRES_RE.search(text or "")
        if mn:
            nombre = _clean_spaces(f"{mn.group(2)} {mn.group(3)} {mn.group(1)}").upper()

    return rfc, idcif, nombre

def extract_csf_fields(path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Lee archivo y extrae (RFC, idCIF, NOMBRE)."""
    logger.info("Extrayendo texto de CSF: {}", path)
    text = read_text_from_file(path)
    if not text:
        logger.warning("No se pudo extraer texto de la CSF ({}).", path)
        return None, None, None
    return parse_fields(text)
