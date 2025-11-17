# # bot/core/csf_scanner.py
# import re
# import cv2
# import numpy as np
# import fitz  # PyMuPDF
# import easyocr
# import unicodedata

# # ---------------- Normalización ----------------
# def strip_accents(s: str) -> str:
#     return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")

# def NORM(s: str) -> str:
#     if s is None:
#         return ""
#     s = strip_accents(s).upper()
#     s = re.sub(r"\s+", " ", s).strip()
#     return s

# # -------- RegEx generales --------
# RFC_RE   = re.compile(r"\b([A-ZÑ&]{3,4}\d{6}[A-Z0-9]{2,3})\b")
# IDCIF_RE = re.compile(r"\b\d{11}\b")

# # -------- Variantes del label (PM) --------
# LABEL_PATTERNS = [
#     r"DENOMINACION\s*/?\s*RAZON\s*/?\s*SOCIAL",
#     r"RAZON\s*/?\s*SOCIAL",
#     r"NOMBRE[, ]*DENOMINACION[, ]*O[, ]*RAZON\s*/?\s*SOCIAL",
# ]

# # -------- Variantes de labels (PF) --------
# LABEL_PF_NOMBRES = [r"\bNOMBRE\s*\(?S\)?\b", r"\bNOMBRES?\b"]
# LABEL_PF_PRIMER_AP = [r"\bPRIMER\s+APELLIDO\b", r"\bAPELLIDO\s+PATERNO\b"]
# LABEL_PF_SEGUNDO_AP = [r"\bSEGUNDO\s+APELLIDO\b", r"\bAPELLIDO\s+MATERNO\b"]

# BAD_TOKENS = {"CEDULA","IDENTIFICACION","FISCAL","LUGAR","FECHA","EMISION","EXPEDICION","DOMICILIO","REGIMEN","CONSTANCIA"}

# def tipo_por_rfc(rfc: str) -> str | None:
#     if not rfc:
#         return None
#     m = re.match(r"^[A-ZÑ&]{3,4}", rfc)
#     if not m:
#         return None
#     return "MORAL" if len(m.group(0)) == 3 else "FISICA"

# class CSFScanner:
#     """
#     PM: Denominación/Razón Social (lógica original).
#     PF: Nombre(s) + Primer Apellido + Segundo Apellido limitado al bloque 'Datos de Identificación del Contribuyente'.
#     """

#     def __init__(self, langs=("es","en"), gpu=False):
#         self.reader = easyocr.Reader(langs, gpu=gpu)

#     # -------- PDF -> imágenes --------
#     def _pdf_to_images(self, path_pdf, zoom=3.2):
#         doc = fitz.open(path_pdf)
#         mat = fitz.Matrix(zoom, zoom)
#         pages = []
#         for i in range(len(doc)):
#             page = doc.load_page(i)
#             pix  = page.get_pixmap(matrix=mat, alpha=False)
#             img  = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
#             pages.append(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
#         doc.close()
#         return pages

#     # -------- OCR con cajas --------
#     def _ocr_boxes(self, path):
#         imgs = self._pdf_to_images(path) if path.lower().endswith(".pdf") else [cv2.imread(path)]
#         boxes = []  # (page, (x0,y0,x1,y1), text, conf)
#         lines_plain = []
#         for pi, img in enumerate(imgs):
#             if img is None:
#                 continue
#             res = self.reader.readtext(img, detail=1, paragraph=False)
#             for (poly, text, conf) in res:
#                 xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
#                 x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
#                 boxes.append((pi, (x0, y0, x1, y1), (text or "").strip(), float(conf)))
#                 lines_plain.append((text or "").strip())
#         boxes.sort(key=lambda t: (t[0], (t[1][1]+t[1][3])/2.0, t[1][0]))
#         return boxes, "\n".join(lines_plain)

#     # -------- helpers geométricos --------
#     @staticmethod
#     def _yc(b):  # centro Y
#         return (b[1] + b[3]) / 2.0

#     @staticmethod
#     def _overlap(a0,a1,b0,b1):
#         inter = max(0.0, min(a1,b1) - max(a0,b0))
#         den = max(1.0, min(a1-a0, b1-b0))
#         return inter/den

