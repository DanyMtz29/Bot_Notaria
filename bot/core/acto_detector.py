# -*- coding: utf-8 -*-
"""
bot/core/acto_detector.py

ActoResolver
-------------
- Detecta el nombre CANÓNICO del acto a partir del nombre de carpeta.
- Extrae el cliente principal (solo el 1er segmento después del primer guion).
- Extrae 'escritura' si el prefijo es numérico; si es 'Esc.' / 'ESC' / 'Escritura' => None.
- No lee DOCX/Excel: todo definido aquí.

Formas de carpeta:
  "Esc. <ACTO> – <Cliente> [– lo que sea]"
  "<numero> <ACTO> – <Cliente> [– lo que sea]"
"""

from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple

# ===========================================================
# 1) LISTA OFICIAL DE ACTOS (tal cual me la diste)
# ===========================================================
ACTOS_CANONICOS: List[str] = [
    "ACLARACION O RECTIFICACION",
    "ADJUDICACION JUDICIAL",
    "ADJUDICACIÓN JUDICIAL (HERENCIA)",
    "AFP / CARTA PERMISO MENOR DE EDAD",
    "AFP / EXTRAVIO DE DOCUMENTACION",
    "AFP / FE DE HECHOS",
    "AFP / OFICIOS SUCESION",
    "AFP / PODER RATIFICADO",
    "AFP / TESTIMONIAL VEHICULAR (FACTURA)",
    "AFP/CONCUBINATO",
    "AFP/RATIFICACIÓN DE FIRMAS",
    "APERTURA DE CREDITO",
    "APORTACION A FIDEICOMISO",
    "CANCELACIÓN DE HIPOTECA",
    "CANCELACIÓN DE RESERVA DE DOMINIO",
    "CANCELACION DE USUFRUCTO",
    "CANCELACION DE USUFRUCTO VITALICIO",
    "CANCELACION PARCIAL DE HIPOTECA",
    "CAPITULACIONES MATRIMONIALES",
    "COMPRAVENTA",
    "COMPRAVENTA CON APERTURA DE CREDITO CON BANCO",
    "COMPRAVENTA FOVISSSTE",
    "COMPRAVENTA INFONAVIT",
    "CONSTITUCIÓN DE ASOCIACIONES Y SOCIEDADES CIVILES",
    "CONSTITUCION DE PATRIMONIO FAMILIAR",
    "CONSTITUCIÓN DE SOCIEDADES MERCANTILES",
    "CONVENIO MODIFICATORIO",
    "DACION EN PAGO",
    "DECLARACION DE HEREDEROS",
    "DILIGENCIAS DE JURISDICCIÓN VOLUNTARIA",
    "DONACIÓN",
    "DONACION DE DINERO",
    "EXTINCIÓN DE PATRIMONIO FAMILIAR CONCLUSIÓN",
    "FIDEICOMISO",
    "INVENTARIO Y AVALUO SUCESION",
    "PERMUTA"
    "PODER O MANDATO",
    "PROTOCOLIZACION CONDOMINIO O FRACCIONAMIENTO",
    "PROTOCOLIZACION DE ACTA DE ASAMBLEA",
    "PROTOCOLIZACION DE ADECUACION DE SUPERFICIE",
    "PROTOCOLIZACION DE CESION DE DERECHOS",
    "PROTOCOLIZACION DE CONTRATO EN GENERAL",
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICAICON Y/O LOTIFICACION",
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICAICON Y/O LOTIFICACION; CON DIVISION DE LA COSA COMUN",
    "PROTOCOLIZACION DE SENTENCIA DE DIVORCIO",
    "RECONOCIMIENTO DE ADEUDO (CONSTITUCION DE HIPOTECA)",
    "REDENCIÓN PASIVOS CON MUTUO DE FOVISSSTE",
    "REVOCACIÓN DE PODER",
    "TESTAMENTO",
    "TRANSMISION DE PROPIEDAD",
    "TRANSMISIÓN DE PROPIEDAD Y EJECUCIÓN Y EXTINCIÓN PARCIAL DE FIDEICOMISO",
]

