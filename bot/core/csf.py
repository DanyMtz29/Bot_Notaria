# bot/core/csf.py
from __future__ import annotations
import re
from typing import Optional, Tuple, Iterable
from loguru import logger

# ========= EXTRACCIÓN POSICIONAL CON PyMuPDF =========
# Requiere: pip install pymupdf

try:
    import fitz  # PyMuPDF
except Exception as e:  # pragma: no cover
    fitz = None
    logger.error("PyMuPDF (fitz) no está disponible: {}", e)


# ---------------- utilidades ----------------
def _norm_upper(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    # colapsa espacios (incluye NBSP) y sube a MAYÚSCULAS
    return " ".join(s.replace("\xa0", " ").split()).upper()


def _tokens_right_of(page, etiqueta: str) -> Optional[str]:
    """
    Busca la 'etiqueta' en la página y regresa el texto (tokens) que están
    en la misma banda horizontal y a la DERECHA de la etiqueta.
    """
    rects = page.search_for(etiqueta)
    if not rects:
        return None
    r = rects[0]
    y0, y1 = r.y0 - 2, r.y1 + 2  # tolerancia vertical
    tokens = []
    # page.get_text("words") => [x0, y0, x1, y1, text, block_no, line_no, word_no]
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


# ---------------- extracción principal ----------------
def _extract_positional_fields(pdf_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Lee una CSF del SAT y extrae (RFC, idCIF, NOMBRE_COMPLETO) por posiciones.
    - Prioriza las etiquetas: 'RFC:', 'idCIF:', 'Nombre (s):', 'Primer Apellido:', 'Segundo Apellido:'.
    - Tolera variantes comunes con/ sin espacio y con dos puntos Unicode.
    """
    if fitz is None:
        logger.error("No se puede leer {} porque PyMuPDF no está instalado.", pdf_path)
        return None, None, None

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.exception("No se pudo abrir PDF {}: {}", pdf_path, e)
        return None, None, None

    rfc = idcif = nombres = ap1 = ap2 = None

    # Variantes de etiquetas que se ven en CSF reales
    RFC_LABELS = ("RFC:", "RFC :")
    IDCIF_LABELS = ("idCIF:", "idCIF :", "idCIF")  # a veces sin los dos puntos
    NOMBRES_LABELS = ("Nombre (s):", "Nombre(s):", "Nombre(s) :", "Nombre (s) :")
    AP1_LABELS = ("Primer Apellido:", "Primer Apellido :", "Apellido paterno:", "Apellido paterno :")
    AP2_LABELS = ("Segundo Apellido:", "Segundo Apellido :", "Apellido materno:", "Apellido materno :")

    try:
        for page in doc:
            # RFC
            if not rfc:
                for lab in RFC_LABELS:
                    rfc = _tokens_right_of(page, lab) or rfc
                    if rfc:
                        break
            # idCIF
            if not idcif:
                for lab in IDCIF_LABELS:
                    idcif = _tokens_right_of(page, lab) or idcif
                    if idcif:
                        break
            # Nombre(s) y Apellidos
            if not nombres:
                for lab in NOMBRES_LABELS:
                    nombres = _tokens_right_of(page, lab) or nombres
                    if nombres:
                        break
            if not ap1:
                for lab in AP1_LABELS:
                    ap1 = _tokens_right_of(page, lab) or ap1
                    if ap1:
                        break
            if not ap2:
                for lab in AP2_LABELS:
                    ap2 = _tokens_right_of(page, lab) or ap2
                    if ap2:
                        break

        doc.close()
    except Exception as e:
        logger.exception("Error leyendo tokens posicionales en {}: {}", pdf_path, e)
        try:
            doc.close()
        except Exception:
            pass
        return None, None, None

    # Normalización
    rfc = _norm_upper(rfc)
    idcif = _norm_upper(idcif)
    nombres = _norm_upper(nombres)
    ap1 = _norm_upper(ap1)
    ap2 = _norm_upper(ap2)

    # Construcción del nombre completo:
    #   PF: "APELLIDO_PATERNO APELLIDO_MATERNO NOMBRES"
    #   Si solo hay una parte, úsala.
    nombre_completo = None
    if ap1 or ap2 or nombres:
        partes = [p for p in (nombres, ap1, ap2) if p]
        nombre_completo = " ".join(partes) if partes else None

    # Filtro anti-ruido: quita cualquier cola que empiece con etiquetas de tabla
    if nombre_completo:
        nombre_completo = re.sub(
            r"\b(FECHA|ESTATUS|NOMBRE\s+COMERCIAL|DOMICILIO|C[ÓO]DIGO|REG[IÍ]MEN|RFC|CURP|LUGAR|ENTIDAD|MUNICIPIO|COLONIA|CALLE)\b.*",
            "",
            nombre_completo,
            flags=re.IGNORECASE,
        ).strip()
        # evita que parezca RFC o que venga demasiado corto
        if re.search(r"\d", nombre_completo) or len(nombre_completo.split()) < 2:
            nombre_completo = None

    return rfc, idcif, nombre_completo


# =============== API PÚBLICA (lo que usa el scanner) ===============
def extract_csf_fields(path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Devuelve (RFC, idCIF, NOMBRE/RAZÓN SOCIAL) desde una CSF usando lectura posicional.
    Si no se encuentra algo, retorna None en ese campo.
    """
    logger.info("Extrayendo CSF (posicional) desde: {}", path)
    rfc, idcif, nombre = _extract_positional_fields(path)

    # Log útil para diagnosticar
    logger.debug("CSF extraída -> RFC={}, idCIF={}, Nombre='{}'", rfc, idcif, nombre)
    return rfc, idcif, nombre
