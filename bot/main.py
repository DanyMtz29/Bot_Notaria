# bot/main.py
import os
import typer
import time
from loguru import logger
from dotenv import load_dotenv

from bot.pages.projects_documents import ProjectsDocumentsPage

from bot.pages.Proyectos.tap_partes import partesTap

from bot.core.browser import make_driver
from bot.pages.login_page import LoginPage
from bot.pages.dashboard_page import DashboardPage

from bot.pages.Proyectos.tap_general import generalTap
from bot.core.acto_scanner import scan_acto_folder

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bot.JSON.procesar_folder import Folder
from bot.core.json_file import json_file

from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path


app = typer.Typer(add_completion=False, no_args_is_help=False)
lista_uifs = []
js = json_file()
actos_folder = Folder()

def subir_lista_uifs(driver) -> None:
    inp = driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")

    #Listas_uifs de prueba
    # lista_uifs = [["UIF_PF_Enajenante_ALFREDO_ALBERTO_PALACIOS_RODRIGUEZ.pdf",r"C:\Users\mdani\OneDrive\Desktop\Botbi\Bot Notaria Publica 84\bot\_cache_bot\UIF_PF_Enajenante_ALFREDO_ALBERTO_PALACIOS_RODRIGUEZ.pdf"],
    #               ["UIF_PF_Adquiriente_JUAN_ANTONIO_MURRA_GONZALEZ.pdf", r"C:\Users\mdani\OneDrive\Desktop\Botbi\Bot Notaria Publica 84\bot\_cache_bot\UIF_PF_Adquiriente_JUAN_ANTONIO_MURRA_GONZALEZ.pdf"]]
    
    for uif in lista_uifs:
        inp.send_keys(uif[1])
        time.sleep(3)
        #Seleccionar la fila del archivo que se subio
        #fila = driver.find_element(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'{uif[0]}')] or .//*[contains(normalize-space(),'{uif[0]}')]]")
        filas = driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
        fila = filas[-1]
        #Seleccionar la columan 2, que es el 'Documento' y establecer que tipo de documento
        Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text("Consulta UIF Lista Negra")
        #Seleccionar el cliente que corresponde esa papeleria
        driver.execute_script("arguments[0].value = '';", inp)#Remover los elementos anteriores
        time.sleep(2)

def subir_doc_inmuebles(driver, inmuebles: list, doc:str) -> bool:
    """
        Sube solo los docus de los inmuebles
    """
    inp = driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
    flag = True
    for inm in inmuebles:
        doc_path = inm.get(doc)
        if doc_path != None:
            inp.send_keys(doc_path)
            time.sleep(3)
            filas = driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
            fila = filas[-1]
            Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc)
            driver.execute_script("arguments[0].value = '';", inp)
            time.sleep(2)
        else:
            add_coment(inm.get_name(), doc)
            flag = False
    return flag

def subir_doc_partes_basicas(driver, clientes: list, doc: str) -> None:
    """
        Sube solo los docus basicos de las partes: CURP, ACTA DE NACIMIENTO, COMP_DOM, CSF, INE
    """
    doc_original = doc
    if doc == "Comprobante de Domicilio (compareciente o partes)": doc = "COMP_DOMICILIO"
    elif doc == "Identificación oficial (compareciente o partes)": doc = "INE"
    elif doc == "Acta de nacimiento (compareciente o partes)": doc = "ACTA_NAC"
    elif doc == "Constancia de identificación fiscal (compareciente o partes)": doc = "CSF"
    elif doc == "CURP (compareciente o partes)": doc = "CURP"

    inp = driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
    flag = True
    for part in clientes:
        if part.get("tipo") == "PF":
            #Primero chechar si no esta en importados
            if checar_docs_importar(driver, part.get("nombre"), doc_original):
                time.sleep(3)
            else:
                docs = part.get("docs")
                doc_up = docs.get(doc)
                if doc_up == None:
                    if not doc == "COMP_DOMICILIO":
                        add_coment(part.get("nombre"), doc_original)
                        flag = False
                else:
                    inp.send_keys(doc_up)
                    time.sleep(4)
                    #fila = driver.find_element(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'{Path(doc_up).name}')] or .//*[contains(normalize-space(),'{Path(doc_up).name}')]]")
                    filas = driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
                    fila = filas[-1]
                    Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc_original)
                    Select(fila.find_element(By.XPATH, ".//td[3]//select")).select_by_visible_text(part.get("nombre"))
                    driver.execute_script("arguments[0].value = '';", inp)
                    time.sleep(2)
    return flag
        
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

