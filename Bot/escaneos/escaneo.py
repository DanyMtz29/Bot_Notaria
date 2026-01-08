import os

from Bot.models.modelos import Persona, Inmueble, Sociedad, DocsInmuebles, DocsOtros, DocsSociedad, DocsPersonaFisica
from Bot.helpers.carpetas import listar_directorios, ignorar_directorios, tiene_docs_sociedad, buscar_archivo_por_criterio, buscar_archivos_por_criterio
from Bot.constantes.hints import PM_NAME_HINTS, BANCOS_HINTS
from typing import List, Tuple
from Bot.constantes.regexes import *
from Bot.escaneos.csf import ProcesadorCSF
from Bot.constantes.actos import ROLES_POR_ACTO

def escanear_persona(ruta: str, rol: str, acto: str, carpeta_rol = None) -> Persona:
    p = Persona()
    p.nombre = os.path.basename(ruta).strip()
    p.nombre_s = "NO ENCONTRADO"
    p.primer_apellido = "NO ENCONTRADO"
    p.segundo_apellido = "NO ENCONTRADO"
    p.rfc = "XXXX000000ZZZ"
    p.idcif = "91234567891"
    p.acto_perteneciente = acto
    p.rol = rol
    p.unknown = False
    p.tipo = "PF"
    #Para buscar la papeleria en su respectiva carpeta
    if carpeta_rol:
        p.ruta_guardado = carpeta_rol+"|"+os.path.basename(ruta)
    else:
        p.ruta_guardado = os.path.basename(ruta)

    contenido = listar_directorios(ruta)
    for nombre in contenido:
        archivo = os.path.join(ruta, nombre)
        if os.path.isdir(archivo):
            p.conyugue = escanear_persona(archivo, rol, acto, p.ruta_guardado)
    docs = DocsPersonaFisica()
    docs.INE = buscar_archivo_por_criterio(ruta, INE_R)
    docs.ACTA_NAC = buscar_archivo_por_criterio(ruta, ACTA_NAC_R)
    docs.COMP_DOMICILIO = buscar_archivo_por_criterio(ruta, COMPROBANTE_DOMICILIO_R)
    docs.CURP = buscar_archivo_por_criterio(ruta, CURP_R)
    docs.ACTA_MATRIMONIO = buscar_archivo_por_criterio(ruta, ACTA_MATRIMONIO_R)
    docs.CSF = buscar_archivo_por_criterio(ruta, CSF_R)
    if docs.CSF:
        proc = ProcesadorCSF()
        nombre, rfc, idcif, nombre_s, primer_apellido, segundo_apellido = proc.extraer_datos(docs.CSF)
        if nombre: p.nombre = nombre
        if rfc: p.rfc = rfc
        if idcif: p.idcif = idcif
        if nombre_s: p.nombre_s = nombre_s
        if primer_apellido: p.primer_apellido = primer_apellido
        if segundo_apellido: p.segundo_apellido = segundo_apellido

    p.docs = docs

    return p

