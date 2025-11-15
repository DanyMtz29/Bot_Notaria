# bot/main.py
import os, typer, time, json, re
from collections import Counter

from collections import OrderedDict
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bot.pages.projects_documents import ProjectsDocumentsPage

from bot.pages.Proyectos.tap_partes import partesTap
from bot.pages.Proyectos.tap_comentarios import comentariosTab

from bot.pages.Proyectos.tap_general import generalTap
from bot.core.acto_scanner import scan_acto_folder

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from bot.JSON.procesar_folder import Folder
from bot.core.json_file import json_file
from bot.core.faltantes import FaltantesService
#from bot.core.gmail_send import send_email
from bot.core.browser import make_driver
from bot.pages.dashboard_page import DashboardPage
from bot.pages.login_page import LoginPage
from bot.core.acto_detector import ActoResolver
from bot.pages.Proyectos.docs_modify import tapModify


app = typer.Typer(add_completion=False, no_args_is_help=False)
lista_uifs = []
lista_comentarios = {}
js = json_file()
actos_folder = Folder()

def subir_lista_uifs(driver) -> None:
    inp = driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")

    #Listas_uifs de prueba
    lista_uifs = [["UIF_PF_Enajenante_ALFREDO_ALBERTO_PALACIOS_RODRIGUEZ.pdf",r"C:\Users\mdani\OneDrive\Desktop\Botbi\Bot Notaria Publica 84\bot\_cache_bot\UIF_PF_Enajenante_ALFREDO_ALBERTO_PALACIOS_RODRIGUEZ.pdf"],
                  ["UIF_PF_Adquiriente_JUAN_ANTONIO_MURRA_GONZALEZ.pdf", r"C:\Users\mdani\OneDrive\Desktop\Botbi\Bot Notaria Publica 84\bot\_cache_bot\UIF_PF_Adquiriente_JUAN_ANTONIO_MURRA_GONZALEZ.pdf"]]
    
    for uif in lista_uifs:
        inp.send_keys(uif[1])
        #time.sleep(3)
        esperar_subida(driver)
        #Seleccionar la fila del archivo que se subio
        #fila = driver.find_element(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'{uif[0]}')] or .//*[contains(normalize-space(),'{uif[0]}')]]")
        filas = driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
        fila = filas[-1]
        #Seleccionar la columan 2, que es el 'Documento' y establecer que tipo de documento
        Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text("Consulta UIF Lista Negra")
        #Seleccionar el cliente que corresponde esa papeleria
        driver.execute_script("arguments[0].value = '';", inp)#Remover los elementos anteriores
        time.sleep(1)

def subir_doc_inmuebles(driver, inmuebles: list, doc:str) -> bool:
    """
        Sube solo los docus de los inmuebles
    """
    global lista_comentarios

    inp = driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
    flag = True
    for inm in inmuebles:
        doc_path = inm.get(doc)
        if doc_path != None:
            inp.send_keys(doc_path)
            esperar_subida(driver)
            filas = driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
            fila = filas[-1]
            Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc)
            driver.execute_script("arguments[0].value = '';", inp)
            time.sleep(1)
        else:
            #add_coment(inm.get_name(), doc)
            tup = ("INM",inm.get_name(), 'INM')
            if tup in lista_comentarios:
                lista_comentarios[tup].append(doc)
            else:
                lista_comentarios[tup] = [doc]
            flag = False
    return flag

def subir_doc_partes_basicas(driver, clientes: list, doc: str) -> None:
    """
        Sube solo los docus basicos de las partes: CURP, ACTA DE NACIMIENTO, COMP_DOM, CSF, INE
    """
    global lista_comentarios
    doc_original = doc
    if doc == "Comprobante de Domicilio (compareciente o partes)": doc = "COMP_DOMICILIO"
    elif doc == "Identificación oficial (compareciente o partes)": doc = "INE"
    elif doc == "Acta de nacimiento (compareciente o partes)": doc = "ACTA_NAC"
    elif doc == "Constancia de identificación fiscal (compareciente o partes)": doc = "CSF"
    elif doc == "CURP (compareciente o partes)": doc = "CURP"
    elif doc == "Acta de matrimonio (compareciente o partes)": doc = "ACTA_MATRIMONIO"

    inp = driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
    flag = True
    for part in clientes:
        if part.get("tipo") == "PM":
            part = part.get("representante", {})
