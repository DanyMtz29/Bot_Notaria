#imports independientes
import time, string, random
from datetime import datetime

#imports de selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

#imports mios
from Bot.helpers.logs import registrar_log
from Bot.helpers.json import guardar_json
from Bot.ui_selenium.pages.base import Base
from Bot.ui_selenium.pages.clients_page import ClientsPage
from Bot.ui_selenium.pages.customer_detail_page import CustomerDetailPage
from Bot.ui_selenium.pages.uif_modal import UifModal
from Bot.ui_selenium.pages.customers_cif_modal import CustomersCifModal
from Bot.ui_selenium.pages.customers_create_confirm_modal import CustomersCreateConfirmModal

class Cliente(Base):
    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self.CP = ClientsPage(driver,wait)
        self.carpeta_logs_acto = ""

    def procesar_partes(self, clientes: list, CARPETA_LOGS: str, ruta_proyecto: str):
        self.carpeta_logs_acto = CARPETA_LOGS
        clientes_nuevos = []
        for cl in clientes:
            self.CP.open_direct(self.url)
            self.CP.assert_loaded()
            try:
                tacha = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'sin-btn-close')]/i[contains(@class,'fa-times')]")))
                tacha.click()
                time.sleep(2)
            except Exception:
                pass
            registrar_log(self.carpeta_logs_acto, f"Procesando cliente '{cl.nombre}'.")
            print(f"Procesando cliente '{cl.nombre}'.")
            reintentar =  self.procesar_cliente(cl,clientes_nuevos)
            if reintentar: #Significa que se creo manual y se procesa de nuevo
                self.procesar_cliente(cl, clientes_nuevos)
        if len(clientes_nuevos)>0:
            guardar_json({"Clientes Creados Manualmente": clientes_nuevos}, ruta_proyecto, "Clientes Nuevos.json")

        registrar_log(self.carpeta_logs_acto, "DESCARGADAS LISTAS UIF CORRESPONDIENTES COMPLETO", "SUCCESS")

    def procesar_cliente(self, cliente, clientes_nuevos) -> bool:
        self.CP.open_direct(self.url)
        self.CP.assert_loaded()

        time.sleep(1)
        found = None
        if  cliente.rfc :
            found = self.CP.search_by_name(cliente.rfc, timeout=12)
            time.sleep(1)
        if (not found) and cliente.nombre:
            print(f"No encontrado por rfc: {cliente.rfc}")
            found = self.CP.search_by_name(cliente.nombre, timeout=12)
            time.sleep(1)

        time.sleep(1)
        if found:
            print(f"Cliente EXISTE en Singrafos: {cliente.nombre}")
            nombre = self.driver.find_element(By.XPATH, "//div[contains(@class,'k-grid-content')]//table//tr[1]/td[1]")
            cliente.nombre = nombre.text.upper()
            self._descargar_uif_existente(cliente)
            registrar_log(self.carpeta_logs_acto,f"DESCARGADA LISTA UIF DE {cliente.nombre}")
        else:
            registrar_log(self.carpeta_logs_acto,f"INTENTANDO CREAR CLIENTE {cliente.nombre}")
            print(f"Cliente NO existe, creando por IdCIF... [{cliente.idcif}]")
            if self._crear_cliente_por_idcif(cliente):
                self._descargar_uif_existente(cliente)
                registrar_log(self.carpeta_logs_acto,f"CLIENTE {cliente.nombre} CREADO CORRECTAMENTE Y UIF DESCARGADA CORRECTAMENTE")
            else:
                #Indicando que no se pudo obtener el cliente
                rfc_escaneado = cliente.rfc
                idcif_escaneado = cliente.idcif
                if self.crear_cliente_manual(cliente):
                    registrar_log(self.carpeta_logs_acto, "CLIENTE CREADO MANUALMENTE EXITOSAMENTE!")
                    #Guardar los clientes creados en el portal automaticamente
                    data = {
                        "Nombre (s)": cliente.nombre,
                        "Primer Apellido:": cliente.primer_apellido,
                        "Segundo Apellido:": cliente.segundo_apellido,
                        "RFC Encontrado en CSF": rfc_escaneado,
                        "IDCIF Encontrado en CSF": idcif_escaneado,
                        "RFC Colocado en el portal": cliente.rfc,
                        "IDCIF Colocado en el portal": cliente.idcif
                    }
                    clientes_nuevos.append(data)
                    time.sleep(1)
                    return True
                else:
                    cliente.unknown = True
                    registrar_log(self.carpeta_logs_acto, f"CLIENTE {cliente.nombre} NO SE PUDO CREAR", "ERROR")

        return False

    def _descargar_uif_existente(self, cliente):
        self.CP.click_first_view()
        self.wait.until(
        EC.text_to_be_present_in_element((By.XPATH,"//h4[contains(@class,'page-title')]""//small[contains(@class,'fw-lighter')]"),cliente.nombre))

        cdp = CustomerDetailPage(self.driver, self.wait)
        cdp.click_busqueda_uif(timeout=20)

        boton_hist = self._obtener_boton_hist()

        self.wait.until(EC.element_to_be_clickable(boton_hist))
        boton_hist.click()
        time.sleep(3)

        pdf = UifModal(self.driver, self.wait).renombrar_ultimo_pdf(self.carpeta_logs_acto)
        if pdf:
            cliente.uif = pdf

        self.CP.open_direct(self.url)
        self.CP.assert_loaded()     

    def _obtener_boton_hist(self):
        XPATH_HIST = "//button[contains(@class, 'btn-light') and contains(., 'Comprobante Histórico')]"
        XPATH_BUSCAR = "//button[contains(@class, 'btn-primary') and contains(., 'Buscar de nuevo')]"

        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, XPATH_HIST)))
            botones = self.driver.find_elements(By.XPATH, XPATH_HIST)
            return botones[-1]  # último
        except:
            buscar_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_BUSCAR)))
            buscar_btn.click()

            self.wait.until(EC.presence_of_element_located((By.XPATH, XPATH_HIST)))
            time.sleep(1.5)
            botones = self.driver.find_elements(By.XPATH, XPATH_HIST)
            return botones[-1]

    def _crear_cliente_por_idcif(self, cliente) -> bool:
        try:
            self.CP.click_new()
            self.CP.click_crear_por_idcif()

            modal = CustomersCifModal(self.driver, self.wait)
            modal.fill_and_consult(cliente.rfc.strip(),cliente.idcif.strip())

            if self.check_incorrecto():
                registrar_log(self.carpeta_logs_acto,f"No se pudo crear el cliente con los siguientes datos: \
                            Nombre: {cliente.nombre}\
                            RFC: {cliente.rfc}\
                            IDCIF: {cliente.idcif}\
                            Error: No se pudo obtener informacion del SAT", "ERROR")
                btn_close = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//ngb-modal-window//button[@class='btn-close']")))
                btn_close.click()
                return False

            modal.click_create_customer(timeout=25)
            confirm = CustomersCreateConfirmModal(self.driver, self.wait)
            confirm.confirm_without_email(timeout=25)
            return True
        except Exception as e:
            #Que cargue de nuevo por si se quedó cargando el portal
            self.CP.open_direct(self.url)
            self.CP.assert_loaded()     
            self.CP.click_new()
            #================DESCONGELAR PORTAL==================    
            registrar_log(self.carpeta_logs_acto, f"No se pudo completar creación automática: {e}", "WARNING")
            return False


    def _safe_pdf_name(self, cliente) -> str:
        base = f"{cliente.tipo}_{cliente.rol}_{cliente.nombre}".strip("_")
        cleaned = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in base)
        return cleaned.replace("  ", " ").replace(" ", "_")
    
    def check_incorrecto(self) -> bool:
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"//div[@id='toast-container']//div[contains(@class,'toast')]//div[contains(.,'Información incorrecta')]")))
            return True
        except Exception:
            return False
        
    def crear_cliente_manual(self, cliente) -> bool:
        try:
            close_btn = self.driver.find_element(By.XPATH,"//div[contains(@class,'modal-header')]//button[contains(@class,'btn-close')]")
            close_btn.click()
        except Exception:#Por si no aparece la ventana de crear por idcif o se quitó
            pass
        if cliente.tipo == "PF":
            if self.crearPersonaFisica(cliente):
                time.sleep(2)
                return True
        else:
            if self.crearPersonaMoral(cliente):
                time.sleep(2)
                return True
        time.sleep(2)
        return False

    def generar_rfc_unico(self) -> str:
        letras = string.ascii_uppercase

        parte1 = ''.join(random.choice(letras) for _ in range(4))

        ahora = datetime.now().strftime("%d%H%M")  # 6 dígitos
        parte2 = ahora

        parte3 = ''.join(random.choice(letras) for _ in range(3))

        rfc = parte1 + parte2 + parte3

        return rfc

    def presionar_guardar(self):
        btn_crear_idcif = self.driver.find_element(By.XPATH,"//button[contains(@class,'btn-primary')][contains(.,'Guardar')]")
        btn_crear_idcif.click()

    def crearPersonaFisica(self, cliente) -> bool:
        # Seleccionar tipo de cliente PF
        persona_fisica = self.driver.find_element(By.XPATH, "//input[@id='naturalPerson']")
        persona_fisica.click()

        try: 
            # Nombre(s)
            self.driver.find_element(By.XPATH,"//kendo-autocomplete[@id='firstName']//input[contains(@class,'k-input-inner')]").send_keys(cliente.nombre_s)
            # Apellidos normales
            self.driver.find_element(By.XPATH, "//input[@id='lastName']").send_keys(cliente.primer_apellido)
            self.driver.find_element(By.XPATH, "//input[@id='lastName2']").send_keys(cliente.segundo_apellido)
            # RFC
            temp_rfc = self.generar_rfc_unico()
            self.driver.find_element(By.XPATH, "//input[@id='rfc']").send_keys(temp_rfc)
            cliente.rfc = temp_rfc
            # idCIF
            temp_idcif = datetime.now().strftime("%Y%m%d%H%M%S")
            self.driver.find_element(By.XPATH, "//input[@id='cifId']").send_keys(temp_idcif)
            cliente.idcif = temp_idcif
            # Guardar
            self.presionar_guardar()
            return True
        except Exception as e:
            registrar_log(self.carpeta_logs_acto, f"No se pudo crear el cliente manualmente: Error {e}")
            return False

    def crearPersonaMoral(self,cliente) -> bool:
        try:
            persona_fisica = self.driver.find_element(By.XPATH, "//input[@id='legalPerson']")
            persona_fisica.click()
            #NOmbre
            razon = self.driver.find_element(By.XPATH,"//label[contains(.,'Razón Social')]/following::input[contains(@class,'k-input-inner')][1]")
            razon.clear()
            razon.send_keys(cliente.nombre)
            #RFC y idcif
            temp_rfc = self.generar_rfc_unico()
            self.driver.find_element(By.XPATH, "//input[@id='rfc']").send_keys(temp_rfc)
            cliente.rfc = temp_rfc
            temp_idcif = datetime.now().strftime("%Y%m%d%H%M%S")
            self.driver.find_element(By.XPATH, "//input[@id='cifId']").send_keys(temp_idcif)
            cliente.idcif = temp_idcif

            #Presionar contactos
            self.driver.find_element(By.XPATH,"//h5[contains(.,'Contactos')]/following::button[contains(@class,'btn-primary')][1]").click()
            #Rellenar nombre
            nombre = self.driver.find_element(By.XPATH,"//label[contains(.,'Nombre')]/following::input[contains(@class,'k-input-inner')][1]")
            nombre.clear()
            nombre.send_keys("Contacto")
            #Rellenar apellido
            primer_apellido = self.driver.find_element(By.XPATH,"//input[@id='lastName']")
            primer_apellido.clear()
            primer_apellido.send_keys("Principal")
            #Rellenar RFC
            self.driver.find_element(By.XPATH,"//input[@id='rfc']").send_keys(self.generar_rfc_unico())
            # Clic en Agregar
            self.driver.find_element(By.XPATH, "//button[contains(@class,'btn-outline-success')][contains(.,'Agregar')]").click()
            return True
        except Exception as e:
            return False
