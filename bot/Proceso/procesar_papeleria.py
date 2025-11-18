
from bot.utils.common_imports import *
from bot.utils.selenium_imports import *
from bot.utils.base import Base

from bot.pages.Proyectos.tap_comentarios import comentariosTab
from collections import OrderedDict, Counter
import json

class Documentos(Base):
    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self.lista_comentarios = {}

    def esperar_subida(self):
        #oculto = driver.find_element(By.XPATH,"//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")
        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'col-md-8') and contains(@class,'ms-2')][.//strong[normalize-space()='1']]")))
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")))
        # print("CHECAR OCULTO: ")
        # print(oculto.get_attribute("outerHTML"))

    def subir_lista_uifs(self, listas_uif: list) -> None:
        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")

        #Listas_uifs de prueba
        # listas_uif = [["UIF_PF_Enajenante_ALFREDO_ALBERTO_PALACIOS_RODRIGUEZ.pdf",r"C:\Users\mdani\OneDrive\Desktop\Botbi\Bot Notaria Publica 84\bot\_cache_bot\UIF_PF_Enajenante_ALFREDO_ALBERTO_PALACIOS_RODRIGUEZ.pdf"],
        #             ["UIF_PF_Adquiriente_JUAN_ANTONIO_MURRA_GONZALEZ.pdf", r"C:\Users\mdani\OneDrive\Desktop\Botbi\Bot Notaria Publica 84\bot\_cache_bot\UIF_PF_Adquiriente_JUAN_ANTONIO_MURRA_GONZALEZ.pdf"]]
        
        for uif in listas_uif:
            inp.send_keys(uif[1])
            #time.sleep(3)
            self.esperar_subida()
            #Seleccionar la fila del archivo que se subio
            #fila = self.driver.find_element(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'{uif[0]}')] or .//*[contains(normalize-space(),'{uif[0]}')]]")
            filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
            fila = filas[-1]
            #Seleccionar la columan 2, que es el 'Documento' y establecer que tipo de documento
            Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text("Consulta UIF Lista Negra")
            #Seleccionar el cliente que corresponde esa papeleria
            self.driver.execute_script("arguments[0].value = '';", inp)#Remover los elementos anteriores
            time.sleep(1)

    def subir_doc_inmuebles(self, inmuebles: list, doc:str) -> bool:
        """
            Sube solo los docus de los inmuebles
        """

        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
        flag = True
        for inm in inmuebles:
            doc_path = inm.get(doc)
            if doc_path != None:
                inp.send_keys(doc_path)
                self.esperar_subida()
                filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//a[contains(@title,'.pdf')] or .//*[contains(normalize-space(),'.pdf')]]")
                fila = filas[-1]
                Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc)
                self.driver.execute_script("arguments[0].value = '';", inp)
                time.sleep(1)
            else:
                #add_coment(inm.get_name(), doc)
                tup = ("INM",inm.get_name(), 'INM')
                if tup in self.lista_comentarios:
                    self.lista_comentarios[tup].append(doc)
                else:
                    self.lista_comentarios[tup] = [doc]
                flag = False
        return flag

    def subir_doc_partes_basicas(self,clientes: list, doc: str) -> None:
        """
            Sube solo los docus basicos de las partes: CURP, ACTA DE NACIMIENTO, COMP_DOM, CSF, INE
        """
        doc_original = doc
        if doc == "Comprobante de Domicilio (compareciente o partes)": doc = "COMP_DOMICILIO"
        elif doc == "Identificación oficial (compareciente o partes)": doc = "INE"
        elif doc == "Acta de nacimiento (compareciente o partes)": doc = "ACTA_NAC"
        elif doc == "Constancia de identificación fiscal (compareciente o partes)": doc = "CSF"
        elif doc == "CURP (compareciente o partes)": doc = "CURP"
        elif doc == "Acta de matrimonio (compareciente o partes)": doc = "ACTA_MATRIMONIO"

        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")
        flag = True
        for part in clientes:

            if part.get("tipo") == "PM":
                part = part.get("representante", {})
                #Primero chechar si no esta en importados

            if self.checar_docs_importar(part.get("nombre"), doc_original):
                time.sleep(1)
            else:
                docs = part.get("docs")
                doc_up = docs.get(doc)
                if doc_up == None:
                    if not doc == "COMP_DOMICILIO" and doc == "ACTA_MATRIMONIO":
                        #add_coment(part.get("nombre"), doc_original)
                        tup = ("PF",part.get("nombre"), part.get('rol'))
                        if tup in self.lista_comentarios:
                            self.lista_comentarios[tup].append(doc_original)
                        else:
                            self.lista_comentarios[tup] = [doc_original]
                        flag = False
                else:
                    inp.send_keys(doc_up)
                    self.esperar_subida()
                    filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//*[contains(normalize-space(),'.pdf')]]")
                    fila = filas[-1]
                    Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(doc_original)
                    Select(fila.find_element(By.XPATH, ".//td[3]//select")).select_by_visible_text(part.get("nombre"))
                    self.driver.execute_script("arguments[0].value = '';", inp)
                    time.sleep(1)
        return flag
    
    def checar_docs_importar(self,cliente: str, doc: str) -> bool:
        wait = WebDriverWait(self.driver, 20)

        # Click en "Importar" (usa wait + JS por si hay overlay)
        but = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")))
        self.driver.execute_script("arguments[0].click();", but)

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
            self.driver.execute_script("arguments[0].click();", cerrar)
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
                self.driver.execute_script("arguments[0].click();", cb)
                break
            except StaleElementReferenceException:
                if i == attempts - 1:
                    raise  # ya no reintentes
                # pequeño backoff opcional:
                # time.sleep(0.2)
                continue

        # Cierra el modal
        cerrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space()='Regresar']")))
        self.driver.execute_script("arguments[0].click();", cerrar)
        return True

    def procesamiento_papeleria(self,documents: list,docs, partes:list, inmuebles: list, listas_uif: list):
        """
            PROCESAMIENTO DE TODOS LOS DOCUMENTOS A SUBIR JUNTO CON SELENIUM
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
                self.subir_lista_uifs(listas_uif)
                #Marcar como hecho la lista_uif
                docs.set_faltante_by_description(doc, marcar=True)
            elif doc in papeleria_basica:
                if self.subir_doc_partes_basicas(partes, doc):
                    docs.set_faltante_by_description(doc, marcar=True)
            if doc in papeleria_inmuebles:
                if self.subir_doc_inmuebles(inmuebles,doc):
                    docs.set_faltante_by_description(doc, marcar=True)
        
        but = self.driver.find_element(By.XPATH,f"//div[@class='col-md-10']//div[@class='text-end']//button[@type='button']")
        self.driver.execute_script("arguments[0].click();", but)
        time.sleep(1) 
        but_seleccionar = self.driver.find_element(By.XPATH, "//div[contains(@class, 'modal-footer')]//button[normalize-space(text())='Importar Seleccionados']")
        self.driver.execute_script("arguments[0].click();", but_seleccionar)

    def comentarios_y_guardar_proyecto(self, cache_dir, descripcion, escritura, cliente, abogado):
        comentarios_tab = comentariosTab(self.driver,self.wait)
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
                comentarios_tab.enviar_comentario()
                time.sleep(1)
        comentarios_tab.guardar_proyecto()
        time.sleep(2)
        
        try:
            folio = comentarios_tab.get_folio("\"PRUEBAS BOTBI\" " + descripcion)
        except Exception as e:
            logger.error("NO se pudo capturar el folio en el proyecto: {}",e)

        self.guardar_papeleria_JSON(cache_dir, "\"PRUEBAS BOTBI\" " + descripcion, folio, escritura, cliente, abogado)

    def guardar_papeleria_JSON(self,ruta: str, descripcion: str, folio:str, escritura: str, cliente: str, abg:str):
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
        data_ordenada["Folio"] = folio
        data_ordenada["Escritura"] = escritura
        data_ordenada["Descripcion del proyecto"] = descripcion
        data_ordenada["Cliente"] = cliente
        data_ordenada["Abogado"] = abg

        # Guardar faltantes por cada parte
        for k, v in self.lista_comentarios.items():
            data_ordenada[str(k)] = v

        # === NUEVO: calcular conteo general de todos los faltantes ===
        todos_faltantes = []
        for lista in self.lista_comentarios.values():
            todos_faltantes.extend(lista)
        conteo = dict(Counter(todos_faltantes))
        data_ordenada["Contadores"] = conteo

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data_ordenada, f, indent=4, ensure_ascii=False)

        logger.info("Papelería guardada con contadores en: {}", ruta)