#        if part.get("tipo") == "PF":
            #Primero chechar si no esta en importados
        if checar_docs_importar(driver, part.get("nombre"), doc_original):
            time.sleep(1)
        else:
            docs = part.get("docs")
            doc_up = docs.get(doc)
            if doc_up == None:
                if not doc == "COMP_DOMICILIO" and doc == "ACTA_MATRIMONIO":
                    #add_coment(part.get("nombre"), doc_original)
                    tup = ("PF",part.get("nombre"), part.get('rol'))
                    if tup in lista_comentarios:
                        lista_comentarios[tup].append(doc_original)
                    else:
                        lista_comentarios[tup] = [doc_original]
                    flag = False
            else:
                inp.send_keys(doc_up)
                esperar_subida(driver)
                filas = driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//*[contains(normalize-space(),'.pdf')]]")
                fila = filas[-1]
                Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc_original)
                Select(fila.find_element(By.XPATH, ".//td[3]//select")).select_by_visible_text(part.get("nombre"))
                driver.execute_script("arguments[0].value = '';", inp)
                time.sleep(1)
            
    return flag
        
def esperar_subida(driver):
    #oculto = driver.find_element(By.XPATH,"//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'col-md-8') and contains(@class,'ms-2')][.//strong[normalize-space()='1']]")))
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")))
    # print("CHECAR OCULTO: ")
    # print(oculto.get_attribute("outerHTML"))

def add_coment(cliente: str, doc_faltante: str) -> None:
    """
        A;ADIR UN COMENTARIO PARA EL JSON
    """
    #Si no existe el archivo de faltantes.json, ahi que crearlo
    global js
    if not js.exists():
        js.ensure({"faltantes": []})
    
    #Agregar lo faltante
    js.list_append("faltantes", {"cliente": cliente, "doc": doc_faltante})

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

def checar_docs_importar(driver, cliente: str, doc: str) -> bool:
    wait = WebDriverWait(driver, 20)

    # Click en "Importar" (usa wait + JS por si hay overlay)
    but = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")))
    driver.execute_script("arguments[0].click();", but)

    # Normalizar nombre de doc a tus keywords usadas en la tabla
    mapping = {
        "Acta de nacimiento (compareciente o partes)": "nacimiento",
        "Comprobante de Domicilio (compareciente o partes)": "Domicilio",
        "Constancia de identificación fiscal (compareciente o partes)": "fiscal",
    }
    doc = mapping.get(doc, doc)

    # Espera a que el modal esté visible
    modal_body = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'modal-body')]")))

    # Ubica el bloque (tabla) del cliente
    table = modal_body.find_element(
        By.XPATH,
        f".//div[contains(@class, 'form-group') and contains(@class, 'row')][.//label[normalize-space(text())='{cliente}']]"
    )

    # Dentro de la tabla, la sección de filas
    rowgroup = table.find_element(By.XPATH, ".//tbody[contains(@role,'rowgroup')]")

    # Locator para todas las filas que contengan el doc (case-insensitive robusto)
    # Nota: usamos contains(., '{doc}') directo; si necesitas 100% insensible a may/min, podemos meter translate().
    rows_locator = (
        By.XPATH,
        f".//tr[.//td[contains(., '{doc}')]]"
    )

    # Espera a que existan (o determina que no hay)
    docs_ = rowgroup.find_elements(*rows_locator)
    si_hay = len(docs_) > 0
    if not si_hay:
        # Cierra el modal y salimos
        cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
        driver.execute_script("arguments[0].click();", cerrar)
        return False

    # Función para reobtener el último row fresco
    def refetch_last_row():
        rows = rowgroup.find_elements(*rows_locator)
        if not rows:
            raise TimeoutException("La fila ya no está disponible")
        return rows[-1]

    # Intenta clickear el checkbox del último row, tolerando 'stale'
    attempts = 2
    for i in range(attempts):
        try:
            last = refetch_last_row()
            # (Opcional) imprime para depurar
            try:
                print(last.text)
            except StaleElementReferenceException:
                # Si incluso leer el texto truena, reintenta completo
                if i == attempts - 1:
                    raise
                continue

            cb = last.find_element(By.XPATH, ".//td[1]//input[@type='checkbox']")
            wait.until(EC.element_to_be_clickable(cb))
            driver.execute_script("arguments[0].click();", cb)
            break
        except StaleElementReferenceException:
            if i == attempts - 1:
                raise  # ya no reintentes
            # pequeño backoff opcional:
            # time.sleep(0.2)
            continue

    # Cierra el modal
    cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
    driver.execute_script("arguments[0].click();", cerrar)
    return True