def escanear_sociedad(ruta: str, rol: str, acto: str, carpeta_rol = None) -> Sociedad:
    s = Sociedad()
    s.nombre = os.path.basename(ruta).strip()
    s.rfc = "XXXX000000ZZZ"
    s.idcif = "91234567891"
    s.representantes = []
    s.es_banco = False
    s.acto_perteneciente = acto
    s.unknown = False
    s.tipo = "PM"
    s.rol = rol
    
    #Para buscar su papeleria en su respectiva carpeta cuando se modifique
    if carpeta_rol:
        s.ruta_guardado = carpeta_rol+"|"+os.path.basename(ruta)
    else:
        s.ruta_guardado = os.path.basename(ruta)

    if any(h in s.nombre for h in BANCOS_HINTS):
        s.es_banco = True

    contenido = listar_directorios(ruta)
    representantes: List[Persona] = []
    for nombre in contenido:
        archivo = os.path.join(ruta, nombre)
        if os.path.isdir(archivo):#Representantes
            representantes.append(escanear_persona(archivo, rol, acto, s.ruta_guardado))
    s.representantes = representantes
    #Documentos de la sociedad
    docs = DocsSociedad()
    docs.ACTA_CONSTITUTIVA = buscar_archivo_por_criterio(ruta, ACTA_CONSTITUTIVA_R)
    docs.CSF_SOCIEDAD = buscar_archivo_por_criterio(ruta, CSF_R)
    docs.ASAMBLEAS = buscar_archivos_por_criterio(ruta, ASAMBLEA_R)
    docs.PODER_REPRESENTANTE = buscar_archivo_por_criterio(ruta, PODER_REPRESENTANTE_LEGAL_R)
    docs.CARTA_INSTRUCCION = buscar_archivo_por_criterio(ruta, CARTA_INSTRUCCION_R)

    if docs.CSF_SOCIEDAD:
        proc = ProcesadorCSF()
        nombre, rfc, idcif = proc.extraer_datos(docs.CSF_SOCIEDAD)
        if nombre: s.nombre = nombre
        if rfc: s.rfc = rfc
        if idcif: s.idcif = idcif

    s.docs = docs
    return s

def escanear_inmueble(ruta: str, carpeta_rol = None) -> Inmueble:
    i = Inmueble()
    i.nombre = os.path.basename(ruta).strip()
    docs = DocsInmuebles()
    docs.escritura_antecedente = buscar_archivo_por_criterio(ruta, ESCRITURA_ANTECEDENTE_R)
    docs.cert_lib_gravamen = buscar_archivo_por_criterio(ruta, CLG_R)
    docs.avaluo_catastral = buscar_archivo_por_criterio(ruta, AVALUO_CATASTRAL_R)
    docs.avaluo_comercial = buscar_archivo_por_criterio(ruta, AVALUO_COMERCIAL_R)
    docs.avaluo_referido = buscar_archivo_por_criterio(ruta, AVALUO_REFERIDO_R)
    docs.aviso_preventivo = buscar_archivo_por_criterio(ruta, AVISO_PREVENTIVO_R)
    docs.solicitud_avaluo = buscar_archivo_por_criterio(ruta, SOLICITUD_AVALUO_R)
    docs.plano = buscar_archivo_por_criterio(ruta, PLANO_R)
    docs.recibo_predial = buscar_archivo_por_criterio(ruta, PREDIAL_R)
    docs.titulo_propiedad = buscar_archivo_por_criterio(ruta, TITULO_PROPIEDAD_R)
    docs.no_adeudo_agua = buscar_archivo_por_criterio(ruta, NO_ADEUDO_AGUA_R)
    docs.lista_nominalvaluo_comercial = buscar_archivo_por_criterio(ruta, LISTA_NOMINAL_R)

    i.docs = docs
    if carpeta_rol:
        i.ruta_guardado = carpeta_rol+"|"+os.path.basename(ruta)
    else:
        i.ruta_guardado = os.path.basename(ruta)
    return i

def escanear_varios_inmuebles(ruta_carpeta: str) -> List[Inmueble]:
    lista_inmuebles: List[Inmueble] = []
    folder_superior = os.path.basename(ruta_carpeta)
    subdirs = listar_directorios(ruta_carpeta)
    if subdirs:#Varios inmuebles
        for d in subdirs:
            archivo = os.path.join(ruta_carpeta, d)
            lista_inmuebles.append(escanear_inmueble(archivo, folder_superior))
    else:#Solo un inmueble
        lista_inmuebles.append(escanear_inmueble(ruta_carpeta))
    return lista_inmuebles


