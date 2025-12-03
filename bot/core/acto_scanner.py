"""
    |Fecha      Responsble Linea     Descripcion                                     |
    |29/11/2025  Daniel    309       Se comento la linea debido a que escaneaba dos  |
    |                                veces las CSF                                   |
    |29/11/2025  Daniel    229,226   Se comento la linea 226 y se quito la variable  |
    |                                rep_inside dentro del if de la linea 229        |
    |29/11/2025  Daniel    219       Se comento el metodo anterior de solo añadir un |
    |                                solo rep, ahora añade varios a la sociedad      |
    |29/11/2025  Daniel    342       Se comento el metodo anterior de solo buscar la |
    |                                CSF de un rep, ahora busca de todos los reps.   |

"""
from __future__ import annotations
import os, re
from typing import List, Dict, Optional, Tuple
from loguru import logger

from bot.core.files import ActosFinder
from bot.core.acto_detector import ActoResolver
from bot.models.acto_models import (
    ActoExtraction, Persona, PersonaFisica, Sociedad, Inmueble, DocumentoPaths
)

from bot.core import csf as csf_parser

IGNORED_DIRS = {
    "__pycache__", ".git", ".svn", ".idea", ".vscode",
    "SubActo", "SubActos", "Generados_Bot", "_cache_bot",
}
IGNORED_PREFIXES = ("SubActo", "Subacto", "subacto", "Generados_", "~$")

bancos_keywords = [
    "bbva", "banorte", "santander", "hsbc",
    "scotiabank", "banregio", "citibanamex",
    "infonavit", "fovissste", "sofom", "sofol",
    "banco"
]

def _is_ignored_dir(name: str) -> bool:
    if name in IGNORED_DIRS:
        return True
    return any(name.startswith(p) for p in IGNORED_PREFIXES)

def _list_dirs(path: str) -> List[str]:
    try:
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except Exception as e:
        logger.exception("Error listando carpetas en {}: {}", path, e)
        return []

def _list_files(path: str) -> List[str]:
    try:
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    except Exception as e:
        logger.exception("Error listando archivos en {}: {}", path, e)
        return []

def _first_or_none(*vals):
    for v in vals:
        if v:
            return v
    return None

KNOWN_ROLES = {
    "comprador","compareciente", "vendedor", "apoderado", "acreedor",
    "banco", "acreditado", "deudor", "donante", "donatario",
    "fideicomisario", "fideicomitente", "fiduciario",
    "mutante", "mutuario", "poderdante", "apoderado",
    "adquiriente", "enajenante", "testador", "testigo",
    "acreditante", "delegado fiduciario", "depositario",
    "socios", "accionistas", "administrador", "comisario",
    "presidente", "secretario", "tesorero", "vocales",
    "comprador/acreditado", "vendedor terreno", "vendedor construccion",
    "hij@", "madre", "padre"
}

ACTO_ROLE_MAP: Dict[str, set] = {
    "compraventa": {"comprador", "vendedor", "apoderado", "acreedor", "aanco", "acreditado"},
    "compraventa fovissste": {"comprador", "vendedor", "acreditado", "acreedor", "aanco", "apoderado"},
    "protocolizacion": {"acreedor", "deudor", "apoderado", "banco"},
    "afp": {"apoderado", "poderdante", "testigo"},
}

def _detect_acto_type(acto_nombre: str) -> Tuple[str, set]:
    name = (acto_nombre or "").lower()
    def has(*tokens): return all(t in name for t in tokens)
    if has("compraventa", "fovissste"):
        return "compraventa fovissste", ACTO_ROLE_MAP["compraventa fovissste"]
    if "compraventa" in name:
        return "compraventa", ACTO_ROLE_MAP["compraventa"]
    if "protocoliz" in name:
        return "protocolizacion", ACTO_ROLE_MAP["protocolizacion"]
    if name.strip().startswith("afp") or "acta de fe" in name or "fe de hechos" in name:
        return "afp", ACTO_ROLE_MAP["afp"]
    return "desconocido", KNOWN_ROLES

