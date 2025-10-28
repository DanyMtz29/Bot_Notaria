# bot/core/csf.py
from __future__ import annotations
import os
import re
from typing import Optional, Tuple
from loguru import logger

# =========================
# Lectura de texto
# =========================
def _read_pdf_text(path: str) -> str:
    """
    Intenta extraer texto de un PDF usando pdfminer.six.
    """
    try:
        from pdfminer.high_level import extract_text
    except Exception as e:
        logger.error("pdfminer.six no está instalado o falló el import: {}", e)
        return ""
    try:
        text = extract_text(path) or ""
        if not text.strip():
            logger.warning("El PDF no devolvió texto (¿escaneado?) -> {}", path)
        return text
    except Exception as e:
        logger.exception("Error extrayendo texto del PDF {}: {}", path, e)
        return ""

def _read_image_text(path: str) -> str:
    """
    Intenta OCR con pytesseract si está disponible.
    """
    try:
        from PIL import Image
        import pytesseract
    except Exception as e:
        logger.warning("OCR no disponible (instala pillow + pytesseract). Motivo: {}", e)
        return ""
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang="spa+eng")
        return text or ""
    except Exception as e:
        logger.exception("Error haciendo OCR a {}: {}", path, e)
        return ""

def read_text_from_file(path: str) -> str:
    """
    Lee texto de un archivo CSF (PDF o imagen).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _read_pdf_text(path)
    elif ext in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        return _read_image_text(path)
    else:
        logger.error("Extensión no soportada para CSF: {}", ext)
        return ""

# =========================
# Parsers RFC + IDCIF
# =========================
# RFC: 3 o 4 letras (& y Ñ válidas), 6 dígitos de fecha, 3 alfanum homoclave
RFC_RE = re.compile(r"\b([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3})\b", re.IGNORECASE)

# IDCIF: patrones comunes que aparecen como "ID CIF", "ID-CIF", "IDCIF", etc.
# Captura una cadena alfanumérica (y guiones) de 6-24 caracteres justo después.
IDCIF_RE = re.compile(
    r"(?:ID\s*[-_]?\s*CIF|IDCIF|ID\s*CIF)[\s:]*([A-Z0-9\-]{6,24})",
    re.IGNORECASE
)

def parse_idcif_and_rfc(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Devuelve (rfc, idcif) si se detectan en el texto.
    Si hay varios RFC, se prioriza el primero que luzca como persona moral (12) o física (13).
    """
    rfc = None
    idcif = None

    # RFC
    rfcs = RFC_RE.findall(text or "")
    if rfcs:
        # Normaliza a mayúsculas
        rfcs = [r.upper() for r in rfcs]
        # Heurística: prioriza el que tenga longitud 12 o 13 (válidas)
        rfcs = [r for r in rfcs if len(r) in (12, 13)] or rfcs
        rfc = rfcs[0]

    # IDCIF
    m = IDCIF_RE.search(text or "")
    if m:
        idcif = m.group(1).upper()

    return rfc, idcif

def extract_csf_fields(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Carga el archivo y extrae (RFC, IDCIF).
    """
    logger.info("Extrayendo texto de CSF: {}", path)
    text = read_text_from_file(path)
    if not text:
        logger.warning("No se pudo extraer texto de la CSF ({}).", path)
        return None, None

    rfc, idcif = parse_idcif_and_rfc(text)
    logger.debug("Parse result -> RFC={}, IDCIF={}", rfc, idcif)
    return rfc, idcif