def escanear_partes(ruta_carpeta: str, actos: list) -> Tuple[List[Persona], List[Sociedad]]:
    subdirs = [d for d in listar_directorios(ruta_carpeta) if not ignorar_directorios(d)]
    lista_personas_fisicas: List[Persona] = []
    lista_personas_morales: List[Sociedad] = []

    folder_superior = os.path.basename(ruta_carpeta)
    rol = os.path.basename(ruta_carpeta).strip().lower()
    acto_perteneciente = "DESCONOCIDO"
    for acto in actos:
        acto = acto.strip().upper()
        if rol in ROLES_POR_ACTO[acto]:
            acto_perteneciente = acto
            break
    # #Significa que hay mas de un cliente
    if subdirs:
        for d in subdirs:
            ruta_d = os.path.join(ruta_carpeta, d)
            d = d.lower()
            posible_sociedad = tiene_docs_sociedad(ruta_d) or any(h in d for h in PM_NAME_HINTS)
            if posible_sociedad:
                lista_personas_morales.append(escanear_sociedad(ruta_d, rol, acto_perteneciente, folder_superior))
            else:
                lista_personas_fisicas.append(escanear_persona(ruta_d, rol, acto_perteneciente, folder_superior))
    else:#Significa que solo hay 1 cliente
        nombre_carpeta = os.path.basename(ruta_carpeta).lower()
        posible_sociedad = tiene_docs_sociedad(ruta_carpeta) or any(h in nombre_carpeta for h in PM_NAME_HINTS)
        if posible_sociedad:
            lista_personas_morales.append(escanear_sociedad(ruta_carpeta, rol, acto_perteneciente))
        else:
            lista_personas_fisicas.append(escanear_persona(ruta_carpeta, rol, acto_perteneciente))

    return lista_personas_fisicas, lista_personas_morales

def escanear_otros(ruta: str) -> DocsOtros:
    docs = DocsOtros()
    docs.expediente_judicial = buscar_archivo_por_criterio(ruta, EXPEDIENTE_JUDICIAL_R)
    docs.constancia_pago = buscar_archivo_por_criterio(ruta, CONSTANCIA_PAGO_R)
    docs.forma_isai_amarilla = buscar_archivo_por_criterio(ruta, FORMA_ISAI_AMARILLA_R)
    docs.recibo_pago_isai = buscar_archivo_por_criterio(ruta, RECIBO_PAGO_ISAI_R)
    docs.recibo_pago_derechos_registro = buscar_archivo_por_criterio(ruta, RECIBO_PAGO_DERECHOS_REGISTRO_R)
    docs.escritura_antecedente_credito = buscar_archivo_por_criterio(ruta, ESCRITURA_ANTECEDENTE_CREDITO_R)
    docs.acta_nacimiento_conyuge = buscar_archivo_por_criterio(ruta, ACTA_NACIMIENTO_CONYUGE_R)
    docs.identificacion_conyuge = buscar_archivo_por_criterio(ruta, IDENTIFICACION_CONYUGE_R)
    docs.lista_nominal = buscar_archivo_por_criterio(ruta, LISTA_NOMINAL_R)
    docs.comprobante_domicilio_conyuge = buscar_archivo_por_criterio(ruta, COMPROBANTE_DOMICILIO_CONYUGE_R)
    docs.curp_conyuge = buscar_archivo_por_criterio(ruta, CURP_CONYUGE_R)
    #=========================Documentos por si no se colocan en una parte===============
    docs.carta_instruccion = buscar_archivo_por_criterio(ruta, CARTA_INSTRUCCION_R)
    docs.poder_representante = buscar_archivo_por_criterio(ruta, PODER_REPRESENTANTE_LEGAL_R)
    docs.titulo_propiedad = buscar_archivo_por_criterio(ruta, TITULO_PROPIEDAD_R)
    docs.no_adeudo_agua = buscar_archivo_por_criterio(ruta, NO_ADEUDO_AGUA_R)
    docs.plano = buscar_archivo_por_criterio(ruta, PLANO_R)
    #====================================================================================
    docs.otros = []

    docs.otros = [os.path.join(ruta,f) for f in os.listdir(ruta) if (os.path.isfile(os.path.join(ruta, f)) and f.startswith("_")) ]
            
    return docs