def procesamiento_papeleria(driver, documents: list, docs, clientes: list, inmuebles: list) -> None:
    """
        Metodo para procesar todos los documentos requeridos
    """
    papeleria_inmuebles = ["Escritura Antecedente (Inmueble)", "Recibo de pago del impuesto predial","Avalúo Catastral", 
                           "Aviso preventivo","Solicitud de Avalúo", "Plano"]
    papeleria_basica = ["Comprobante de Domicilio (compareciente o partes)", "Identificación oficial (compareciente o partes)",
                        "Constancia de identificación fiscal (compareciente o partes)", "Acta de nacimiento (compareciente o partes)",
                        "CURP (compareciente o partes)", "Acta de matrimonio (compareciente o partes)"]
    papeleria_sociedad = ["Acta constitutiva (antecedente)", "Poder del representante legal", "Asambleas antecedente de la sociedad",
                          "Constancia de identificación fiscal Sociedad"]
    papeleria_otros = ["Expediente judicial", "Forma ISAI Amarilla (Registro Publico)", "Recibo de pago ISAI",
                       "Recibo de pago Derechos de Registro", "Acta de nacimiento del cónyuge", "Identificación oficial del cónyuge",
                       "Otros", "CURP del cónyuge", "Comprobante de Domicilio del cónyuge"]
    
    for doc in documents:
        print(f"DOC PROCESANDO: {doc}")
        if doc == "Consulta UIF Lista Negra":
           subir_lista_uifs(driver)
           #Marcar como hecho la lista_uif
           docs.set_faltante_by_description(doc, marcar=True)
        elif doc in papeleria_basica:
           if subir_doc_partes_basicas(driver, clientes, doc):
               docs.set_faltante_by_description(doc, marcar=True)
        if doc in papeleria_inmuebles:
            if subir_doc_inmuebles(driver,inmuebles,doc):
                docs.set_faltante_by_description(doc, marcar=True)
    
    but = driver.find_element(By.XPATH,f"//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")
    driver.execute_script("arguments[0].click();", but)
    time.sleep(1) 
    but_seleccionar = driver.find_element(By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space(text())='Importar Seleccionados']")
    driver.execute_script("arguments[0].click();", but_seleccionar)