# ===========================================================
# 2) ALIAS / SINÓNIMOS (agregados según tus ejemplos)
# ===========================================================
ALIAS_POR_ACTO: Dict[str, List[str]] = {
    # CV + variantes
    "COMPRAVENTA": [
        "cv","compra venta","compra-venta","compravta","venta","esc compra venta"
    ],
    "COMPRAVENTA INFONAVIT": [
        "cv infonavit","compra venta infonavit","infonavit compra venta","infonavit cv","compraventa infonavit"
    ],
    "COMPRAVENTA FOVISSSTE": [
        "cv fovis","cv fovissste","compra venta fovis","fovissste compra venta","fovis cv","compraventa fovissste"
    ],
    "COMPRAVENTA CON APERTURA DE CREDITO CON BANCO": [
        "compraventa apertura credito","cv apertura credito","apertura credito banco",
        "compra-venta con apertura de credito","cv ap credito banco","credito bancario",
        "compraventa apertura crédito","compraventa con apertura crédito"
    ],

    # Aclaración / Rectificación
    "ACLARACION O RECTIFICACION": [
        "aclaracion","rectificacion","rectificación","rectifica","rectificacion datos","aclaracion de"
    ],

    # Adjudicaciones
    "ADJUDICACION JUDICIAL": ["adjudicacion","adjudicación"],
    "ADJUDICACIÓN JUDICIAL (HERENCIA)": ["adjudicacion herencia","adjudicación herencia","adj herencia"],

    # AFP variantes
    "AFP / CARTA PERMISO MENOR DE EDAD": [
        "carta permiso","carta de permiso","carta permiso menor","permiso menor","permiso menor de edad",
        "permiso hijo","permiso hija","permiso hij@","permiso hijo menor","carta permiso hijo","carta permiso hija"
    ],
    "AFP / EXTRAVIO DE DOCUMENTACION": ["extravío","extravío docs","extravio","extravio documentacion"],
    "AFP / FE DE HECHOS": ["fe de hechos","fe hechos"],
    "AFP / OFICIOS SUCESION": ["oficios","oficios sucesion","oficio sucesion"],
    "AFP / PODER RATIFICADO": ["poder ratificado","ratificar poder"],
    "AFP / TESTIMONIAL VEHICULAR (FACTURA)": ["testimonial vehicular","testimonial vehicular factura","testimonioal vehicular"],
    "AFP/CONCUBINATO": ["concubinato"],
    "AFP/RATIFICACIÓN DE FIRMAS": ["ratificacion firmas","ratificación firmas","rat de firmas","rat firmas"],

    # Varios civiles/mercantiles
    "APERTURA DE CREDITO": ["apertura credito","ap credito","ap. credito","apertura crédito"],
    "APORTACION A FIDEICOMISO": ["aportacion fideicomiso","ap a fideicomiso","ap fideicomiso"],
    "CANCELACIÓN DE HIPOTECA": ["cancelacion hipoteca","cancel hipoteca","canc hipoteca"],
    "CANCELACIÓN DE RESERVA DE DOMINIO": ["cancelacion dominio","cancelación dominio"],
    "CANCELACION DE USUFRUCTO": ["cancelacion usufructo"],
    "CANCELACION DE USUFRUCTO VITALICIO": ["cancelacion usufructo vit","cancelación usufructo vitalicio"],
    "CANCELACION PARCIAL DE HIPOTECA": ["cancelacion parcial hip","cancelacion parcial hipoteca","canc parcial hipoteca"],
    "CAPITULACIONES MATRIMONIALES": ["capitulaciones patrimoniales","capitulaciones"],
    "CONSTITUCIÓN DE ASOCIACIONES Y SOCIEDADES CIVILES": ["constitución sociedades civiles","constitucion sociedades civiles","constitucion asociaciones civiles"],
    "CONSTITUCION DE PATRIMONIO FAMILIAR": ["constitucion patrimonio","constitución patrimonio familiar"],
    "CONSTITUCIÓN DE SOCIEDADES MERCANTILES": ["constitucion sociedades mercantiles","constitución sociedades mercantiles"],
    "CONVENIO MODIFICATORIO": ["convenio modificatorio","convenio modif"],
    "DACION EN PAGO": ["dacion en pago","dación en pago","dacion"],
    "DECLARACION DE HEREDEROS": ["declaracion de herederos","declaración de herederos"],
    "DILIGENCIAS DE JURISDICCIÓN VOLUNTARIA": ["diligencias","jurisdiccion voluntaria","jurisdicción voluntaria"],
    "DONACIÓN": ["donacion"],
    "DONACION DE DINERO": ["donacion de dinero","donación de dinero"],
    "EXTINCIÓN DE PATRIMONIO FAMILIAR CONCLUSIÓN": ["extincion patrimonio","extinción patrimonio familiar"],
    "FIDEICOMISO": ["fideicomiso"],
    "INVENTARIO Y AVALUO SUCESION": ["inventario y avaluo","inventario y avalúo","inventario avaluo sucesion"],
    "PERMUTA": ["permuta", "perm", "perm."],
    "PODER O MANDATO": ["poder","mandato","otorgamiento de poder"],
    "REVOCACIÓN DE PODER": ["revocacion de poder","revocar poder"],
    "TESTAMENTO": ["testamento"],
    "TRANSMISION DE PROPIEDAD": ["transmision de propiedad","transmisión de propiedad"],
    "TRANSMISIÓN DE PROPIEDAD Y EJECUCIÓN Y EXTINCIÓN PARCIAL DE FIDEICOMISO": [
        "transmision de propiedad fideicomiso","transmision propiedad y ejecucion fideicomiso",
        "transmisión de propiedad fideicomiso"
    ],

    # Protocolizaciones abreviado "Pr ..."
    "PROTOCOLIZACION CONDOMINIO O FRACCIONAMIENTO": [
        "pr condominio","pr fraccionamiento","pr fracc","pr cond","protoc condominio","protoc fraccionamiento"
    ],
    "PROTOCOLIZACION DE ACTA DE ASAMBLEA": ["pr acta de asamblea","protocolizacion acta asamblea","prot acta asamblea"],
    "PROTOCOLIZACION DE ADECUACION DE SUPERFICIE": ["pr adecuacion","pr adecuación","protocolizacion adecuacion superficie"],
    "PROTOCOLIZACION DE CESION DE DERECHOS": ["pr cesion de derechos","protocolizacion cesion de derechos"],
    "PROTOCOLIZACION DE CONTRATO EN GENERAL": ["pr contrato gral","protocolizacion contrato general","pr contrato general"],

    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICACION Y/O LOTIFICACION": [
        "pr oficio de fusion","pr subdivision","pr relotificacion","pr lotificacion",
        "protocolizacion oficio fusion","protocolizacion oficio subdivision","protocolizacion oficio relotificacion",
        "protocolizacion oficio lotificacion"
    ],
    "PROTOCOLIZACIÓN DE OFICIO DE FUSIÓN, SUBDIVISIÓN, RELOTIFICACION Y/O LOTIFICACION; CON DIVISION DE LA COSA COMUN": [
        "pr oficio de fusion comun","pr subdivision comun","pr relotificacion comun","pr lotificacion comun"
    ],
    "PROTOCOLIZACION DE SENTENCIA DE DIVORCIO": [
        "pr sentencia de divorcio","protocolizacion sentencia divorcio","prot sentencia divorcio"
    ],

    # Adeudos / redención
    "RECONOCIMIENTO DE ADEUDO (CONSTITUCION DE HIPOTECA)": [
        "reconomiento adeudo","reconocimiento adeudo","constitucion hipoteca","rcn adeudo"
    ],
    "REDENCIÓN PASIVOS CON MUTUO DE FOVISSSTE": [
        "redencion pasivos","redención pasivos fovissste","redencion fovis"
    ],
}