#     # -------- agrupar por renglones --------
#     def _group_rows(self, boxes, y_tol=8.0):
#         rows = {}
#         row_refs = {}
#         next_row_id = 0
#         for i, (pi, (x0,y0,x1,y1), text, conf) in enumerate(boxes):
#             yc = (y0+y1)/2.0
#             found = None
#             row_list = row_refs.setdefault(pi, [])
#             for (ry, rid) in row_list:
#                 if abs(yc - ry) <= y_tol:
#                     found = rid; break
#             if found is None:
#                 rid = next_row_id; next_row_id += 1
#                 row_refs[pi].append((yc, rid))
#             else:
#                 rid = found
#             rows.setdefault((pi, rid), []).append(i)
#         for k, idxs in rows.items():
#             idxs.sort(key=lambda j: boxes[j][1][0])
#         return rows

#     # -------- localizar label (PM) --------
#     def _find_label_rows(self, boxes, rows):
#         label_hits = []  # [(page, rid, label_idx, label_bbox)]
#         for (pi, rid), idxs in rows.items():
#             norm_join = NORM(" ".join(boxes[j][2] for j in idxs))
#             for pat in LABEL_PATTERNS:
#                 if re.search(pat, norm_join):
#                     for j in idxs:
#                         tnorm = NORM(boxes[j][2])
#                         if re.search(pat, tnorm):
#                             label_hits.append((pi, rid, j, boxes[j][1])); break
#                     else:
#                         xs = [boxes[j][1][0] for j in idxs] + [boxes[j][1][2] for j in idxs]
#                         ys = [boxes[j][1][1] for j in idxs] + [boxes[j][1][3] for j in idxs]
#                         label_hits.append((pi, rid, idxs[0], (min(xs), min(ys), max(xs), max(ys))))
#                     break
#         return label_hits

#     # -------- localizar label (genérico, para PF) --------
#     def _find_label_rows_by(self, boxes, rows, patterns, exclude_phrases=None, restrict_keys=None):
#         exclude_phrases = exclude_phrases or set()
#         hits = []
#         for (pi, rid), idxs in rows.items():
#             if restrict_keys is not None and (pi, rid) not in restrict_keys:
#                 continue
#             joined = NORM(" ".join(boxes[j][2] for j in idxs))
#             if any(ph in joined for ph in exclude_phrases):
#                 continue
#             for pat in patterns:
#                 if re.search(pat, joined):
#                     for j in idxs:
#                         if re.search(pat, NORM(boxes[j][2])):
#                             hits.append((pi, rid, j, boxes[j][1])); break
#                     else:
#                         xs = [boxes[j][1][0] for j in idxs] + [boxes[j][1][2] for j in idxs]
#                         ys = [boxes[j][1][1] for j in idxs] + [boxes[j][1][3] for j in idxs]
#                         hits.append((pi, rid, idxs[0], (min(xs), min(ys), max(xs), max(ys))))
#                     break
#         return hits

#     # -------- del renglón del label, tomar todo a la derecha --------
#     def _take_right_side_text(self, boxes, rows, pi, rid, label_bbox, min_h_overlap=0.5, min_gap_px=6):
#         idxs = rows[(pi, rid)]
#         lx0, ly0, lx1, ly1 = label_bbox
#         parts = []
#         for j in idxs:
#             p2, (x0,y0,x1,y1), txt, conf = boxes[j]
#             if p2 != pi: 
#                 continue
#             if x0 >= lx1 + min_gap_px and self._overlap(ly0, ly1, y0, y1) >= min_h_overlap:
#                 if txt:
#                     parts.append((x0, txt))
#         parts.sort(key=lambda t: t[0])
#         joined = " ".join(p[1] for p in parts).strip()
#         return joined or None

#     # -------- filtros para nombre (PM) --------
#     def _valid_nombre(self, s: str) -> bool:
#         if not s:
#             return False
#         sn = NORM(s)
#         if len(sn) < 3:
#             return False
#         toks = set(sn.split())
#         if BAD_TOKENS & toks:
#             return False
#         return len(sn.split()) >= 2 or len(sn) >= 8

