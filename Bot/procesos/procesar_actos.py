#imports independientes
from __future__ import annotations
import os, datetime, shutil, time

#Imports de selenium
from Bot.ui_selenium.pages.procesar_clientes import Cliente
from Bot.ui_selenium.pages.tap_partes import partesTap
from Bot.ui_selenium.pages.tap_general import generalTap
from Bot.ui_selenium.pages.projects_documents import ProjectsDocumentsPage
from Bot.ui_selenium.pages.docs_modify import tapModify
from Bot.ui_selenium.pages.Escrituras import Escritura

#imports mios
from Bot.helpers.logs import tomar_screenshot, registrar_log
from Bot.config.rutas import RUTA_LOGS, RUTA_TEMPORALES, ARCHIVO_FALTANTES
from Bot.models.modelos import Proyecto, ProyectoMod
from Bot.escaneos.extraccion import ExtraccionCarpeta
from Bot.helpers.carpetas import obtener_clientes_totales
from Bot.procesos.procesar_papeleria import Documentos
from Bot.helpers.json import obtener_faltantes, guardar_json, checar_fecha_valida

def procesar_actos(driver, wait, abogado: str, ruta_proyectos_abogado: str,ruta_bitacora: str, carpeta_afps=False):
    #it = 0#===========================pendiente por quitar
    for acto in os.listdir(ruta_proyectos_abogado):
        #Si no esta en carpeta de afps entonces busca la carpeta de afps
        ruta_acto = os.path.join(ruta_proyectos_abogado, acto)
        if not carpeta_afps and 'AFP' in acto:
            procesar_actos(driver,wait, abogado, os.path.join(ruta_proyectos_abogado, acto),ruta_bitacora, True)
            continue

        if not os.path.isdir(ruta_acto):# Ignorar archivos sueltos que no sean carpetas de acto
            continue

        cache_dir = os.path.join(ruta_acto, "_cache_bot")#Donde se guarda la papeleria faltante
        json_dir = os.path.join(cache_dir, ARCHIVO_FALTANTES)#Para guardar papeleria faltante

        print(f"Procesando {acto}")
        carpeta_logs_acto = os.path.join(RUTA_LOGS, str(datetime.date.today()), abogado, acto)
        os.makedirs(carpeta_logs_acto, exist_ok=True)
        attempts = 3
        if not os.path.exists(json_dir):#Si no hay papeleria faltante
            while attempts > 0:
                try:
                    print("CREANDO PROYECTO")
                    extraer_datos_proyecto(driver, wait, ruta_acto, abogado, carpeta_logs_acto)
                    registrar_log(carpeta_logs_acto, f"Proyecto '{acto}' creado correctamente")
                    shutil.rmtree(RUTA_TEMPORALES, ignore_errors=True)#Borra la carpeta con listas uifs
                    os.makedirs(RUTA_TEMPORALES, exist_ok=True)#VOLVER A CREAR LA CARPETA
                    break
                except Exception as e:
                    attempts-=1
                    ruta_img = tomar_screenshot(driver, carpeta_logs_acto, "Error al intentar crear el proyecto")
                    registrar_log(carpeta_logs_acto,f"No se pudo crear el proyecto '{acto}'. Error: {e}, Screenshot: {ruta_img}")
                    shutil.rmtree(RUTA_TEMPORALES, ignore_errors=True)#Borra la carpeta con listas uifs
                    os.makedirs(RUTA_TEMPORALES, exist_ok=True)#VOLVER A CREAR LA CARPETA
                    print(f"Reintentando {attempts}")
                    time.sleep(5)
        else:
            while attempts > 0:
                try:
                    state = modificar_proyecto(driver, wait, ruta_acto, carpeta_logs_acto, ruta_bitacora)
                    if state == 2 :registrar_log(carpeta_logs_acto,f"Proyecto '{acto}' COMPLETO!")
                    elif state == 1: registrar_log(carpeta_logs_acto,f"Proyecto '{acto}' modificado correctamente")
                    elif state == 3: registrar_log(carpeta_logs_acto,f"Sin archivos para subir en el proyecto '{acto}'")
                    elif state == 0: registrar_log(carpeta_logs_acto,f"No se puedo modificar el proyecto '{acto}'", "WARNING")
                    else: registrar_log(carpeta_logs_acto,f"ERROR DESCONOCIDO al modificar '{acto}'", "WARNING")
                    break
                except Exception as e:
                    attempts -=1
                    ruta_img = tomar_screenshot(driver, carpeta_logs_acto, "Error al intentar modificar el proyecto")
                    registrar_log(carpeta_logs_acto, f"No se pudo modificar el proyecto '{acto}'. Error: {e}, Screenshot: {ruta_img}")
                    print(f"Reintentando {attempts}")
                    time.sleep(5)
        time.sleep(3)
        attempts = 3
        # if it > -1:#===================================
        #     break#==========TODO
        # it+=1#========PENDIENTE POR QUITAR

    #input("Presiona cualquier tecla para avanzar...")===========================================TODO

