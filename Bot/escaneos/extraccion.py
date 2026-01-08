#Imports independientes
import os, datetime
from typing import List, Tuple

#Impors mios
from Bot.helpers.archivos_urgentes import papeleria_importante
from Bot.constantes.regexes import *
from Bot.models.modelos import Inmueble, Persona, Sociedad, DocsOtros, Proyecto
from Bot.escaneos.escaneo import escanear_partes, escanear_varios_inmuebles, escanear_otros
from Bot.helpers.carpetas import buscar_acto_por_alias

class ExtraccionCarpeta:
    def __init__(self, path: str):
        self.ruta_proyecto = os.path.normpath(path)

    def extraccion_nombre_carpeta(self):
        campos = os.path.basename(self.ruta_proyecto).split("-")
        escritura = campos[0][:-1]
        actos = campos[1].strip().split(",")
        cliente_principal = campos[2].strip()
        descripcion = None
        if len(campos)>3:
            descripcion = campos[3].strip()
        
        return escritura, actos, cliente_principal, descripcion

    def extraccion_carpetas_documentos(self, actos: list) -> Tuple[List[Persona], List[Sociedad], List[Inmueble], DocsOtros]:
        inmuebles: List[Inmueble] = []
        pfs: List[Persona] = []
        pms: List[Sociedad] = []
        contenido = os.listdir(self.ruta_proyecto)
        for nombre in contenido:
            if nombre == "_cache_bot" or nombre == "LISTAS UIFS": continue#Ignorar la carpeta de cache

            archivo = os.path.join(self.ruta_proyecto, nombre)

            if nombre.lower() == "inmueble" or nombre.lower() == "inmuebles":#Escanear los inmuebles
                inmuebles = escanear_varios_inmuebles(archivo)
                continue

            if os.path.isdir(archivo):#Escanear clientes ya sean pfs o pms
                pfs_aux, pms_aux = escanear_partes(archivo, actos)
                pfs.extend(pfs_aux)
                pms.extend(pms_aux)
        otros = escanear_otros(self.ruta_proyecto)#Escanear otros documentos si es que hay
        return pfs, pms, inmuebles, otros

        
    def extraccion_de_datos(self) -> Proyecto:
        escritura, actos, cliente_principal, descripcion = self.extraccion_nombre_carpeta()
        ruta_proyecto = self.ruta_proyecto
        actos_involucrados = []

        for acto_en_carpeta in actos:
            acto_en_carpeta = acto_en_carpeta.strip().lower()
            actos_involucrados.append(buscar_acto_por_alias(acto_en_carpeta))
            # for acto_candidato, alias in ALIAS_POR_ACTO.items():
            #     if acto_en_carpeta in alias:
            #         actos_involucrados.append(acto_candidato)
            #         break
        acto_principal = actos_involucrados[0]
        fecha_generacion_proyecto = datetime.datetime.now().strftime("%Y/%m/%d")

        pfs, pms, inmuebles, otros = self.extraccion_carpetas_documentos(actos_involucrados)

        proyecto = Proyecto()
        proyecto.ruta = ruta_proyecto
        proyecto.fecha = fecha_generacion_proyecto 
        proyecto.escritura = escritura or "NO ENCONTRADO"
        
        proyecto.descripcion = descripcion or ""
        proyecto.acto_principal = acto_principal or "NO ENCONTRADO"
        proyecto.actos_involucrados = actos_involucrados or []
        proyecto.pfs = pfs
        proyecto.pms = pms
        proyecto.inmuebles = inmuebles
        proyecto.otros = otros

        #Para detectar el cliente principal
        split_nombre = cliente_principal.split(" ")
        coincidencias = {}
        for nombre in split_nombre:
            if pfs:
                for pf in pfs:
                    if pf.nombre not in coincidencias: coincidencias[pf.nombre] = 0
                    if nombre.lower() in pf.nombre.lower():
                        coincidencias[pf.nombre]+=1
            if pms:
                for pm in pms:
                    if pm.nombre not in coincidencias: coincidencias[pm.nombre] = 0
                    if nombre.lower() in pm.nombre.lower():
                        coincidencias[pm.nombre]+=1
        #Ver el mejor candidato para el nombre principal
        cliente_principal = max(coincidencias, key=coincidencias.get)
        
        #Estraer toda la papeleria que se necesita (IMPORTANTE) de los actos y los clientes involucrados
        proyecto.papeleria_total = papeleria_importante(proyecto)

        proyecto.cliente_principal = cliente_principal    
        return proyecto