INMUEBLE_DIR_NAMES = {"inmueble", "inmuebles"}
SPOUSE_DIR_NAMES = {"esposa", "esposo", "conyuge", "cónyugue"}
REPRESENTANTE_DIR_NAMES = {"representante", "representante legal"}
PM_NAME_HINTS = {
    "s.a.", "s de rl", "s. de r.l", "sapi", "sab", "s.a.b",
    "sa de cv", "s.a. de c.v", "sc", "sociedad", "desarrolladora", "constructora",
    "inmobiliaria", "industria", "comercial", "comercializadora", "servicios",
}

TOP_OTHERS_PATTERNS = {
    "Expediente judicial": [r"expediente\s*jud", r"exp\s*jud"],
    "Constancia de pago": [r"constancia\s*pago", r"constancia de pago"],
    "Forma ISAI Amarilla (Registro Publico)": [r"isai.*amarilla", r"forma\s*amarilla", r"forma\s*isai"],
    "Recibo de pago ISAI": [r"pago\s*isai", r"recibo\s*isai"],
    "Recibo de pago Derechos de Registro": [r"pago.*registro", r"recibo.*derechos.*registro"],
    "Escritura Antecedente de la apertura del crédito, convenios o constitución del fideicomiso": [r"escritura\s*ant",r"escritura.*(credito|fidei|convenios)",r"ant\s*(credito|fidei)",r"fideicomiso\s*const"],
    "Acta de nacimiento del conyuge": [r"acta.*nacimiento.*(cony|c[oó]nyu)"],
    "Identificación oficial del conyuge": [r"(ine|ife|identificacion).*(cony|c[oó]nyu)"],
    "Lista nominal": [r"lista.*nominal"],
    "Comprobante de Domicilio del conyuge": [r"(comp.*dom)|(recibo.*(cfe|agua|luz)).*(cony|c[oó]nyu)"],
    "CURP del conyuge": [r"curp.*(cony|c[oó]nyu)"],
}

def _match_top_other(name: str):
    n = name.lower()

    # Regla 1: empieza con "_"
    if name.startswith("_"):
        return "Otros"

    # Regla 2: patrones exactos
    for key, pats in TOP_OTHERS_PATTERNS.items():
        for pat in pats:
            if re.search(pat, n):
                return key

    # Regla 3: similitud por tokens (mínimo 50%)
    def tokens(s): 
        return set(re.split(r"[^a-z0-9]+", s.lower()))

    nt = tokens(n)
    for key in TOP_OTHERS_PATTERNS:
        kt = tokens(key)
        if len(nt & kt) / max(1, len(kt)) >= 0.5:
            return key

    return None

def _looks_like_pm_folder_name(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in PM_NAME_HINTS)

# ---------------- PF ----------------
def _scan_persona_fisica(person_dir: str) -> Persona:
    p = Persona()

    csf_path = ActosFinder.find_csf_in_folder(person_dir)
    if csf_path:
        p.docs.CSF = csf_path
        try:
            rfc, idcif, nombre = csf_parser.extract_csf_fields(csf_path)
        except Exception as e:
            logger.warning("No se pudo parsear CSF PF {}: {}", csf_path, e)
            rfc = idcif = nombre = None
        # **IMPORTANTE**: el nombre de CSF manda SIEMPRE
        p.nombre = nombre or p.nombre
        p.rfc = _first_or_none(p.rfc, rfc)
        p.idcif = _first_or_none(p.idcif, idcif)

    # Otros básicos
    p.docs.CURP = ActosFinder.find_curp(person_dir)
    p.docs.ACTA_NAC = ActosFinder.find_acta_nacimiento(person_dir)
    p.docs.INE = ActosFinder.find_ine(person_dir)
    p.docs.COMP_DOMICILIO = ActosFinder.find_comprobante_domicilio(person_dir)
    p.docs.ACTA_MATRIMONIO = ActosFinder.find_acta_matrimonio(person_dir)

    # Fallback final si **no** hubo nombre en CSF
    if not p.nombre:
        p.nombre = os.path.basename(person_dir)

    return p

def _find_spouse_dir_inside_person(person_dir: str) -> Optional[str]:
    for d in _list_dirs(person_dir):
        if d in SPOUSE_DIR_NAMES and not _is_ignored_dir(d):
            return os.path.join(person_dir, d)
    return None