def extraer_datos_proyecto(driver, wait, ruta_acto: str, abogado:str, carpeta_logs_acto: str) -> None:
    """
        EXTRAE INFO DE LA CARPETA DEL PROYECTO
    """
    ex = ExtraccionCarpeta(ruta_acto)
    proyecto = ex.extraccion_de_datos()
    proyecto.abogado = abogado
    clientes = obtener_clientes_totales(proyecto)
    guardar_json(proyecto,os.path.join(proyecto.ruta, "_cache_bot"),"Proyecto analizado.json")

    time.sleep(1)
    clt = Cliente(driver, wait)

    clt.cerrar_popup_nueva_funcionalidad()
    
    clt.procesar_partes(clientes, carpeta_logs_acto, os.path.join(proyecto.ruta, "_cache_bot"))

    crear_proyecto(driver,wait, proyecto, clientes, carpeta_logs_acto)
    
def crear_proyecto(driver, wait, proyecto: Proyecto, clientes: list, carpeta_logs_acto: str):
    pp = generalTap(driver, wait)
    pp.create_project(proyecto.abogado,proyecto.cliente_principal,("\"PRUEBAS BOTBI\" " + proyecto.descripcion), proyecto.actos_involucrados)
    registrar_log(carpeta_logs_acto, "INFORMACION DE PESTAÑA 'GENERAL' COLOCADA CORRECTAMENTE")
    pt = partesTap(driver, wait)

    roles_repetidos = {}

    for cl in clientes:
        rol = cl.rol.upper()
        if rol in roles_repetidos:
            roles_repetidos[rol] += 1
        else:
            roles_repetidos[rol] = 1

    for cl in clientes:
        nombre = cl.nombre
        rol = cl.rol.upper()
        acto = cl.acto_perteneciente
        print(f"Procesando: {nombre}, rol {rol}, acto: {acto}")

        if pt.existe_cliente_rol_y_acto(acto, nombre, rol):
            continue
        pt.click_agregar_acto(acto)
        if cl.unknown:
            pt.set_cliente("PUBLICO EN GENERAL")
        else:
            pt.set_cliente(nombre)
        pt.set_rol(rol)
        if pt.existe_cliente_rol_y_acto(acto, "", rol):
            try:
                pt.set_porcentaje((100/roles_repetidos[rol]))
            except Exception:
                pt.guardar_parte()
        else:
            pt.guardar_parte()

    registrar_log(carpeta_logs_acto, "INFORMACION DE PESTAÑA 'PARTES' COLOCADA CORRECTAMENTE")

    docs = ProjectsDocumentsPage(driver, wait)
    docs.open_documents_tap()
    time.sleep(2)

    proceso_docs = Documentos(driver, wait)
    proceso_docs.procesamiento_papeleria(docs.list_all_required_descriptions(), docs, proyecto, carpeta_logs_acto)

    registrar_log(carpeta_logs_acto, "INFORMACION DE PESTAÑA DE 'DOCUMENTOS' COLOCADA CORRECTAMENTE", "SUCCESS")
    proceso_docs.comentarios_y_guardar_proyecto(proyecto, carpeta_logs_acto)