def _fill_new_project_fields(driver, wait, cliente_principal, pf_list,pm_list, acto_nombre, descripcion, inmuebles: list, ruta: str):
    """
        Automatizacion del apartado documentos en la pagina de 'Proyectos'
    """
    resto = 'COMENTARIOS EXTRA PARA DESCRIPCION'
    pp = generalTap(driver, wait)
    pp.create_project(
        abogado="BOT SINGRAFOS BOTBI",
        cliente=cliente_principal,
        descripcion=("\"PRUEBAS BOTBI\" " + descripcion),
        acto=acto_nombre
    )
    #"""
    clientes = []
    for cl in pf_list:
        clientes.append(cl)
    for cl in pm_list:
        clientes.append(cl)
    
    time.sleep(1)
    #"""
    partes = partesTap(driver, wait)
    for cl in pf_list:
        nombre = cl.get("nombre", "")
        rol    = cl.get("rol", "").upper()
        print(f"Procesando: {nombre}, rol {rol}")
        if partes.existe_cliente_y_rol(nombre,rol):
            continue
        partes.agregar()
        partes.set_cliente(nombre)
        partes.set_rol(rol)
        if (acto_nombre.lower() in {"compraventa","compraventa con apertura de credito","compraventa infonavit","compraventa fovissste",
                                    } and rol.strip().lower() == "comprador" and partes.existe_cliente_y_rol("", "Comprador")):
            partes.set_porcentaje(50)
        partes.guardar_parte()
    #"""
    
    # #Apartado de documentos
    docs = ProjectsDocumentsPage(driver, wait)
    docs.open_documents_tap()
    time.sleep(2)

    procesamiento_papeleria(driver, docs.list_all_required_descriptions(), docs, clientes, inmuebles)
    guardar_papeleria_JSON(ruta, "\"PRUEBAS BOTBI\" " + descripcion)
    comentarios_tab = comentariosTab(driver,wait)
    if lista_comentarios:
        for tup, lis in lista_comentarios.items():
            comentarios = ["Falta papeleria del "]
            if tup[0] != 'INM':
                comentarios.append(f"Cliente {tup[1]}: ")
            else:
                comentarios.append(f"Inmueble: {tup[1]}: ")
            for i in range(0,(len(lis))):
                comentarios.append(f"{i+1}.-{lis[i]}. ")
            comentarios.append("\n")
            comentario_subir = "".join(comentarios)
            comentarios_tab.open_tap_comentarios()
            comentarios_tab.agregar_comentario(comentario_subir)
            comentarios_tab.enviar_comentario()
            time.sleep(1)
        #comentarios_tab.guardar_proyecto()
        print("GUARDANDO PROYECTO...")
    else:
        #comentarios_tab.guardar_proyecto()
        print("GUARDANDO PROYECTO...")
        #print("GUARDAR PROYECTO...")
    # print("PAPELERIA FALTANTE")
    # for tup, lis in lista_comentarios.items():
    #     if tup[0] == "PF":
    #         print(f"Nombre del cliente: {tup[1]}")
    #     else:
    #         print(f"Inmueble: {tup[1]}")
    #     for i in range(0, len(lis)):
    #         print(f"{i+1}. {lis[i]}")
    #     print("\n")

def guardar_papeleria_JSON(ruta: str, descripcion: str):
    """
    Guarda en JSON con estructura extendida:
    {
        "Fecha de registro": "YYYY-MM-DDTHH:MM:SS",
        "Descripcion del proyecto": "...",
        "('Tipo','Nombre','Rol')": [faltantes],
        "Contadores": {
            "Plano": 3,
            "Solicitud de Avalúo": 2,
            "CURP (Compareciente o partes)": 2
        }
    }
    """
    ruta = os.path.join(ruta, "papeleria_faltante.json")
    data_ordenada = OrderedDict()
    data_ordenada["Fecha de registro"] = datetime.now().isoformat(timespec="seconds")
    data_ordenada["Descripcion del proyecto"] = descripcion

    # Guardar faltantes por cada parte
    for k, v in lista_comentarios.items():
        data_ordenada[str(k)] = v

    # === NUEVO: calcular conteo general de todos los faltantes ===
    todos_faltantes = []
    for lista in lista_comentarios.values():
        todos_faltantes.extend(lista)
    conteo = dict(Counter(todos_faltantes))
    data_ordenada["Contadores"] = conteo

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data_ordenada, f, indent=4, ensure_ascii=False)

    print(f"Papelería guardada con contadores en: {ruta}")

def quitar_estatus(driver, wait)-> None:
    try:
        estatus = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//span[contains(@class,'badge') and contains(@class,'text-bg-light') and "
                "contains(normalize-space(.), 'Estatus: En Revisión')]"
            ))
        )
        print("Elemento de estatus detectado:", estatus.text)
    except Exception as e:
        print(f"No se encontró el elemento de estatus: {e}")