# ===========================================================
# 3) Utilidades
# ===========================================================
STOP = {
    "de","del","la","el","los","las","y","o","en","con","para","por","al",
    "a","se","su","sus","una","un","lo","uno","unos","unas",
    "escritura","esc","esc.","exp","proy","proyecto","carpeta","doc","docs"
}
DASH_SPLIT = re.compile(r"\s*[-–—]\s*")  # -, –, —

def _strip_acc(s: str) -> str:
    if not s:
        return ""
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _norm(s: str) -> str:
    s = _strip_acc((s or "").lower())
    s = s.replace("—","-").replace("–","-").replace("_"," ").replace("/", " / ")
    s = re.sub(r"[.,;:(){}\[\]]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _tokens(s: str) -> List[str]:
    s = _norm(s)
    ts = re.findall(r"[a-z0-9]+", s)
    return [t for t in ts if t not in STOP and t]

def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / float(len(a | b))

# Precálculo
TOKENS_CANON: Dict[str, set] = {acto: set(_tokens(acto)) for acto in ACTOS_CANONICOS}
ALIAS_MAP: Dict[str, str] = {}
for canon, alias_list in ALIAS_POR_ACTO.items():
    for alias in alias_list:
        ALIAS_MAP[_norm(alias)] = canon

# ===========================================================
# 4) Resolver
# ===========================================================
@dataclass
class ResolucionActo:
    acto_canonico: str
    actos_relacionados: List[str] = field(default_factory=list)
    cliente_principal: Optional[str] = None
    cliente_fuente: str = "carpeta"   # "carpeta" o "partes"
    raw_cliente_hint: Optional[str] = None
    match_score: float = 0.0
    escritura: Optional[int] = None   # NUEVO
    debug: Dict[str, str] = None

class ActoResolver:
    """
    - detect_acto(): nombre CANÓNICO del acto (+ escritura si aplica)
    - pick_cliente_principal(): empata 'cliente_hint' con 'partes'
    - resolve(): orquesta todo
    """

    # ---------- helpers de parsing ----------
    # def _split_por_guiones(self, folder_name: str) -> Tuple[str, Optional[str], Optional[str]]:
    #     """
    #     Divide en 3: [izquierda] - [cliente] - [resto ignorado]
    #     Acepta -, –, —. Si no hay guion, cliente y resto serán None.
    #     """
    #     parts = DASH_SPLIT.split(folder_name, maxsplit=2)
    #     left = parts[0].strip() if len(parts) >= 1 else folder_name
    #     print("Left: ", left)
    #     middle = parts[1].strip() if len(parts) >= 2 else None
    #     print("Middle: ",middle)
    #     right = parts[2].strip() if len(parts) >= 3 else None
    #     print("Right: ",right)
    #     return left, middle, right
    def _split_por_guiones(self, folder_name: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Divide el nombre por guiones REALES, ignorando los guiones del prefijo .-
        Ejemplos válidos de prefijo:
            Esc.- ...
            AFP.- ...
            123.- ...
        Resultado:
            left   -> prefijo + actos
            middle -> cliente principal
            right  -> lo que venga después (descripción)
        """
        s = folder_name.strip()

        # ============================================================
        # 1) Detectar prefijo con ".-" para NO partir en ese guion
        # ============================================================
        m = re.match(r"^\s*([A-Za-z0-9]+)\.\-\s*(.*)$", s)
        if m:
            prefijo = m.group(1)       # Ej: Esc, AFP, 123
            resto   = m.group(2)       # Ej: Compraventa, Donación - Juan - Descripción

            # ============================================================
            # 2) Partir el resto en MÁXIMO 2 guiones reales
            # ============================================================
            partes = re.split(r"\s*-\s*", resto)

            if len(partes) == 1:
                # Sólo actos, sin cliente
                left = f"{prefijo}.- {partes[0].strip()}"
                return left, None, None

            if len(partes) == 2:
                # left = prefijo + actos, middle = cliente, no hay right
                left   = f"{prefijo}.- {partes[0].strip()}"
                middle = partes[1].strip()
                return left, middle, None

            # len >= 3 → hay right
            left   = f"{prefijo}.- {partes[0].strip()}"
            middle = partes[1].strip()
            right  = "-".join(partes[2:]).strip()
            return left, middle, right

        # ============================================================
        # 3) SI NO HAY PREFIJO .-, entonces usar split normal en 3 partes
        # ============================================================
        partes = re.split(r"\s*-\s*", s)

        if len(partes) == 1:
            return partes[0].strip(), None, None

        if len(partes) == 2:
            return partes[0].strip(), partes[1].strip(), None

        left   = partes[0].strip()
        middle = partes[1].strip()
        right  = "-".join(partes[2:]).strip()
        return left, middle, right


    def _extraer_escritura_y_titulo(self, left: str):
        """
        Extrae el número de escritura (si existe) y limpia el título del nombre de carpeta.

        Ejemplos válidos:
            '123.- Adjudicacion'      -> (123, 'Adjudicacion')
            '04.- Compraventa'        -> (4, 'Compraventa')
            '30.- Carta permiso'      -> (30, 'Carta permiso')
            'Esc.- Adjudicacion'      -> (None, 'Adjudicacion')
            'ESC.- Compraventa'       -> (None, 'Compraventa')
            'Escritura.- Testamento'  -> (None, 'Testamento')
        """

        s = (left or "").strip()

        # Caso: número inicial (ej. 123.- Compraventa)
        m = re.match(r"^\s*(\d{1,10})\s*[\.\-]*\s*(.*\S)\s*$", s)
        if m:
            return int(m.group(1)), m.group(2).strip()

        # Caso: prefijos textuales tipo Esc, ESC, Escritura (ej. Esc.- Adjudicacion)
        # m = re.match(
        #     r"^\s*(?:esc(?:\.|ritura)?|escritura)\s*[\.\-]*\s*(.*\S)\s*$",
        #     s,
        #     flags=re.IGNORECASE
        # )
        m = re.match(
            r"""
            ^\s*
            (?:                                   # Prefijos válidos
                esc(?:\.|ritura)?                 # ESC, ESC., ESCRITURA
                | afp\.?                          # AFP o AFP.
                | \d+                             # números tipo 123
            )
            \s*[\.\-]*\s*                          # separadores: ".", "-", ".-", "--", etc.
            (.*\S)                                 # captura del nombre del acto
            $
            """,
            s,
            flags=re.IGNORECASE | re.VERBOSE
        )
        if m:
            return None, m.group(1).strip()

        return None, s

    def _limpiar_nombre_visual(self, s: str) -> str:
        s = _strip_acc(s)
        s = re.sub(r"[^a-zA-Z\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return " ".join(w.capitalize() for w in s.split())

    def _score_nombre(self, a: str, b: str) -> float:
        ta = set(_tokens(a))
        tb = set(_tokens(b))
        if not ta or not tb:
            return 0.0
        score = 5.0 * _jaccard(ta, tb) + 2.0 * len(ta & tb)
        a_first = next(iter(ta), "")
        if a_first and (a_first in tb):
            score += 2.0
        return score

    # ---------- detección de acto ----------
    def detect_acto(self, folder_name: str):
        """
        Detecta uno o varios actos canónicos.
        Regresa:
        acto_principal: str
        actos_relacionados: list[str]
        escritura: int|None
        dbg: dict
        """
        dbg = {}

        # Extraer left = actos (con prefijo si aplica)
        left, middle, right = self._split_por_guiones(folder_name)
        escritura, titulo_candidato = self._extraer_escritura_y_titulo(left)

        dbg["left"] = left
        dbg["titulo_candidato"] = titulo_candidato
        dbg["escritura"] = str(escritura) if escritura is not None else "None"

        # ======================================================
        # NUEVO: dividir múltiples actos por coma
        # ======================================================
        actos_raw = [a.strip() for a in titulo_candidato.split(",") if a.strip()]
        dbg["actos_raw"] = actos_raw

        actos_detectados = []

        for acto_raw in actos_raw:
            dbg_acto = {}
            cand_tokens = set(_tokens(acto_raw))
            titulo_norm = _norm(acto_raw)

            # ------------------------------
            # 1) Reglas fuertes
            # ------------------------------
            if "compraventa" in cand_tokens and "fovissste" in cand_tokens:
                actos_detectados.append(("COMPRAVENTA FOVISSSTE", dbg_acto))
                continue
            if "infonavit" in cand_tokens and (
                "compraventa" in cand_tokens or
                "compra" in cand_tokens or
                "venta" in cand_tokens or
                "cv" in cand_tokens
            ):
                actos_detectados.append(("COMPRAVENTA INFONAVIT", dbg_acto))
                continue
            if "carta" in cand_tokens and "permiso" in cand_tokens:
                actos_detectados.append(("AFP / CARTA PERMISO MENOR DE EDAD", dbg_acto))
                continue

            # ------------------------------
            # 2) Alias directos
            # ------------------------------
            alias_found = False
            for alias_norm, canon in ALIAS_MAP.items():
                if alias_norm in titulo_norm:
                    actos_detectados.append((canon, dbg_acto))
                    alias_found = True
                    break
            if alias_found:
                continue

            # ------------------------------
            # 3) Scoring tokens
            # ------------------------------
            best = None
            best_score = -1.0
            for canon, canon_toks in TOKENS_CANON.items():
                if not canon_toks:
                    continue
                overlap = len(canon_toks & cand_tokens)
                if overlap == 0:
                    continue
                score = (
                    3 * overlap +
                    5 * (1.0 if canon_toks.issubset(cand_tokens) else 0.0) +
                    4 * _jaccard(canon_toks, cand_tokens)
                )
                # boosts especiales
                if "infonavit" in cand_tokens and "infonavit" in canon_toks:
                    score += 3
                if "fovissste" in cand_tokens and "fovissste" in canon_toks:
                    score += 3

                if score > best_score:
                    best_score = score
                    best = canon

            if best:
                actos_detectados.append((best, dbg_acto))
                continue

            # ------------------------------
            # 4) fallback razonable
            # ------------------------------
            if "compraventa" in cand_tokens:
                actos_detectados.append(("COMPRAVENTA", dbg_acto))
            else:
                actos_detectados.append((acto_raw.upper(), dbg_acto))

        # ======================================================
        # ACTO PRINCIPAL + RELACIONADOS
        # ======================================================
        acto_principal = actos_detectados[0][0] if actos_detectados else titulo_candidato.upper()
        actos_relacionados = [a[0] for a in actos_detectados[1:]]

        dbg["actos_detectados"] = actos_detectados

        return acto_principal, actos_relacionados, escritura, dbg

    def normalizar_acto(self,acto_usuario: str):
        """
        Recibe un acto escrito por el usuario (ej: 'compra venta infonavit')
        y devuelve el nombre canónico real (ej: 'COMPRAVENTA INFONAVIT').

        Usa las mismas reglas que detect_acto(), pero aplicado a 1 solo acto.
        """
        dbg = {}
        acto_raw = acto_usuario.strip()
        dbg["input"] = acto_raw

        # Normalizaciones
        cand_tokens = set(_tokens(acto_raw))
        titulo_norm = _norm(acto_raw)
        dbg["tokens"] = cand_tokens
        dbg["titulo_norm"] = titulo_norm

        # ======================================================
        # 1) Reglas fuertes
        # ======================================================
        if "compraventa" in cand_tokens and "fovissste" in cand_tokens:
            return "COMPRAVENTA FOVISSSTE"

        if "infonavit" in cand_tokens and (
            "compraventa" in cand_tokens or
            "compra" in cand_tokens or
            "venta" in cand_tokens or
            "cv" in cand_tokens
        ):
            return "COMPRAVENTA INFONAVIT"

        if "carta" in cand_tokens and "permiso" in cand_tokens:
            return "AFP / CARTA PERMISO MENOR DE EDAD"

        # ======================================================
        # 2) Alias directos (ej: "cpv", "acto fe hechos", etc.)
        # ======================================================
        for alias_norm, canon in ALIAS_MAP.items():
            if alias_norm in titulo_norm:
                return canon

        # ======================================================
        # 3) Scoring con TOKENS_CANON
        # ======================================================
        best = None
        best_score = -1.0

        for canon, canon_toks in TOKENS_CANON.items():
            if not canon_toks:
                continue

            overlap = len(canon_toks & cand_tokens)
            if overlap == 0:
                continue

            score = (
                3 * overlap +
                5 * (1.0 if canon_toks.issubset(cand_tokens) else 0.0) +
                4 * _jaccard(canon_toks, cand_tokens)
            )

            # Boosts extra
            if "infonavit" in cand_tokens and "infonavit" in canon_toks:
                score += 3
            if "fovissste" in cand_tokens and "fovissste" in canon_toks:
                score += 3

            if score > best_score:
                best_score = score
                best = canon

        if best:
            return best

        # ======================================================
        # 4) Fallback razonable
        # ======================================================
        if "compraventa" in cand_tokens:
            return "COMPRAVENTA"

        # Último recurso: mayus del input
        return acto_raw.upper()


    # ---------- cliente principal ----------
    def _cliente_hint(self, folder_name: str) -> str:
        """
        Toma SOLO lo que esté entre el 1er y 2o guion; si no hay 2o guion, toma desde el 1o hasta el final.
        """
        left, middle, _ = self._split_por_guiones(folder_name)
        if middle:
            return self._limpiar_nombre_visual(middle)
        return ""

    def pick_cliente_principal(self, cliente_hint: str, partes: Optional[List[dict]]) -> Tuple[Optional[str], float, str]:
        if not cliente_hint:
            return None, 0.0, "carpeta"

        best_name, best_score = None, 0.0
        if partes:
            for p in partes:
                for key in ("nombre", "nombre_completo", "name", "full_name"):
                    if key in p and p[key]:
                        score = self._score_nombre(cliente_hint, p[key])
                        if score > best_score:
                            best_score = score
                            best_name = p[key]

        if best_name and best_score >= 3.0:
            return best_name, best_score, "partes"
        return cliente_hint, 1.0, "carpeta"

    # ---------- Orquestador ----------
    def resolve(self, folder_name: str, partes: Optional[List[dict]] = None) -> Dict[str, object]:
        acto, actos_relacionados, escritura, dbg = self.detect_acto(folder_name)
        hint = self._cliente_hint(folder_name)
        cliente, score, fuente = self.pick_cliente_principal(hint, partes)
        return asdict(ResolucionActo(
            acto_canonico=acto,
            actos_relacionados = actos_relacionados,
            cliente_principal=cliente,
            cliente_fuente=fuente,
            raw_cliente_hint=hint,
            match_score=score,
            escritura=escritura,
            debug=dbg
        ))