def subir_faltantes_proyecto(driver,wait, proyectoMod: ProyectoMod, carpeta_logs_acto: str) -> bool:
    modify = tapModify(driver, wait)
    modify.open_url("projects")
    try:
        modify.buscarNombreProyecto(proyectoMod.folio+", "+proyectoMod.cliente_principal+", "+proyectoMod.abogado)
        if modify.esta_en_revision():
            registrar_log(carpeta_logs_acto, "PROYECTO EN REVISION")
            tomar_screenshot(driver, carpeta_logs_acto, "PROYECTO EN REVISION")
            return False
        
        modify.presionar_lupa_nombre()
        modify.presionar_modificar_proyecto()
        modify.open_documents_tap()
        modify.subir_documentos(proyectoMod)
        modify.open_url("projects")
        modify.limpiar_busqueda_proyecto()
        return True
    except Exception:
        time.sleep(5)
        modify.open_url("projects")
        modify.limpiar_busqueda_proyecto()
        pass
    #Probar con escritura
    try:
        registrar_log(carpeta_logs_acto, f"No se encontró el proyecto con folio '{proyectoMod.folio}' en 'Proyectos'. Probando con Escrituras ")
        deeds = Escritura(driver,wait)
        deeds.open_url_deeds(deeds.url)
        deeds.buscarProyecto(str(proyectoMod.escritura)+", "+proyectoMod.cliente_principal+", "+proyectoMod.abogado)
        modify.presionar_lupa_nombre()
        deeds.open_documents_tap()

        #Proceso a repetir por archivo
        for info_parte, documentos in proyectoMod.archivos_para_subir.items():
            nombre_cliente = info_parte[0]
            for doc in documentos:
                nombre_documento = doc[0]
                ruta_documento = doc[1]
                deeds.subir_adjunto()
                deeds.set_tipo_documento(nombre_documento)
                deeds.subir_documento(ruta_documento)
                deeds.set_descripcion(nombre_cliente)

                time.sleep(5)

                deeds.click_subir()

                time.sleep(1)
                proyectoMod.contadores[nombre_documento]-=1
                if proyectoMod.contadores[nombre_documento] == 0:
                    del proyectoMod.contadores[nombre_documento]
                    deeds.marcar_faltante(nombre_documento)

                time.sleep(1)
        deeds.click_guardar()
        deeds.open_url_deeds(deeds.url)
        modify.limpiar_busqueda_proyecto()
        return True
    except Exception as e:
        deeds.open_url_deeds(deeds.url)
        modify.limpiar_busqueda_proyecto()
        registrar_log(carpeta_logs_acto,  f"No se encontró el proyecto con escritura {proyectoMod.escritura} en 'Escrituras': {e}", "ERROR")
        return False

def modificar_proyecto(driver, wait, ruta_acto: str, carpeta_logs_acto: str, ruta_abogado: str) -> bool:
    proyectoMod = obtener_faltantes(ruta_acto, carpeta_logs_acto)

    if not proyectoMod: return -1

    if len(proyectoMod.archivos_para_subir) > 0:
        if subir_faltantes_proyecto(driver,wait, proyectoMod, carpeta_logs_acto):
            cache_dir = os.path.join(ruta_acto, "_cache_bot")
            data = {
                "Fecha de registro": proyectoMod.fecha,
                "Folio": proyectoMod.folio,
                "Escritura": proyectoMod.escritura,
                "Descripcion del proyecto": proyectoMod.descripcion,
                "Cliente":proyectoMod.cliente_principal,
                "Abogado":proyectoMod.abogado,
                "Faltantes":proyectoMod.faltantes_nuevos,
                "Contadores":proyectoMod.contadores
            }
            guardar_json(data, cache_dir, ARCHIVO_FALTANTES)
            checar_fecha_valida(proyectoMod, carpeta_logs_acto, os.path.basename(ruta_acto), ruta_abogado)

            return 2 if (not proyectoMod.faltantes_nuevos or len(proyectoMod.faltantes_nuevos) == 0) else 1
        else:
            checar_fecha_valida(proyectoMod, carpeta_logs_acto, os.path.basename(ruta_acto), ruta_abogado)
            return 0
    else:
        checar_fecha_valida(proyectoMod, carpeta_logs_acto, os.path.basename(ruta_acto), ruta_abogado)
        return 2 if (not proyectoMod.faltantes_nuevos or len(proyectoMod.faltantes_nuevos) == 0) else 3
    # 3 sin archivos para subir
    # 2 significa completo
    # 1 significa incompleto
    # 0 significa que ocurrio un error al modificarlo o que esta en revision