def checar_docs_importar(driver,cliente: str, doc:str) -> bool:
    #Seleccionar el boton de importar
    but = driver.find_element(By.XPATH,f"//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")
    driver.execute_script("arguments[0].click();", but)

    #tables = driver.find_elements(By.XPATH, "//div[@class='modal-body']//div[@class='form-group']")
    #Obtener las tablas
    if doc == "Acta de nacimiento (compareciente o partes)": doc = "nacimiento"
    elif doc == "Comprobante de Domicilio (compareciente o partes)": doc = "Domicilio"
    elif doc == "Constancia de identificación fiscal (compareciente o partes)": doc = "fiscal"

    modal_body = driver.find_element(By.XPATH, ".//div[contains(@class,'modal-body')]")
    table = modal_body.find_element(By.XPATH,f".//div[contains(@class, 'form-group') and contains(@class, 'row')][.//label[normalize-space(text())='{cliente}']]")
    row = table.find_element(By.XPATH, ".//tbody[contains(@role,'rowgroup')]")
    docs_ = row.find_elements(By.XPATH, f".//tr[.//td[contains(., '{doc}')]]")
    si_hay = len(docs_)>0
    if si_hay:
        last = docs_[-1]
        sub = last.find_element(By.XPATH, "./td[1]//input[@type='checkbox']")
        sub.click()
        
    time.sleep(1) 
    but_seleccionar = driver.find_element(By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space(text())='Regresar']")
    driver.execute_script("arguments[0].click();", but_seleccionar)
    return si_hay

def procesamiento_papeleria(driver, documents: list, docs, clientes: list, inmuebles) -> None:
    """
        Metodo para procesar todos los documentos requeridos
    """
    papeleria_inmuebles = ["Escritura Antecedente (Inmueble)", "Recibo de pago del impuesto predial","Avalúo Catastral", 
                           "Aviso preventivo","Solicitud de Avalúo", "Plano"]
    papeleria_basica = ["Comprobante de Domicilio (compareciente o partes)", "Identificación oficial (compareciente o partes)",
                        "Constancia de identificación fiscal (compareciente o partes)", "Acta de nacimiento (compareciente o partes)",
                        "CURP (compareciente o partes)"]
    papeleria_sociedad = ["Acta constitutiva (antecedente)", "Poder del representante legal", "Asambleas antecedente de la sociedad",
                          "Constancia de identificación fiscal Sociedad"]
    papeleria_otros = ["Expediente judicial", "Forma ISAI Amarilla (Registro Publico)", "Recibo de pago ISAI",
                       "Recibo de pago Derechos de Registro"]
    
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

def _fill_new_project_fields(driver, wait, cliente_principal, pf_list,pm_list, acto_nombre, inmuebles):
    """
        Automatizacion del apartado documentos en la pagina de 'Proyectos'
    """
    resto = 'COMENTARIOS EXTRA PARA DESCRIPCION'
    pp = generalTap(driver, wait)
    pp.create_project(
        abogado="BOT SINGRAFOS BOTBI",
        cliente=cliente_principal,
        descripcion=("\"PRUEBA BOTBI\" NOMBRE_CARPETA " + resto),
        acto=acto_nombre
    )
    #"""
    clientes = []
    for cl in pf_list:
        clientes.append(cl)
    for cl in pm_list:
        clientes.append(cl)
    
    partes = partesTap(driver, wait)
    for cl in pf_list:
        partes.agregar()
        partes.set_cliente(cl.get("nombre"))
        partes.set_rol(cl.get("rol").upper())
        partes.guardar_parte()
        time.sleep(1)
        
    # #Apartado de documentos
    docs = ProjectsDocumentsPage(driver, wait)
    docs.open_documents_tab()
    time.sleep(2)
    #""" 
    procesamiento_papeleria(driver, docs.list_all_required_descriptions(), docs, clientes, inmuebles)

# Pipeline
# =========================
def _pipeline(headless: bool):
    #Variables globales
    global js, actos_folder, lista_uifs

    load_dotenv("bot/config/.env")

    url = os.getenv("PORTAL_URL", "")
    user = os.getenv("PORTAL_USER", "")
    pwd  = os.getenv("PORTAL_PASS", "")
    actos_root = os.getenv("LOCAL_ACTOS_ROOT", "")

    if not (url and user and pwd and actos_root):
        logger.error("Faltan PORTAL_URL/USER/PASS y/o ACTOS_ROOT en .env")
        raise typer.Exit(code=2)

    driver, wait = make_driver(headless=headless, page_load_timeout=60, wait_timeout=20)

    try:
        #1) Login
        LoginPage(driver, wait).login(url, user, pwd)
        DashboardPage(driver, wait).assert_loaded()
        logger.info("Login OK")

        # 2) Buscar primer acto sin cache
        target_acto = actos_folder._find_first_acto_without_cache(actos_root)
        if not target_acto:
            logger.warning("No hay actos nuevos (todos tienen _cache_bot). Nada que hacer.")
            return

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

        #Por si se requieren poner faltantes
        js.set_path(target_acto + "\\_cache_bot")

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
                actos_folder._process_party(lista_uifs, driver, wait, base, party)
            except Exception as e:
                logger.exception(f"Error procesando parte [{party.get('nombre_upper')}]: {e}")

        logger.success("Todas las partes del acto han sido procesadas.")
        # (Más adelante: iterar actos/proyectos; por ahora solo el primero sin _cache_bot)
        """
        _fill_new_project_fields(driver,wait,acto_ctx["cliente_principal"],acto_ctx["pf"],acto_ctx["pm"], acto_ctx["acto_nombre"], acto_ctx["inmuebles"])
        

    finally:
        input("INTRODUCE: ")
        pass
        # driver.quit()

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