#Import independientes
import os, re, json
from typing import List, Optional

#Imports mios
from Bot.constantes.regexes import *
from Bot.constantes.papeleria import *
from Bot.models.modelos import Proyecto
from Bot.constantes.actos import REGEX_POR_ACTO

IGNORED_DIRS = {"Generados_Bot", "_cache_bot", "Listas Uifs"}
IGNORED_PREFIXES = ("SubActo", "Subacto", "subacto", "Generados_", "~$")
DOC_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}

def listar_directorios(path: str) -> List[str]:
    try:
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except Exception:
        return []

def ignorar_directorios(name: str) -> bool:
    if name in IGNORED_DIRS:
        return True
    return any(name.startswith(p) for p in IGNORED_PREFIXES)

def buscar_archivo_por_criterio(ruta_carpeta: str, regexes: List[re.Pattern]) -> Optional[str]:
    archivos = os.listdir(ruta_carpeta)
    for nombre in archivos:
        ruta_completa = os.path.join(ruta_carpeta, nombre)
        if os.path.isfile(ruta_completa):
            for patron in regexes:
                if patron.search(nombre):
                    return os.path.normpath(ruta_completa)
    return None

def buscar_archivos_por_criterio(ruta_carpeta: str, regexes: List[re.Pattern]) -> Optional[str]:
    archivos_encontrados = []
    archivos = os.listdir(ruta_carpeta)
    for nombre in archivos:
        ruta_completa = os.path.join(ruta_carpeta, nombre)
        if os.path.isfile(ruta_completa):
            for patron in regexes:
                if patron.search(nombre):
                    archivos_encontrados.append(os.path.normpath(ruta_completa))
                    break
    return archivos_encontrados

def buscar_archivos_faltantes_pf(ruta_carpeta: str, doc: str) -> Optional[str]:
    if doc == ACTA_NAC:
        return buscar_archivo_por_criterio(ruta_carpeta, ACTA_NAC_R)
    elif doc == CURP:
        return buscar_archivo_por_criterio(ruta_carpeta, CURP_R)
    elif doc == INE:
        return buscar_archivo_por_criterio(ruta_carpeta, INE_R)
    elif doc == CSF:
        return buscar_archivo_por_criterio(ruta_carpeta, CSF_R)
    elif doc == COMPROBANTE_DOMICILIO:
        return buscar_archivo_por_criterio(ruta_carpeta, COMPROBANTE_DOMICILIO_R)
    elif doc == ACTA_MAT:
        return buscar_archivo_por_criterio(ruta_carpeta, ACTA_MATRIMONIO_R)
    else: return None
    
def buscar_archivos_faltantes_pm(ruta_carpeta: str, doc: str) -> Optional[str]:
    if doc == CSF_SOCIEDAD:
        return buscar_archivo_por_criterio(ruta_carpeta, CSF_R)
    elif doc == ACTA_CONSTITUTIVA:
        return buscar_archivo_por_criterio(ruta_carpeta, ACTA_CONSTITUTIVA_R)
    elif doc == PODER_REPRESENTANTE:
        return buscar_archivo_por_criterio(ruta_carpeta, PODER_REPRESENTANTE_LEGAL_R)
    elif doc == CARTA_INSTRUCCION:
        return buscar_archivo_por_criterio(ruta_carpeta, CARTA_INSTRUCCION_R)
    else: return None

def buscar_archivos_faltantes_inmueble(ruta_carpeta: str, doc: str) -> Optional[str]:
    if doc == ESCRITURA_ANTECEDENTE:
        return buscar_archivo_por_criterio(ruta_carpeta, ESCRITURA_ANTECEDENTE_R)
    elif doc == CLG:
        return buscar_archivo_por_criterio(ruta_carpeta, CLG_R)
    elif doc == AVALUO_CATASTRAL:
        return buscar_archivo_por_criterio(ruta_carpeta, AVALUO_CATASTRAL_R)
    elif doc == AVALUO_REFERIDO:
        return buscar_archivo_por_criterio(ruta_carpeta, AVALUO_REFERIDO_R)
    elif doc == AVALUO_COMERCIAL:
        return buscar_archivo_por_criterio(ruta_carpeta, AVALUO_COMERCIAL_R)
    elif doc == AVISO_PREVENTIVO:
        return buscar_archivo_por_criterio(ruta_carpeta, AVISO_PREVENTIVO_R)
    elif doc == SOLICITUD_AVALUO:
        return buscar_archivo_por_criterio(ruta_carpeta, SOLICITUD_AVALUO_R)
    elif doc == PLANO:
        return buscar_archivo_por_criterio(ruta_carpeta, PLANO_R)
    elif doc == PAGO_PREDIAL:
        return buscar_archivo_por_criterio(ruta_carpeta, PREDIAL_R)
    elif doc == TITULO_PROPIEDAD:
        return buscar_archivo_por_criterio(ruta_carpeta, TITULO_PROPIEDAD_R)
    elif doc == NO_ADEUDO_AGUA:
        return buscar_archivo_por_criterio(ruta_carpeta, NO_ADEUDO_AGUA_R)
    elif doc == LISTA_NOMINAL:
        return buscar_archivo_por_criterio(ruta_carpeta, LISTA_NOMINAL_R)
    else: return None

def tiene_docs_sociedad(ruta: str):
    return any([
        buscar_archivo_por_criterio(ruta, ACTA_CONSTITUTIVA_R),
        buscar_archivo_por_criterio(ruta, PODER_REPRESENTANTE_LEGAL_R),
        len(buscar_archivos_por_criterio(ruta, ASAMBLEA_R)) > 0
    ])

def obtener_clientes_totales(proyecto: Proyecto) -> list:
    clientes = []
    pfs = proyecto.pfs
    pms = proyecto.pms
    for pf in pfs:
        clientes.append(pf)
        conyu = pf.conyugue
        if conyu: clientes.append(conyu)

    for pm in pms:
        clientes.append(pm)
        reps = pm.representantes
        if reps:
            for r in reps:
                clientes.append(r)
    return clientes

def obtener_solo_clientes_pfs(proyecto: Proyecto) -> List:
    clientes = []
    pfs = proyecto.pfs
    pms = proyecto.pms
    for pf in pfs:
        clientes.append(pf)
        conyu = pf.conyugue
        if conyu: clientes.append(conyu)

    for pm in pms:
        reps = pm.representantes
        if reps:
            for r in reps:
                clientes.append(r)
    return clientes

def buscar_acto_por_alias(nombre_acto: str) -> Optional[str]:
    for acto_candidato, regex_acto in REGEX_POR_ACTO.items():
        for patron in regex_acto:
            if patron.search(nombre_acto):
                return acto_candidato
    return None