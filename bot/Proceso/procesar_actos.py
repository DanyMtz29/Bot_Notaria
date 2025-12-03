from bot.utils.common_imports import *
from bot.utils.selenium_imports import *
import shutil

from bot.JSON.procesar_folder import Folder
from bot.core.acto_detector import ActoResolver
from bot.core.faltantes import FaltantesService
from bot.core.acto_scanner import scan_acto_folder
from bot.pages.Proyectos.procesar_cliente import Cliente
from bot.pages.Proyectos.tap_partes import partesTap
from bot.pages.Proyectos.tap_general import generalTap
from bot.pages.projects_documents import ProjectsDocumentsPage
from bot.Proceso.procesar_papeleria import Documentos
from bot.pages.Proyectos.docs_modify import tapModify
from bot.pages.Escrituras.Escrituras import Escritura
from bot.utils.Logger import setup_logger

def procesar_actos(driver, wait,abogado, actos_root):
    """
        Proceso que recorre el portal por todos los proyectos de cada abogado
    """
    #setup_logger(f"{datetime.date.today()}/{abogado}")

    it = 0
    attempts = 3
    for acto in os.listdir(actos_root):
        full = os.path.join(actos_root, acto)
        if not os.path.isdir(full):# Ignorar archivos sueltos que no sean carpetas de acto
            continue
        cache_dir = os.path.join(full, "_cache_bot")
        json_dir = os.path.join(cache_dir, "papeleria_faltante.json")
        print(f"Procesando {acto}")
        setup_logger(f"{datetime.date.today()}/{abogado}/{acto}")
        if not os.path.exists(json_dir):
            while attempts > 0:
                try:
                    print("CREANDO PROYECTO")
                    extraer_datos_proyecto(driver, wait, full, abogado, cache_dir)
                    logger.success(f"Proyecto '{acto}' creado correctamente")
                    break
                except Exception as e:
                    attempts-=1
                    logger.error(f"No se pudo crear el Proyecto '{acto}'. Error: {e}")
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    print(f"Reintentando {attempts}")
                    time.sleep(5)
        else:
            while attempts > 0:
                try:
                    if modificar_proyecto(driver, wait, full):
                        logger.success(f"Proyecto '{acto}' COMPLETO!")
                    else:
                        logger.success(f"Proyecto '{acto}' modificado correctamente")
                    break
                except Exception as e:
                    attempts -=1
                    logger.error(f"No se pudo modificar el Proyecto '{acto}'. Error: {e}")
                    print(f"Reintentando {attempts}")
                    time.sleep(5)
        time.sleep(3)
        if it > 0:
            break
        attempts = 3
        it+=1
    input("Presiona cualquier tecla para terminar...")

def extraer_datos_proyecto(driver, wait, acto: str, abogado:str, cache_dir: str) -> None:
    """
        EXTRAE INFO DE LA CARPETA DEL PROYECTO
    """
    resolver = ActoResolver()
    actos_folder = Folder()
    left, middle, right = resolver._split_por_guiones(os.path.basename(acto))
    escritura, titulo = resolver._extraer_escritura_y_titulo(left)
    descripcion = " – ".join(filter(None, [titulo, middle, right]))
    
    # 3) Escanear y guardar JSON
    extraction = scan_acto_folder(acto, acto_nombre=os.path.basename(acto))
    
    pf_list, pm_list = actos_folder._extract_partes_pf_pm(extraction)

    acto_nombre = getattr(extraction, "acto_nombre", os.path.basename(acto))
    cliente_principal = getattr(extraction, "cliente_principal")
    inm_list = getattr(extraction, "inmuebles")
    otros = getattr(extraction, "otros")

    #Guarda el json
    json_path = actos_folder._ensure_cache_and_write_json(acto, extraction)

    #all_parties = actos_folder._flatten_all_parties(pf_list, pm_list)

    partes = []
    for cl in pf_list:
        cl["tipo"] = "PF"
        partes.append(cl)
    for cl in pm_list:
        cl["tipo"] = "PM"
        partes.append(cl)

    time.sleep(1)
    cerrar_popup_nueva_funcionalidad(driver)
    clt = Cliente(driver, wait)
    
    clt.procesar_partes(partes)

    crear_proyecto(driver,wait,cliente_principal,partes, acto_nombre, descripcion, 
                  inm_list, cache_dir, escritura, abogado, otros)
    