def modificar_proyecto(driver,wait, archivos_para_subir,url, contadores, descripcion:str) -> None:
    """
        Metodo para modificar un proyecto y subir los archivos faltantes
    """
    modify = tapModify(driver, wait)
    modify.open_url_projects(url)
    modify.buscarNombreProyecto(descripcion)

    #Si esta en revision no se puede modificar, toca esperar
    #a que se quite de revision
    if modify.esta_en_revision():
        return False
    
    # modify.presionar_lupa_nombre()
    # modify.presionar_modificar_proyecto()
    # modify.open_documents_tap()
    # modify.subir_documentos(archivos_para_subir, contadores)    
    return True


def proceso_por_abogado(headless,abogado, actos_root, url,user,pwd):
    """
        Proceso que  recorre el portal por todos los proyectos de cada abogado
    """
    global js, actos_folder, lista_uifs
    
    #driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=7)

    try:
        #1) Login
        # LoginPage(driver, wait).login(url, user, pwd)
        # DashboardPage(driver, wait).assert_loaded()
        # logger.info("Login OK")

        # 2) Buscar primer acto sin cache
        target_acto, flag = actos_folder._find_first_acto_without_cache(actos_root)
        
        if flag:
            logger.warning("No hay actos nuevos (todos tienen _cache_bot). Nada que hacer.")
            #logger.warning("NO TIENE CACHE")
        else:
            logger.warning("YA TIENE CACHE")
            descripcion, archivos_para_subir, contadores, json_actualizado = FaltantesService.procesar_proyecto(target_acto)
            # archivos_para_subir: { key_str : [(nombre_doc, ruta_abs), ...] }
            # for key, pairs in archivos_para_subir.items():
            #     tipo, nombre, rol = FaltantesService._parse_tuple_key(key)
            #     print(f"Cliente: {nombre}")
            #     for nombre_doc, ruta in pairs:
            #         # aquí usas tu flujo Selenium para subir 'ruta' y etiquetarlo como 'nombre_doc'
            #         print("Subir:", nombre_doc, "->", ruta)

            if len(archivos_para_subir) > 0:
                print("Contadores finales:")
                # for archivo, total in contadores.items():
                #     print(f"\t{archivo}: {total}")
                # cur = driver.current_url
                # base = actos_folder._origin_of(cur)
                # if modificar_proyecto(driver,wait, archivos_para_subir,base,contadores,descripcion="2488"):
                #     cache_dir = os.path.join(target_acto, "_cache_bot")
                #     FaltantesService._guardar_json_faltantes(cache_dir, json_actualizado)

                
            if not "Contadores" in json_actualizado:
                print("Proyecto completo. Sin faltantes.")
            else:
                print("Aun faltan archivos!!")
            return
        
        return
        resolver = ActoResolver()
        left, middle, right = resolver._split_por_guiones(os.path.basename(target_acto))
        _, titulo = resolver._extraer_escritura_y_titulo(left)
        #print(f"Titulo: {titulo}, Middle: {middle}, Right: {right}, _: {_}")
        descripcion = " – ".join(filter(None, [titulo, middle, right]))
        #print(f"Descripcion: {descripcion}")
        
        # 3) Escanear y guardar JSON
        extraction = scan_acto_folder(target_acto, acto_nombre=os.path.basename(target_acto))
        json_path = actos_folder._ensure_cache_and_write_json(target_acto, extraction)

        # 4) PF/PM -> consola y contexto
        pf_list, pm_list = actos_folder._extract_partes_pf_pm(extraction)

        actos_folder._print_partes_console(
            pf_list, pm_list,
            getattr(extraction, "acto_nombre", os.path.basename(target_acto))
        )
        acto_ctx = {
            "json_path": json_path,
            "pf": pf_list,
            "pm": pm_list,
            "acto_dir": target_acto,
            "acto_nombre": getattr(extraction, "acto_nombre", os.path.basename(target_acto)),
            "cliente_principal": getattr(extraction, "cliente_principal"),
            "inmuebles": getattr(extraction, "inmuebles"),
            "otros":getattr(extraction, "otros")
        }

        """
        # 5) Ir a Clientes y PROCESAR TODAS LAS PARTES
        cur = driver.current_url
        base = actos_folder._origin_of(cur)

        all_parties = actos_folder._flatten_all_parties(acto_ctx["pf"], acto_ctx["pm"])
        if not all_parties:
            logger.warning("No hay PARTES (PF/PM) para buscar/crear y sacar UIF.")
            return

        logger.info(f"Procesando {len(all_parties)} parte(s) del acto: {acto_ctx['acto_nombre']}")
        for idx, party in enumerate(all_parties, start=1):
            logger.info(f"===== PARTE {idx}/{len(all_parties)} :: {party.get('tipo')} | {party.get('rol') or '-'} | {party.get('nombre_upper')} =====")
            try:
                if party.get('tipo') == "PM":
                    actos_folder._process_party(lista_uifs, driver, wait, base, party.get("representante"))
                actos_folder._process_party(lista_uifs, driver, wait, base, party)
            except Exception as e:
                logger.exception(f"Error procesando parte [{party.get('nombre_upper')}]: {e}")

        logger.success("Todas las partes del acto han sido procesadas.")
        # (Más adelante: iterar actos/proyectos; por ahora solo el primero sin _cache_bot)
        """
        _fill_new_project_fields(driver,wait,acto_ctx["cliente_principal"],acto_ctx["pf"],acto_ctx["pm"], acto_ctx["acto_nombre"],descripcion, acto_ctx["inmuebles"], os.path.dirname(acto_ctx["json_path"]))

    finally:
        input("INTRODUCE: ")
        pass
        # driver.quit()