def _build_pf_from_person_folder(person_dir: str, role_name: str) -> PersonaFisica:
    pf = PersonaFisica(rol=role_name, persona=_scan_persona_fisica(person_dir))
    if pf.persona.docs.ACTA_MATRIMONIO:
        spouse_dir = _find_spouse_dir_inside_person(person_dir)
        if spouse_dir:
            pf.esposa_o_esposo = _scan_persona_fisica(spouse_dir)
    return pf

# ---------------- PM ----------------
def _scan_sociedad(soc_dir: str, rol: str) -> Sociedad:
    s = Sociedad(rol=rol, nombre=os.path.basename(soc_dir))
    d = DocumentoPaths()

    d.CSF_SOCIEDAD = ActosFinder.find_csf_in_folder(soc_dir)
    d.ACTA_CONSTITUTIVA = ActosFinder.find_acta_constitutiva(soc_dir)
    d.PODER_REPRESENTANTE = ActosFinder.find_poder_representante(soc_dir)
    d.ASAMBLEAS = ActosFinder.find_asambleas(soc_dir)
    d.OTROS = ActosFinder.find_otros_sociedad(soc_dir)
    s.docs = d

    #NUEVO PARA VER SI ES UN BACNO===============================
    nombre_lower = s.nombre.lower() if s.nombre else ""

    if any(k in nombre_lower for k in bancos_keywords):
        s.es_banco = True
        s.carta_instruccion = ActosFinder.find_carta_instruccion(soc_dir)
    #AQUI TERMINA LO DE PARA VER SI ES BANCO=================================

    # Nombre completo + RFC/idCIF **desde CSF de la sociedad**
    if d.CSF_SOCIEDAD:
        try:
            rfc_soc, idcif_soc, nombre_soc = csf_parser.extract_csf_fields(d.CSF_SOCIEDAD)
            s.nombre = nombre_soc or s.nombre
            s.rfc = rfc_soc or s.rfc
            s.idcif = idcif_soc or s.idcif
        except Exception as e:
            logger.warning("No se pudo parsear CSF PM {}: {}", d.CSF_SOCIEDAD, e)

    # # Representante PF (con su propio nombre desde su CSF)
    # rep_folder = ActosFinder.find_representante_folder(soc_dir)
    # if rep_folder:
    #     s.representante = _scan_persona_fisica(rep_folder)

    rep_folders = ActosFinder.find_representantes_folders(soc_dir)
    s.representantes = []

    for rep_dir in rep_folders:
        rep = _scan_persona_fisica(rep_dir)
        s.representantes.append(rep)

    return s

# ---------------- INMUEBLE(S) ----------------
def _scan_inmueble_dir(inm_dir: str, name: Optional[str] = None) -> Inmueble:
    nm = name or os.path.basename(inm_dir)
    docs = {
        "ESCRITURA_ANTECEDENTE": ActosFinder.find_escritura_antecedente(inm_dir),
        "CERT_LIB_GRAVAMEN": ActosFinder.find_cert_libertad_gravamen(inm_dir),
        "AVALUO_CATASTRAL": ActosFinder.find_avaluo_catastral(inm_dir),
        "AVALUO_COMERCIAL": ActosFinder.find_avaluo_comercial(inm_dir),
        "AVALUO_REFERIDO": ActosFinder.find_avaluo_referido(inm_dir),
        "AVISO_PREVENTIVO": ActosFinder.find_aviso_preventivo(inm_dir),
        "SOLICITUD_AVALUO": ActosFinder.find_solicitud_avaluo(inm_dir),
        "PLANO": ActosFinder.find_plano(inm_dir),
        "RECIBO_PREDIAL": ActosFinder.find_recibo_predial(inm_dir),
        "TITULO_PROPIEDAD": ActosFinder.find_titulo_propiedad(inm_dir),
        "NO_ADEUDO_AGUA": ActosFinder.find_no_adeudo_agua(inm_dir),
        "LISTA_NOMINAL": ActosFinder.find_lista_nominal(inm_dir),
    }
    docs_otros = ActosFinder.find_otros_inmueble(inm_dir)
    if docs_otros:
        docs["OTROS"] = docs_otros
    return Inmueble(nombre=nm, docs=docs)