#     # -------- filtro celda PF --------
#     def _valid_pf_cell(self, s: str) -> bool:
#         if not s:
#             return False
#         sn = NORM(s)
#         if sn in {"NOMBRE","NOMBRES","NOMBRE S","PRIMER APELLIDO","SEGUNDO APELLIDO","APELLIDO PATERNO","APELLIDO MATERNO"}:
#             return False
#         if BAD_TOKENS & set(sn.split()):
#             return False
#         return True

#     # -------- fallback: renglón inferior --------
#     def _take_next_row(self, boxes, rows, pi, rid, label_bbox):
#         lx0, ly0, lx1, ly1 = label_bbox
#         yc = (ly0+ly1)/2.0
#         cand = []
#         for (p2, rid2), idxs in rows.items():
#             if p2 != pi or (p2, rid2) == (pi, rid):
#                 continue
#             ys = [ (boxes[j][1][1]+boxes[j][1][3])/2.0 for j in idxs ]
#             rc = sum(ys)/len(ys)
#             if rc > yc:
#                 cand.append((rc, rid2))
#         if not cand:
#             return None
#         cand.sort(key=lambda t: t[0])
#         rid2 = cand[0][1]
#         parts = [boxes[j][2] for j in rows[(pi, rid2)]]
#         return (" ".join(parts).strip()) or None

#     # -------- RFC / IDCIF de todo el texto --------
#     def _extract_rfc(self, full_text: str):
#         m = RFC_RE.search(NORM(full_text))
#         return m.group(1) if m else None

#     def _extract_idcif(self, full_text: str):
#         m = IDCIF_RE.search(NORM(full_text))
#         return m.group(0) if m else None

#     # -------- fallback por texto corrido (PM) --------
#     def _fallback_span_text(self, full_text: str):
#         T = NORM(full_text)
#         label_pos = None
#         for pat in LABEL_PATTERNS:
#             m = re.search(pat, T)
#             if m:
#                 label_pos = m.end(); break
#         if label_pos is None:
#             return None
#         m_rfc = RFC_RE.search(T[label_pos:])
#         end_pos = label_pos + m_rfc.start() if m_rfc else len(T)
#         seg = T[label_pos:end_pos].strip()
#         if not seg:
#             return None
#         lines = [l.strip() for l in re.split(r"[\n\r]+", seg) if l.strip()]
#         for ln in lines:
#             if "LUGAR" in ln and "FECHA" in ln:
#                 continue
#             if self._valid_nombre(ln):
#                 return ln
#         words = seg.split()
#         if len(words) >= 2:
#             cand = " ".join(words[:8]).strip()
#             if self._valid_nombre(cand):
#                 return cand
#         return None

#     # -------- límites de sección para PF --------
#     def _section_keys_identificacion(self, boxes, rows):
#         # Ordenar filas por (página, y-centro)
#         ordered = []
#         for (pi, rid), idxs in rows.items():
#             ys = [(boxes[j][1][1]+boxes[j][1][3])/2.0 for j in idxs]
#             yc = sum(ys)/len(ys)
#             ordered.append((pi, yc, rid))
#         ordered.sort()

#         start = end = None
#         for (pi, yc, rid) in ordered:
#             joined = NORM(" ".join(boxes[j][2] for j in rows[(pi, rid)]))
#             if start is None and re.search(r"\bDATOS\s+DE\s+IDENTIFICACION\s+DEL\s+CONTRIBUYENTE\b", joined):
#                 start = (pi, rid)
#             if start and end is None and re.search(r"\bDATOS\s+DEL\s+DOMICILIO\b", joined):
#                 end = (pi, rid); break

#         valid = set()
#         take = False
#         for (pi, yc, rid) in ordered:
#             key = (pi, rid)
#             if start and key == start:
#                 take = True; continue
#             if take:
#                 if end and key == end:
#                     break
#                 valid.add(key)
#         return valid  # puede estar vacío si no detecta encabezados

#     # =================== API principal ===================
#     def scan(self, path: str):
#         boxes, full_text = self._ocr_boxes(path)
#         rfc   = self._extract_rfc(full_text)
#         idcif = self._extract_idcif(full_text)

#         rows = self._group_rows(boxes, y_tol=9.0)

