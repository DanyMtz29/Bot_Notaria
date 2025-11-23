"""
    CAMBIOS 
    DPI = 450
"""

import re
import fitz
from rapidocr import RapidOCR


# =============================
#  SEPARADOR DE NOMBRES PEGADOS
# =============================
def separar_nombre_pegado(s: str) -> str:
    """
    Separa solo nombres realmente pegados:
    ALFREDOALBERTO -> ALFREDO ALBERTO
    MARIAJOSE -> MARIA JOSE
    JOSELUIS -> JOSE LUIS

    No toca nombres normales como:
    ARACELI, SOFIA, KAREN, PAMELA, PAOLA
    """

    s = s.strip().upper()

    # Si ya tiene espacio NO dividir
    if " " in s:
        return s

    # Si es un nombre normal (<= 7 letras), NO dividir
    if len(s) <= 7:
        return s

    # Detectar posiciones candidatos (muchas transiciones)
    cortes = []
    for i in range(2, len(s)-2):
        if s[i].isupper() and s[i+1].isupper():
            cortes.append(i)

    # Si no hay transiciones internas → no dividir
    if len(cortes) < 2:
        return s

    # Eligir corte más balanceado
    mitad = len(s) // 2
    corte = min(cortes, key=lambda x: abs(x - mitad))

    return s[:corte] + " " + s[corte:]

def separar_denominacion_pegada(nombre: str) -> str:
    """
    Separa nombres de personas morales pegados, sin afectar nombres normales.
    Ej:
      DESARROLLADORAVILLARI → DESARROLLADORA VILLARI
      GRUPOINDUSTRIALPEREZ → GRUPO INDUSTRIAL PEREZ
      CONSTRUCTORAALTAVISTA → CONSTRUCTORA ALTAVISTA

    No divide elementos cortos:
      VILLARI → VILLARI
      HIKARI → HIKARI
      TRIOSA → TRIOSA
    """
    s = nombre.strip().upper()

    # si ya está separado → no tocar
    if " " in s:
        return s

    # palabras cortas → no separar (brand names)
    if len(s) <= 8:
        return s

    # candidatos de corte basados en prefijos de palabras frecuentes
    prefijos = [
        "CONSTRU", "CONSTRUCTORA", "SERVICIOS", "GRUPO", "GRUPOINDUSTRIAL",
        "INDUSTRIAL", "DESARROLLADORA", "INMOBILIARIA", "COMERCIALIZADORA",
        "TRANSPORTES", "SOLUCIONES", "TECNOLOGIA", "PROYECTOS"
    ]

    # buscar prefijo dentro del string
    for pref in prefijos:
        if s.startswith(pref):
            if len(pref) < len(s):
                return pref + " " + s[len(pref):]

    # fallback: cortar en una posición equilibrada
    mitad = len(s) // 2

    # buscar una vocal cercana a la mitad
    mejores = []
    for i in range(4, len(s)-4):
        if s[i] in "AEIOU":
            mejores.append((abs(i-mitad), i))

    if mejores:
        _, corte = min(mejores, key=lambda x: x[0])
        return s[:corte] + " " + s[corte:]

    return s

# =============================
#  EXTRACTOR CSF
# =============================
class ExtractorCSF:

    def __init__(self, dpi: int = 450):
        self.ocr_engine = RapidOCR()
        self.dpi = dpi

    
    def _extraer_nombre_moral(self, texto: str) -> str | None:
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]

        patrones = [
            r"^Denominacion\/?Razon Social\s*:?\s*(.*)$",
            r"^Nombre,denominacion\s*o\s*razon\s*social\s*:?\s*(.*)$"
        ]

        # 1) Buscar inmediatamente en la misma línea
        for i, linea in enumerate(lineas):
            for p in patrones:
                m = re.match(p, linea, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if val:
                        return separar_denominacion_pegada(val)
                    # puede venir en la siguiente línea
                    if i + 1 < len(lineas):
                        return separar_denominacion_pegada(lineas[i + 1].strip())

        # 2) Si no existe, intentar usar la línea debajo del RFC en el encabezado
        for i in range(len(lineas)-1):
            if re.match(r"^Registro\s+Federal\s+de\s+Contribuyentes$", lineas[i], re.IGNORECASE):
                return separar_denominacion_pegada(lineas[i+1])

        return None

    # ------------------------------
    #  OCR con reconstrucción básica
    # ------------------------------
    def _extraer_texto(self, ruta: str) -> str:
        ext = ruta.lower().split(".")[-1]

        def reconstruir(result):
            if not result.txts:
                return ""

            # Usamos SOLO txts; ignora coordenadas (no sirven en CSF)
            lineas = []
            for t in result.txts:
                t = t.replace("  ", " ")
                t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
                lineas.append(t)

            return "\n".join(lineas)

        if ext in ("jpg", "jpeg", "png"):
            with open(ruta, "rb") as f:
                img = f.read()
            out = self.ocr_engine(img)
            return reconstruir(out)

        elif ext == "pdf":
            doc = fitz.open(ruta)
            paginas = []
            for page in doc:
                pix = page.get_pixmap(dpi=self.dpi)
                img = pix.tobytes("png")
                out = self.ocr_engine(img)
                paginas.append(reconstruir(out))
            doc.close()
            return "\n".join(paginas)

        else:
            raise ValueError("Formato no soportado")

    # =============================
    #  EXTRACCIÓN PROPIA DE CSF
    # =============================

    def _buscar_valor_bajo_etiqueta(self, texto, etiqueta):
        """
        Para patrones tipo:
        Nombre (s):
        AlfredoAlberto
        """
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]

        patron = rf"^{etiqueta}\s*:?\s*(.*)$"

        for i, linea in enumerate(lineas):
            m = re.match(patron, linea, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val:   # valor en la misma línea
                    return val
                elif i+1 < len(lineas):  # viene debajo
                    return lineas[i+1].strip()

        return None

    def _extraer_nombre(self, texto):

        nombre = self._buscar_valor_bajo_etiqueta(texto, r"Nombre\s*\(s\)")
        ap1    = self._buscar_valor_bajo_etiqueta(texto, r"Primer\s*Apellido")
        ap2    = self._buscar_valor_bajo_etiqueta(texto, r"Segundo\s*Apellido")

        if not nombre:
            return None
        if nombre.isupper() and " " not in nombre:
            nombre = separar_nombre_pegado(nombre)

        partes = [nombre]
        if ap1:
            partes.append(ap1)
        if ap2:
            partes.append(ap2)

        return " ".join(partes)

    def _extraer_rfc(self, texto):
        patron = r"\b([A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3})\b"
        m = re.search(patron, texto)
        return m.group(1) if m else None

    def _extraer_idcif(self, texto):
        patron = r"id\s*cif[:\s]*([A-Za-z0-9]+)"
        m = re.search(patron, texto, re.IGNORECASE)
        return m.group(1) if m else None

    # =============================
    #  MÉTODO PRINCIPAL
    # =============================
    def extraer_datos_csf(self, ruta: str) -> dict:
        texto = self._extraer_texto(ruta)

        rfc = self._extraer_rfc(texto)
        idcif = self._extraer_idcif(texto)

        # si encontramos etiquetas de persona física → procesar FY
        if "Nombre (s):" in texto or "Primer Apellido" in texto:
            nombre = self._extraer_nombre(texto)
        else:
            nombre = self._extraer_nombre_moral(texto)

        return {
            "rfc": rfc,
            "idcif": idcif,
            "nombre": nombre,
            "texto_completo": texto
        }
