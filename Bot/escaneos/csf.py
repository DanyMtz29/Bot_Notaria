#imports independientes
import re
from pypdf import PdfReader
import fitz
from rapidocr_onnxruntime import RapidOCR

class ProcesadorCSF:
    def __init__(self):
        self.engine = RapidOCR()

    def extraer_datos(self, ruta_archivo: str):
        try:
            texto_completo = ""
            es_imagen = ruta_archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))
            if es_imagen:
                 return self.extraccion_sin_texto(ruta_archivo)
            reader = PdfReader(ruta_archivo)
            for pagina in reader.pages:
                texto_extraido = pagina.extract_text()
                if texto_extraido:
                    texto_completo += texto_extraido + "\n"

            if len(texto_completo.strip()) > 50:
                return self.extraccion_con_texto(texto_completo)
            else:
                return self.extraccion_sin_texto(ruta_archivo)

        except Exception as e:
            return None

    def acortar_texto(self, palabra_clave: str, texto:str) -> str:
        idx_primer_coincidencia = 0
        idx_palabra = 0
        for i in range(0, len(texto)):
            if texto[i] == palabra_clave[idx_palabra]:
                if idx_palabra == 0:
                    idx_primer_coincidencia = i
                idx_palabra += 1
                if idx_palabra == len(palabra_clave):
                    return idx_primer_coincidencia
            else:
                idx_palabra = 0

    def extraccion_con_texto(self, texto: str):
        denominacion = nombre_completo = nombre_s = primer_apellido = segundo_apellido = rfc = idcif = None
        if "Nombre (s):" in texto or "Primer Apellido:" in texto:
            match_rfc = re.search(r"RFC:?\s*([A-Z&Ñ0-9]{12,13})", texto, re.IGNORECASE)
            match_idcif = re.search(r"idCIF:?\s*(\d+)", texto, re.IGNORECASE)
            match_nom = re.search(r"N[o0]mb[rn][eo]\s*\([sz]?\)[:.;]?\s*(.*?)(?=\s*P[rl1i]+m[eo]r)", texto, re.IGNORECASE)
            match_pa = re.search(r"P[rl1i]+m[eo]r\s*Ap[eo]l+[i1l]d[oa][:.;]?\s*(.*?)(?=\s*S[eo]g[uü]nd[oa])", texto, re.IGNORECASE)
            match_sa = re.search(r"S[eo]g[uü]nd[oa]\s*Ap[eo]l+[i1l]d[oa][:.;]?\s*(.*?)(?=\s*(?:RFC|Fecha|F[oe]cha|Inicio|$))", texto, re.IGNORECASE)

            if match_rfc: rfc = match_rfc.group(1).strip()
            if match_idcif: idcif = match_idcif.group(1).strip()
            
            if match_nom: nombre_s = match_nom.group(1).strip()
            if match_pa: primer_apellido = match_pa.group(1).strip()
            if match_sa: segundo_apellido = match_sa.group(1).strip()

            partes = [p for p in [nombre_s, primer_apellido, segundo_apellido] if p]
            nombre_completo = " ".join(partes)

            return nombre_completo, rfc, idcif, nombre_s, primer_apellido, segundo_apellido 
        else:
            match_rfc = re.search(r"RFC:?\s*([A-Z&Ñ0-9]{12,13})", texto, re.IGNORECASE)
            match_idcif = re.search(r"idCIF:?\s*(\d+)", texto, re.IGNORECASE)
            #match_nom = re.search(r"Denominaci[óo]n/Raz[óo]n\s*Social:?\s*(.+)", texto, re.IGNORECASE)
            match_nom = re.search(r"D[e0o]n[o0]m[i1l][nr]ac[il1][oó0]n[/|il1]Raz[oó0s]n\s*S[o0]c[il1]a[l1][:.;]?\s*(.+)", texto, re.IGNORECASE)

            if match_rfc: rfc = match_rfc.group(1).strip()
            if match_idcif: idcif = match_idcif.group(1).strip()
            if match_nom: denominacion = match_nom.group(1).strip()

            return denominacion, rfc, idcif

    def extraccion_sin_texto(self, ruta_archivo: str):
        texto_acumulado = ""
        
        try:#Probar si es imagen
            if ruta_archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                resultado, _ = self.engine(ruta_archivo)
                if resultado:
                    texto_acumulado = " ".join([res[1] for res in resultado])
            else:
                doc = fitz.open(ruta_archivo)
                pagina = doc.load_page(0) 
                
                mat = fitz.Matrix(2, 2)
                pix = pagina.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                
                resultado, _ = self.engine(img_bytes)

                if resultado:
                    texto_acumulado = "\n".join([res[1] for res in resultado])
                
                doc.close()
            return self.extraccion_con_texto(texto_acumulado)

        except Exception as e:
            return None