#         # ---------- PM (lógica original intacta) ----------
#         hits_pm = self._find_label_rows(boxes, rows)
#         nombre_pm = None
#         for (pi, rid, jlab, lbbox) in hits_pm:
#             nombre_pm = self._take_right_side_text(boxes, rows, pi, rid, lbbox)
#             if nombre_pm and self._valid_nombre(nombre_pm):
#                 break
#             alt = self._take_next_row(boxes, rows, pi, rid, lbbox)
#             if alt and self._valid_nombre(alt):
#                 nombre_pm = alt; break
#         if not nombre_pm:
#             nombre_pm = self._fallback_span_text(full_text)
#         if nombre_pm:
#             corte = re.split(r"\b(RFC|REGIMEN|NOMBRE COMERCIAL|DOMICILIO|ESTATUS|FECHA)\b", NORM(nombre_pm))
#             if corte:
#                 nombre_pm = corte[0].strip()
#             nombre_pm = " ".join(nombre_pm.split())

#         # ---------- PF (acotado a la sección de Identificación) ----------
#         ident_keys = self._section_keys_identificacion(boxes, rows)

#         def pick_pf_field(patterns):
#             hits = self._find_label_rows_by(
#                 boxes, rows, patterns,
#                 exclude_phrases={"NOMBRE COMERCIAL","DENOMINACION","RAZON","SOCIAL"},
#                 restrict_keys=(ident_keys if ident_keys else None)
#             )
#             for (pi, rid, jlab, lbbox) in hits:
#                 v = self._take_right_side_text(boxes, rows, pi, rid, lbbox)
#                 if not v or not self._valid_pf_cell(v):
#                     # siguiente renglón, pero SOLO dentro de la sección
#                     v = None
#                     # calcular next row y validar que esté en ident_keys
#                     lx0, ly0, lx1, ly1 = lbbox
#                     yc = (ly0+ly1)/2.0
#                     cand = []
#                     for (p2, rid2), idxs2 in rows.items():
#                         if p2 != pi or (p2, rid2) == (pi, rid):
#                             continue
#                         ys = [(boxes[j][1][1]+boxes[j][1][3])/2.0 for j in idxs2]
#                         rc = sum(ys)/len(ys)
#                         if rc > yc and ((pi, rid2) in ident_keys or not ident_keys):
#                             cand.append((rc, rid2))
#                     if cand:
#                         cand.sort(key=lambda t: t[0])
#                         rid2 = cand[0][1]
#                         parts = [boxes[j][2] for j in rows[(pi, rid2)]]
#                         v = (" ".join(parts).strip()) or None
#                 if v and self._valid_pf_cell(v):
#                     return v
#             return None

#         pf_nombres = pick_pf_field(LABEL_PF_NOMBRES)
#         pf_ap1     = pick_pf_field(LABEL_PF_PRIMER_AP)
#         pf_ap2     = pick_pf_field(LABEL_PF_SEGUNDO_AP)

#         nombre_pf = None
#         if pf_nombres or pf_ap1 or pf_ap2:
#             partes = [p for p in [pf_nombres, pf_ap1, pf_ap2] if p]
#             if partes:
#                 nombre_pf = " ".join(partes).strip()

#         # ---------- Resolver tipo por RFC y nombres ----------
#         tipo = tipo_por_rfc(rfc)
#         if tipo == "MORAL":
#             nombre = nombre_pm
#         elif tipo == "FISICA":
#             nombre = nombre_pf
#         else:
#             if nombre_pm and not nombre_pf:
#                 tipo, nombre = "MORAL", nombre_pm
#             elif nombre_pf and not nombre_pm:
#                 tipo, nombre = "FISICA", nombre_pf
#             elif nombre_pm and nombre_pf:
#                 tipo = "MORAL" if tipo_por_rfc(rfc) == "MORAL" else "FISICA"
#                 nombre = nombre_pm if tipo == "MORAL" else nombre_pf
#             else:
#                 tipo, nombre = None, None

#         return nombre,rfc,idcif
#         #return {"tipo_persona": tipo, "nombre": nombre, "rfc": rfc, "idcif": idcif}

# # if __name__ == "__main__":
# #     # csf = CSFScanner()
# #     # datos = csf.scan("CSF_Villari.pdf")
# #     # print(datos)
# #     csf = CSFScanner(langs=("es","en"), gpu=False)
# #     print(csf.scan("CSF_PREDIX.pdf"))   # también sirve PDF