# Pipeline
# =========================
def _pipeline(headless: bool):
    #Variables globales
    
    # send_email(
    #     to="danieljm2901@gmail.com",
    #     subject="HOLA DANIEL!!",
    #     body_html="<h1>ESTIMADO QUERIDO AMIGO:</h1><p>Sientase orgulloso de la vida.</p>",
    #     body_text="Es un dia maravilloso para estar en cama."
    # )

    #return

    load_dotenv("bot/config/.env")

    url = os.getenv("PORTAL_URL", "")
    user = os.getenv("PORTAL_USER", "")
    pwd  = os.getenv("PORTAL_PASS", "")
    actos_root = os.getenv("LOCAL_ACTOS_ROOT", "")

    if not (url and user and pwd and actos_root):
        logger.error("Faltan PORTAL_URL/USER/PASS y/o ACTOS_ROOT en .env")
        raise typer.Exit(code=2)

    for name in os.listdir(actos_root):
          proceso_por_abogado(headless,name,os.path.abspath(os.path.join(actos_root,name)), url,user,pwd)
    

# =========================
# CLI
# =========================
@app.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    headless: bool = typer.Option(False, help="Ejecuta navegador en modo headless"),
):
    """
    Sin subcomando: ejecuta el pipeline por defecto.
    Con subcomando `run`: hace lo mismo.
    """
    if ctx.invoked_subcommand is None:
        _pipeline(headless=headless)

@app.command("run")
def run(
    headless: bool = typer.Option(False, help="Ejecuta navegador en modo headless"),
):
    """Ejecuta el pipeline principal (alias)."""
    _pipeline(headless=headless)

if __name__ == "__main__":
    app()
"""
{
    "Fecha de registro": "2025-11-12T08:04:19",
    "Descripcion del proyecto": "\"PRUEBAS BOTBI\" Adjudicacion – Juan – INM 32",
    "('INM', 'Inmueble 20_mz_Dej', 'INM')": [
        "Escritura Antecedente (Inmueble)",
        "Recibo de pago del impuesto predial",
        "Solicitud de Avalúo",
        "Plano"
    ],
    "('INM', 'Inmueble 10_mz', 'INM')": [
        "Recibo de pago del impuesto predial",
        "Solicitud de Avalúo"
    ],
    "Contadores": {
        "Escritura Antecedente (Inmueble)": 1,
        "Recibo de pago del impuesto predial": 2,
        "Solicitud de Avalúo": 2,
        "Plano": 1
    }
}
"""