def _scan_inmuebles(acto_dir: str, inm_dir_name: str) -> List[Inmueble]:
    inm_path = os.path.join(acto_dir, inm_dir_name)
    subs = [d for d in _list_dirs(inm_path) if not _is_ignored_dir(d)]
    if subs:
        return [_scan_inmueble_dir(os.path.join(inm_path, d), name=d) for d in subs]
    else:
        return [_scan_inmueble_dir(inm_path, name=inm_dir_name)]

# ---------------- routing de rol (PF/PM por subcarpeta) ----------------
def _scan_role_dir(role_dir: str, role_name: str) -> Tuple[List[PersonaFisica], List[Sociedad]]:
    pf_list: List[PersonaFisica] = []
    pm_list: List[Sociedad] = []

    subdirs = [d for d in _list_dirs(role_dir) if not _is_ignored_dir(d)]

    if subdirs:
        for d in subdirs:
            full = os.path.join(role_dir, d)
            #rep_inside = ActosFinder.find_representante_folder(full) is not None
            has_pm_docs = ActosFinder.has_sociedad_docs(full)
            name_looks_pm = _looks_like_pm_folder_name(d)
            if has_pm_docs or name_looks_pm:
                pm_list.append(_scan_sociedad(full, rol=role_name))
            else:
                pf_list.append(_build_pf_from_person_folder(full, role_name))
        return pf_list, pm_list
    
    # fallback si no hay subcarpetas
    #rep_inside = ActosFinder.find_representante_folder(role_dir) is not None
    has_pm_docs = ActosFinder.has_sociedad_docs(role_dir)
    if has_pm_docs or _looks_like_pm_folder_name(os.path.basename(role_dir)):
        pm_list.append(_scan_sociedad(role_dir, rol=role_name))
    else:
        pf_list.append(_build_pf_from_person_folder(role_dir, role_name))

    return pf_list, pm_list

# ---------------- forzado de NOMBRES desde CSF (PF y PM) ----------------
def _force_names_from_csf(extraction: ActoExtraction) -> None:
    """
    Recorre todas las partes y, si hay CSF, vuelve a parsear y **sobrescribe** el nombre
    (y RFC/idCIF donde aplique) para evitar que se quede el acrónimo de carpeta.
    """
    # PF
    for pf in extraction.partes_pf:
        csf = pf.persona.docs.CSF
        if csf:
            try:
                rfc, idcif, nombre = csf_parser.extract_csf_fields(csf)
                if nombre:
                    pf.persona.nombre = nombre  # FORZAR nombre completo
                if rfc:
                    pf.persona.rfc = rfc
                if idcif:
                    pf.persona.idcif = idcif
            except Exception as e:
                logger.warning("ForceName PF error con {}: {}", csf, e)

        # Cónyuge si existe
        if pf.esposa_o_esposo and pf.esposa_o_esposo.docs.CSF:
            try:
                rfc, idcif, nombre = csf_parser.extract_csf_fields(pf.esposa_o_esposo.docs.CSF)
                if nombre:
                    pf.esposa_o_esposo.nombre = nombre
                if rfc:
                    pf.esposa_o_esposo.rfc = rfc
                if idcif:
                    pf.esposa_o_esposo.idcif = idcif
            except Exception as e:
                logger.warning("ForceName Conyuge error con {}: {}", pf.esposa_o_esposo.docs.CSF, e)

    # PM
    for pm in extraction.partes_pm:
        csf_soc = pm.docs.CSF_SOCIEDAD
        if csf_soc:
            try:
                rfc, idcif, nombre = csf_parser.extract_csf_fields(csf_soc)
                if nombre:
                    pm.nombre = nombre  # razón social completa
                if rfc:
                    pm.rfc = rfc
                if idcif:
                    pm.idcif = idcif
            except Exception as e:
                logger.warning("ForceName PM error con {}: {}", csf_soc, e)

        for rep in pm.representantes:
            if rep.docs.CSF:
                try:
                    rfc, idcif, nombre = csf_parser.extract_csf_fields(rep.docs.CSF)
                    if nombre: rep.nombre = nombre
                    if rfc: rep.rfc = rfc
                    if idcif: rep.idcif = idcif
                except Exception as e:
                    logger.warning("ForceName Representante error con {}: {}", pm.representante.docs.CSF, e)