def crear_proyecto(driver, wait, cliente, partes, acto_nombre, descripcion, inmuebles, cache_dir, escritura,abogado, otros):
    """
        CREA EL PROYECTO EN EL PORTAL
    """
    pp = generalTap(driver, wait)
    pp.create_project(abogado,cliente,("\"PRUEBAS BOTBI\" " + descripcion),acto_nombre)
    partesTAP = partesTap(driver, wait)

    roles_repetidos = {}

    #Obtener el total de roles por si se repiten
    for part in partes:
        rol = part.get("rol", "").upper()
        
        if rol in roles_repetidos:
            roles_repetidos[rol] += 1
        else:
            roles_repetidos[rol] = 1

        if part.get("tipo") == "PM":
            representantes = part.get("representantes", {})
            for representante in representantes:
                rep_rol = representante.get("rol", "").upper()
                if rep_rol in roles_repetidos:
                    roles_repetidos[rep_rol] += 1
                else:
                    roles_repetidos[rep_rol] = 1    
        else:
            conyugue = part.get("esposa_o_esposo", {})
            if conyugue:
                conyugue_rol = conyugue.get("rol", "").upper()
                if conyugue_rol in roles_repetidos:
                    roles_repetidos[conyugue_rol] += 1
                else:
                    roles_repetidos[conyugue_rol] = 1


    partes_involucradas = []
    
    for part in partes:
        if part.get("tipo") == "PM":
            reps = part.get("representantes", {})
            for rep in reps:
                partes_involucradas.append(rep)
        else:
            conyugue = part.get("esposa_o_esposo", {})
            if conyugue:
                partes_involucradas.append(conyugue)
        partes_involucradas.append(part)


    for part in partes_involucradas:
        nombre = part.get("nombre", "")
        rol    = part.get("rol", "").upper()
        print(f"Procesando: {nombre}, rol {rol}")

        if partesTAP.existe_cliente_y_rol(nombre,rol):
            continue

        partesTAP.agregar()
        if part.get("unknown"):
            partesTAP.set_cliente("PUBLICO EN GENERAL")
        else:
            partesTAP.set_cliente(nombre)
        partesTAP.set_rol(rol)
        # if (acto_nombre.lower() in {"compraventa","compraventa con apertura de credito","compraventa infonavit","compraventa fovissste",
        #             } and rol.strip().lower() == "comprador" and partesTAP.existe_cliente_y_rol("", "Comprador") ):
        #     partesTAP.set_porcentaje((100/roles_repetidos[rol]))
        # elif (acto_nombre.lower() in {"compraventa","compraventa con apertura de credito","compraventa infonavit","compraventa fovissste",
        #             } and rol.strip().lower() == "vendedor" and partesTAP.existe_cliente_y_rol("", "vendedor") ):
        #     partesTAP.set_porcentaje((100/roles_repetidos[rol]))
        if partesTAP.existe_cliente_y_rol("", rol.strip().lower()):
            try:
                partesTAP.set_porcentaje((100/roles_repetidos[rol]))
            except Exception:
                partesTap.guardar_parte()
        else:
            partesTAP.guardar_parte()

    logger.info("INFORMACION DE PESTAÑA 'PARTES' COLOCADA CORRECTAMENTE")

    docs = ProjectsDocumentsPage(driver, wait)
    docs.open_documents_tap()
    time.sleep(2)

    proceso_docs = Documentos(driver, wait)
    proceso_docs.procesamiento_papeleria(docs.list_all_required_descriptions(), docs, partes, inmuebles, otros)
    logger.info("INFORMACION DE PESTAÑA DE 'DOCUMENTOS' COLOCADA CORRECTAMENTE")
    proceso_docs.comentarios_y_guardar_proyecto(cache_dir,descripcion, escritura,cliente,abogado)

