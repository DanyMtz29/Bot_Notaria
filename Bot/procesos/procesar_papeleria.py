#Imports independientes
from collections import OrderedDict, Counter
import time, os, datetime, shutil

#Imports mios
from Bot.ui_selenium.pages.base import Base
from Bot.ui_selenium.pages.tap_comentarios import comentariosTab
from Bot.models.modelos import Proyecto
from Bot.config.papeleria import *
from Bot.config.rutas import ARCHIVO_FALTANTES
from Bot.helpers.carpetas import obtener_clientes_totales, obtener_solo_clientes_pfs
from Bot.helpers.json import guardar_json
from Bot.helpers.logs import registrar_log

#imports selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


class Documentos(Base):
    def __init__(self, driver, wait, proyecto: Proyecto):
        super().__init__(driver, wait)
        self.lista_comentarios = {}
        self.proyecto = proyecto

    def esperar_subida(self):
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'col-md-8') and contains(@class,'ms-2')][.//strong[normalize-space()='1']]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")))

    def subir_lista_uifs(self, clientes: list, doc: str) -> bool:
        flag = True
        for cl in clientes:
            if not cl.uif:
                tup = ("PF",cl.nombre, cl.ruta_guardado)
                if tup in self.lista_comentarios:
                    self.lista_comentarios[tup].append(doc)
                else:
                    self.lista_comentarios[tup] = [doc]
                flag = False
                continue
            
            self.subir_doc_input(cl.uif, cl.nombre, doc)
        return flag

    def subir_doc_inmuebles(self, inmuebles: list, doc:str) -> bool:
        if not inmuebles: return False

        flag = True
        for inm in inmuebles:
            docs = inm.docs
            doc_path = docs.obtener_documento(doc)
            if doc_path != None:
                self.subir_doc_input(doc_path, inm.nombre, doc)
            else:
                tup = ("INM",inm.nombre, inm.ruta_guardado)
                self.add_coment(tup, doc)
                flag = False
        return flag

    def add_coment(self, parte: tuple, doc:str) -> None:
        if doc not in self.proyecto.papeleria_total:
            return
        if parte in self.lista_comentarios:
            self.lista_comentarios[parte].append(doc)
        else:
            self.lista_comentarios[parte] = [doc]

    def subir_doc_select(self, doc_up: str, parte, doc_original: str) -> None:
        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
        inp.send_keys(doc_up)
        self.esperar_subida()
        #filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//*[contains(normalize-space(),'.pdf')]]")
        filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tbody[contains(@class,'k-table-tbody')]//tr[@role='row']")
        fila = filas[-1]
        Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc_original)
        if parte.unknown:
            fila.find_element(By.XPATH, ".//td[4]//input").send_keys(parte.nombre)
        else:
            Select(fila.find_element(By.XPATH, ".//td[3]//select")).select_by_visible_text(parte.nombre)
        self.driver.execute_script("arguments[0].value = '';", inp)
        time.sleep(1)
    
    def subir_doc_input(self, doc_up: str, nombre:str, doc_original: str) -> None:
        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
        inp.send_keys(doc_up)
        self.esperar_subida()
        #filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//*[contains(normalize-space(),'.pdf')]]")
        filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tbody[contains(@class,'k-table-tbody')]//tr[@role='row']")
        fila = filas[-1]
        Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc_original)
        fila.find_element(By.XPATH, ".//td[4]//input").send_keys(nombre)
        self.driver.execute_script("arguments[0].value = '';", inp)
        time.sleep(1)

    def subir_papeleria_sociedad(self, partes: list, doc: str) -> bool:

        flag = True
        hay_pm = False
        for parte in partes:
            if parte.tipo == "PM":
                docs = parte.docs
                hay_pm = True
                if doc == ACTA_CONSTITUTIVA:
                    if not parte.unknown and self.checar_docs_importar(parte.nombre, doc):
                        time.sleep(1)
                    else:
                        doc_up = docs.obtener_documento(doc)
                        if doc_up == None:
                            self.add_coment(("PM",parte.nombre, parte.ruta_guardado), doc)
                            flag = False
                        else:
                            self.subir_doc_select(doc_up, parte, doc)
                elif doc == CSF_SOCIEDAD:
                    if not parte.unknown and (self.checar_docs_importar(parte.nombre, doc) or self.checar_docs_importar(parte.nombre, CSF)):
                        time.sleep(1)
                    else:
                        doc_up = docs.obtener_documento(doc)
                        if doc_up == None:
                            self.add_coment(("PM",parte.nombre, parte.ruta_guardado), doc)
                            flag = False
                        else:
                            self.subir_doc_select(doc_up, parte, doc)
                elif doc == ASAMBLEAS:
                    if not parte.unknown:
                        self.checar_docs_importar_varios(parte.nombre, doc)
                    asambleas = docs.obtener_documento(doc) or []
                    for asam in asambleas:
                        self.subir_doc_select(asam, parte, doc)
                elif doc == CARTA_INSTRUCCION:
                    es_banco = parte.es_banco
                    doc_up = docs.obtener_documento(doc)
                    if es_banco:
                        if doc_up:
                            self.subir_doc_input(doc_up, parte.nombre, doc)
                        else:
                            self.add_coment(("PM",parte.nombre, parte.ruta_guardado), doc)
                            flag = False
                    else: flag = False
                elif doc == PODER_REPRESENTANTE:
                    doc_up = docs.obtener_documento(doc)
                    if doc_up:
                        self.subir_doc_input(doc_up, parte.nombre, doc)
                    else:
                        self.add_coment(("PM",parte.nombre, parte.ruta_guardado), doc)
                        flag = False
        return hay_pm and flag
                    
    def subir_doc_partes_basicas(self,clientes: list, doc: str) -> bool:
        flag = True

        for part in clientes:
            if not part.unknown and self.checar_docs_importar(part.nombre, doc):
                time.sleep(1)
            else:
                doc_up= part.docs.obtener_documento(doc)
                if doc_up == None:
                    if doc not in (COMPROBANTE_DOMICILIO, ACTA_MAT):
                        tup = ("PF",part.nombre, part.ruta_guardado)
                        self.add_coment(tup,doc)
                    flag = False
                else:
                    self.subir_doc_select(doc_up, part, doc)
        return flag
    
    def checar_docs_importar_varios(self, cliente: str, doc: str) -> None:
        wait = WebDriverWait(self.driver, 20)

        but = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")))
        self.driver.execute_script("arguments[0].click();", but)

        time.sleep(2)

        modal_body = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'modal-body')]")))

        table = modal_body.find_element(By.XPATH,f".//div[contains(@class, 'form-group') and contains(@class, 'row')][.//label[normalize-space(text())='{cliente}']]")

        rowgroup = table.find_element(By.XPATH, ".//tbody[contains(@role,'rowgroup')]")

        rows_locator = (By.XPATH,f".//tr[.//td[contains(., '{doc}')]]")

        docs_ = rowgroup.find_elements(*rows_locator)
        si_hay = len(docs_) > 0
        if not si_hay:
            cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
            self.driver.execute_script("arguments[0].click();", cerrar)
            return

        selected_texts = []
        rows = rowgroup.find_elements(*rows_locator)
        for idx in range(len(rows)):
            tries = 3
            for attempt in range(tries):
                try:
                    rows_fresh = rowgroup.find_elements(*rows_locator)
                    if idx >= len(rows_fresh):
                        break
                    row = rows_fresh[idx]

                    try:
                        selected_texts.append(row.text)
                    except StaleElementReferenceException:
                        if attempt == tries - 1:
                            raise
                        continue

                    cb = row.find_element(By.XPATH, ".//td[1]//input[@type='checkbox']")
                    wait.until(EC.element_to_be_clickable(cb))
                    self.driver.execute_script("arguments[0].click();", cb)
                    break
                except StaleElementReferenceException:
                    if attempt == tries - 1:
                        raise
                    time.sleep(0.15)
                    continue

        # Cierra el modal
        cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
        self.driver.execute_script("arguments[0].click();", cerrar)


    def checar_docs_importar(self,cliente: str, doc: str) -> bool:
        wait = WebDriverWait(self.driver, 20)

        but = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")))
        self.driver.execute_script("arguments[0].click();", but)

        mapping = {
            ACTA_NAC: "nacimiento",
            COMPROBANTE_DOMICILIO: "Domicilio",
            CSF: "fiscal",
        }
        doc = mapping.get(doc, doc)

        time.sleep(2)

        modal_body = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'modal-body')]")))

        table = modal_body.find_element(By.XPATH,f".//div[contains(@class, 'form-group') and contains(@class, 'row')][.//label[normalize-space(text())='{cliente}']]")

        rowgroup = table.find_element(By.XPATH, ".//tbody[contains(@role,'rowgroup')]")

        rows_locator = (By.XPATH,f".//tr[.//td[contains(., '{doc}')]]")

        docs_ = rowgroup.find_elements(*rows_locator)
        si_hay = len(docs_) > 0
        if not si_hay:
            cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
            self.driver.execute_script("arguments[0].click();", cerrar)
            return False

        def refetch_last_row():
            rows = rowgroup.find_elements(*rows_locator)
            if not rows:
                raise TimeoutException("La fila ya no está disponible")
            return rows[-1]

        attempts = 2
        for i in range(attempts):
            try:
                last = refetch_last_row()
                # try:
                # except StaleElementReferenceException:
                #     if i == attempts - 1:
                #         raise
                #     continue

                cb = last.find_element(By.XPATH, ".//td[1]//input[@type='checkbox']")
                wait.until(EC.element_to_be_clickable(cb))
                self.driver.execute_script("arguments[0].click();", cb)
                break
            except StaleElementReferenceException:
                if i == attempts - 1:
                    raise  # ya no se reintenta
                continue

        # Cierra el modal
        cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
        self.driver.execute_script("arguments[0].click();", cerrar)
        return True

    def procesamiento_papeleria(self,documents: list,docs, carpeta_logs: str):
        
        ya_subio_uifs = False # En algunos actos viene 2 veces la uif, para esto es la variable
        clientes = []
        clientes.extend(self.proyecto.pfs)
        clientes.extend(self.proyecto.pms)
        clientes_totales = obtener_clientes_totales(self.proyecto)
        clientes_pfs = obtener_solo_clientes_pfs(self.proyecto)

        for doc in documents:
            if doc in LISTAS_UIFS:
                if self.subir_lista_uifs(clientes_totales, doc) and not ya_subio_uifs:
                    docs.set_faltante_by_description(doc, marcar=True)
                    ya_subio_uifs = True
            elif doc in PAPELERIA_BASICA_PF:
                if self.subir_doc_partes_basicas(clientes_pfs, doc):
                    docs.set_faltante_by_description(doc, marcar=True)
            elif doc in PAPELERIA_INMUEBLES:
                if self.subir_doc_inmuebles(self.proyecto.inmuebles,doc):
                    docs.set_faltante_by_description(doc, marcar=True)
            elif doc in PAPELERIA_SOCIEDAD_PM:
                if self.subir_papeleria_sociedad(clientes, doc):
                    docs.set_faltante_by_description(doc, marcar=True)
            elif doc in PAPELERIA_OTROS:
                documentos_a_Subir = self.proyecto.otros
                doc_up = documentos_a_Subir.obtener_documento(doc)
                if doc_up:
                    if doc == OTROS:#Porque es una lista
                        for d in doc_up:
                            self.subir_doc_input(d,"Parte del acto", doc)
                    else:#Solo es un archivo
                        self.subir_doc_input(doc_up,"Parte del acto", doc)
                        docs.set_faltante_by_description(doc, marcar=True)
            
        but = self.driver.find_element(By.XPATH,f"//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")
        self.driver.execute_script("arguments[0].click();", but)
        time.sleep(1) 
        but_seleccionar = self.driver.find_element(By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space(text())='Importar Seleccionados']")
        self.driver.execute_script("arguments[0].click();", but_seleccionar)



        #gUARDAR LAS LISTAS FUIS EN LA CARPETA DEL SERVIDOR SI NO VAN EN EL PORTAL
        if not ya_subio_uifs:
            carpeta_uifs = os.path.join(self.proyecto.ruta, "LISTAS UIFS")
            os.makedirs(carpeta_uifs, exist_ok=True)
            for cl in clientes_totales:
                if not cl.uif:
                    tup = ("PF",cl.nombre, cl.ruta_guardado)
                    if tup in self.lista_comentarios:
                        self.lista_comentarios[tup].append(LISTA_UIF1)
                    else:
                        self.lista_comentarios[tup] = [LISTA_UIF1]
                    continue
                shutil.move(cl.uif, carpeta_uifs)
                registrar_log(carpeta_logs ,f"Guardada UIF de {cl.nombre} en carpeta: {carpeta_uifs}")

    def comentarios_y_guardar_proyecto(self, CARPETA_LOGS_ACTO):
        comentarios_tab = comentariosTab(self.driver,self.wait)
        time.sleep(2)
        if self.lista_comentarios:
            for tup, lis in self.lista_comentarios.items():
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
                comentarios_tab.enviar_comentario(CARPETA_LOGS_ACTO)
                time.sleep(1)
        #ACTIVAR PARA GUARDAR EL PROYECTO TODO===================================================================
        #comentarios_tab.guardar_proyecto(CARPETA_LOGS_ACTO)
        
        registrar_log(CARPETA_LOGS_ACTO, "INFORMACION DE PESTAÑA 'COMENTARIOS' RELLENADA CORRECTAMENTE", "SUCCESS")
        time.sleep(2)
        
        try:
            self.proyecto.folio = comentarios_tab.get_folio("\"PRUEBAS BOTBI\" " + self.proyecto.descripcion)
        except Exception as e:
            registrar_log(CARPETA_LOGS_ACTO, f"NO se pudo capturar el folio en el proyecto: {e}", "ERROR")
            pass
        
        cache_dir = os.path.join(self.proyecto.ruta,"_cache_bot")
        #POR QUITAR POR ABOGADOS=============================TODO==========================
        self.guardar_papeleria_JSON(cache_dir, "\"PRUEBAS BOTBI\" " + self.proyecto.descripcion)
        #self.guardar_papeleria_JSON(cache_dir,self.proyecto.descripcion)
        registrar_log(CARPETA_LOGS_ACTO, f"DOCUMENTACION DEL ACTO GUARDADA CORRECTAMENTE EN LA CARPETA '_cache_bot': {cache_dir}", "SUCCESS")

    def guardar_papeleria_JSON(self,cache_dir: str, descripcion: str):
        data_ordenada = OrderedDict()
        data_ordenada["Fecha de registro"] = str(datetime.date.today())
        data_ordenada["Folio"] = self.proyecto.folio
        data_ordenada["Escritura"] = self.proyecto.escritura
        data_ordenada["Descripcion del proyecto"] = descripcion
        data_ordenada["Cliente"] = self.proyecto.cliente_principal
        data_ordenada["Abogado"] = self.proyecto.abogado
        data_ordenada['Papeleria importante'] = self.proyecto.papeleria_total

        faltantes = {}
        for k, v in self.lista_comentarios.items():
            faltantes[str(k)] = v
        data_ordenada["Faltantes"] = faltantes

        todos_faltantes = []
        for lista in self.lista_comentarios.values():
            todos_faltantes.extend(lista)
        conteo = dict(Counter(todos_faltantes))
        data_ordenada["Contadores"] = conteo

        guardar_json(data_ordenada, cache_dir, ARCHIVO_FALTANTES)