# ---------------- MAIN ----------------
def scan_acto_folder(acto_dir: str, acto_nombre: Optional[str] = None) -> ActoExtraction:
    """
    Escanea una carpeta de acto y devuelve ActoExtraction con:
      - acto_nombre (canónico)
      - cliente_principal (match PARTES o fallback carpeta entre 1er y 2o guion)
      - escritura (int si la carpeta empieza con número, sino None)
    """
    carpeta = acto_nombre or os.path.basename(acto_dir)

    # Routing por roles (tu lógica existente)
    acto_type, allowed_roles = _detect_acto_type(carpeta)
    logger.debug("Tipo de acto (routing): {} (roles permitidos: {})", acto_type, ", ".join(sorted(allowed_roles)))

    out = ActoExtraction(acto_nombre=carpeta)

    # Top-level
    top_dirs = [d for d in _list_dirs(acto_dir) if not _is_ignored_dir(d)]
    top_files = _list_files(acto_dir)

    # Partes PF/PM
    for d in top_dirs:
        d = d.lower()
        if d in INMUEBLE_DIR_NAMES:
            continue
        if d not in KNOWN_ROLES or d not in allowed_roles:
            continue
        full = os.path.join(acto_dir, d)
        pf_found, pm_found = _scan_role_dir(full, d)
        out.partes_pf.extend(pf_found)
        out.partes_pm.extend(pm_found)

    # Inmuebles
    for c in INMUEBLE_DIR_NAMES:
        if c in top_dirs:
            out.inmuebles.extend(_scan_inmuebles(acto_dir, c))
            break

    # Otros
    #out.otros = sorted(os.path.join(acto_dir, f) for f in top_files)
    # --- NUEVA CLASIFICACIÓN DE OTROS ---
    otros_dict = {}

    for f in top_files:
        category = _match_top_other(f)
        if not category:
            continue  # ignorar archivo

        full = os.path.join(acto_dir, f)
        otros_dict.setdefault(category, []).append(full)

    out.otros = otros_dict

    # Normaliza nombres desde CSF
    #_force_names_from_csf(out) ========================================================

    # Prepara partes planas para el matcher
    partes_para_match = []

    for pf in out.partes_pf:
        if pf.persona and pf.persona.nombre:
            partes_para_match.append({"rol": pf.rol, "nombre": pf.persona.nombre})
        if pf.esposa_o_esposo and pf.esposa_o_esposo.nombre:
            partes_para_match.append({"rol": "CONYUGE", "nombre": pf.esposa_o_esposo.nombre})

    for pm in out.partes_pm:
        if pm.nombre:
            partes_para_match.append({"rol": pm.rol, "nombre": pm.nombre})
        for rep in pm.representantes:
            if rep.nombre:
                partes_para_match.append({"rol": "REPRESENTANTE", "nombre": rep.nombre})    
        # if pm.representante and pm.representante.nombre:
        #     partes_para_match.append({"rol": "REPRESENTANTE", "nombre": pm.representante.nombre})

    # Resolver acto canónico + cliente + escritura (soporta -, –, — y 2do guion)
    resolver = ActoResolver()
    det = resolver.resolve(folder_name=carpeta, partes=partes_para_match)

    out.acto_nombre       = det.get("acto_canonico") or carpeta
    out.cliente_principal = det.get("cliente_principal")
    out.cliente_fuente    = det.get("cliente_fuente")
    out.escritura         = det.get("escritura")
    out.actos_relacionados = det.get("actos_relacionados")

    logger.debug("Acto canónico: {}", out.acto_nombre)
    logger.debug("Cliente principal: {} (fuente: {})", out.cliente_principal, out.cliente_fuente)
    logger.debug("Escritura: {}", out.escritura)

    return out