def subir_faltantes_proyecto(driver,wait, archivos_para_subir, contadores, escritura: str, clt: str, abg: str,folio:str) -> bool:
    """
        Metodo para modificar un proyecto y subir los archivos faltantes
    """
    modify = tapModify(driver, wait)
    modify.open_url("projects")
    try:
        modify.buscarNombreProyecto(folio+", "+clt+", "+abg)

        #Si esta en revision no se puede modificar, toca esperar
        #a que se quite de revision
        if modify.esta_en_revision():
            return False
        
        modify.presionar_lupa_nombre()
        modify.presionar_modificar_proyecto()
        modify.open_documents_tap()
        modify.subir_documentos(archivos_para_subir, contadores)
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
        deeds = Escritura(driver,wait)
        deeds.open_url_deeds(deeds.url)
        deeds.buscarProyecto(str(escritura)+", "+clt+", "+abg)
        modify.presionar_lupa_nombre()
        deeds.open_documents_tap()

        #Aux para pruebas
        nombre_documentos = "CURP (compareciente o partes)"

        #Proceso a repetir por archivo
        for info_parte, info_documentos in archivos_para_subir.items():
            tipo, nombre_parte, rol = FaltantesService._parse_tuple_key(info_parte)
            for nombre_documento, ruta_archivo in info_documentos:
                print(f"Procesando: {nombre_documento}")
                deeds.subir_adjunto()
                deeds.set_tipo_documento(nombre_documento)
                deeds.subir_documento(ruta_archivo)
                deeds.set_descripcion(nombre_parte)

                #Cambiar por subir
                deeds.click_cancelar()
                #deeds.click_subir()

                time.sleep(1)
                contadores[nombre_documento]-=1
                if contadores[nombre_documento] == 0:
                    deeds.marcar_faltante(nombre_documento)

                time.sleep(1)
        deeds.click_guardar()
        deeds.open_url_deeds(deeds.url)
        modify.limpiar_busqueda_proyecto()
        return True
    except Exception as e:
        deeds.open_url_deeds(deeds.url)
        deeds.limpiar_busqueda_proyecto()
        logger.error(f"No se encontró el proyecto con folio {folio} en 'Proyectos' o 'Escrituras': {e}")
        return False

def modificar_proyecto(driver, wait, acto) -> bool:
    """
        MODIFICA UN NUEVO PROYECTO/ESCRITURA EN EL PORTAL
    """
    descripcion, archivos_para_subir, contadores, json_actualizado, folio, escritura, clt, abg = FaltantesService.procesar_proyecto(acto)
    if not escritura:
        resolver = ActoResolver()
        left, middle, right = resolver._split_por_guiones(os.path.basename(acto))
        _, titulo = resolver._extraer_escritura_y_titulo(left)
        if _:
            escritura = _
            json_actualizado["Escritura"] = escritura

    if len(archivos_para_subir) > 0:    
        #if subir_faltantes_proyecto(driver,wait, archivos_para_subir,contadores, escritura, clt="GMSD ASOCIADOS", abg="Jorge del Río",folio="2551"):
        if subir_faltantes_proyecto(driver,wait, archivos_para_subir,contadores, escritura, clt, abg,folio):
            cache_dir = os.path.join(acto, "_cache_bot")
            FaltantesService._guardar_json_faltantes(cache_dir, json_actualizado)
        else:
            raise Exception
    
    return "Contadores" not in json_actualizado
    

def cerrar_popup_nueva_funcionalidad(driver):
    wait = WebDriverWait(driver, 5)

    try:
        wait.until(lambda d: d.find_element("xpath","//h4[contains(@class,'modal-title') and contains(.,'Nueva Funcionalidad')]"))
    except Exception:
        return
    
    btn = wait.until(lambda d: d.find_element("xpath","//ngb-modal-window//button[contains(text(),'Cerrar')]"))
    btn.click()