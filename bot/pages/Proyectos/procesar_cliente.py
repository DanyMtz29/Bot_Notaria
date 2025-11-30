from bot.utils.base import Base
from bot.utils.common_imports import *
from bot.utils.selenium_imports import *

from bot.pages.clients_page import ClientsPage
from bot.pages.customer_detail_page import CustomerDetailPage
from bot.pages.uif_modal import UifModal
from bot.pages.customers_cif_modal import CustomersCifModal
from bot.pages.customers_create_confirm_modal import CustomersCreateConfirmModal
from typing import Dict

class Cliente(Base):
    def __init__(self, driver, wait):
        super().__init__(driver, wait)
        self.CP = ClientsPage(driver,wait)

    def procesar_partes(self, partes) -> list[str]:
        clientes = []
        for parte in partes:
            if parte.get("tipo") == "PM":
                clientes.append(parte.get("representante", {}))
            else:
                if parte.get("esposa_o_esposo"):
                    clientes.append(parte.get("esposa_o_esposo", {}))
            clientes.append(parte)

        for cl in clientes:
            self.CP.open_direct(self.url)
            self.CP.assert_loaded()
            try:
                tacha = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'sin-btn-close')]/i[contains(@class,'fa-times')]")))
                tacha.click()
                time.sleep(2)
            except Exception:
                pass
            self.procesar_cliente(cl)
            
        logger.info("DESCARGADAS LISTAS UIF CORRESPONDIENTES COMPLETO")
        
        # for idx, party in enumerate(partes, start=1):
        #     if party.get('tipo') == "PM":
        #         self.procesar_cliente(party.get("representante"))
        #     else:
        #         if party.get("esposa_o_esposo"):
        #             self.procesar_cliente(party.get("esposa_o_esposo"))
        #     self.procesar_cliente(party)

    def procesar_cliente(self, party) -> None:
        self.CP.open_direct(self.url)
        self.CP.assert_loaded()

        time.sleep(1)
        found = self.CP.search_by_name(party["rfc"], timeout=12)
        time.sleep(1)
        if found:
            print("Cliente EXISTE en Singrafos: {}", party["nombre"])
            nombre = self.driver.find_element(By.XPATH, "//div[contains(@class,'k-grid-content')]//table//tr[1]/td[1]")
            party["nombre"] = nombre.text.upper()
            self._descargar_uif_existente(party)
            logger.info(f"DESCARGADA LISTA UIF DE {party["nombre"]}")
        else:
            logger.info(f"INTENTANDO CREAR CLIENTE {party["nombre"]}")
            print("Cliente NO existe, creando por IdCIF... [{}]", party.get("idcif", "sin IdCIF"))
            if not self._crear_cliente_por_idcif(party):
                """
                    Crear cliente manualmente
                    self.crearClienteManual(party)

                    Correccion:
                    VERIFICAR EL TOAST DE INCORRECTO
                """
                
            self._descargar_uif_existente(party)
            logger.info(f"CLIENTE {party["nombre"]} CREADO CORRECTAMENTE Y UIF DESCARGADA CORRECTAMENTE")

    def _descargar_uif_existente(self, party):
        self.CP.click_first_view()
        print("Detalle de cliente abierto (lupita).")

        self.wait.until(
        EC.text_to_be_present_in_element((By.XPATH,"//h4[contains(@class,'page-title')]""//small[contains(@class,'fw-lighter')]"),party["nombre"]))

        cdp = CustomerDetailPage(self.driver, self.wait)
        cdp.click_busqueda_uif(timeout=20)

        boton_hist = self._obtener_boton_hist()

        self.wait.until(EC.element_to_be_clickable(boton_hist))
        boton_hist.click()
        time.sleep(3)

        nombre_pdf = self._safe_pdf_name(party)
        pdf = UifModal(self.driver, self.wait).renombrar_ultimo_pdf(nombre_pdf)
        party["uif"] = pdf[-1]


        # regresar a Clientes
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

    def _crear_cliente_por_idcif(self, party) -> bool:
        self.CP.click_new()

        self.CP.click_crear_por_idcif()

        modal = CustomersCifModal(self.driver, self.wait)
        modal.fill_and_consult(
            (party.get("rfc") or "").strip(),
            (party.get("idcif") or "").strip()
        )

        self.check_incorrecto()

        try:
            modal.click_create_customer(timeout=25)
            confirm = CustomersCreateConfirmModal(self.driver, self.wait)
            confirm.confirm_without_email(timeout=25)
            return True
        except Exception as e:
            logger.warning(f"No se pudo completar creación automática: {e}")
            return False


    def _safe_pdf_name(self, party: Dict[str, str]) -> str:
        base = f"{party.get('tipo','')}_{party.get('rol','')}_{party.get('nombre','')}".strip("_")
        # Limpia caracteres raros para nombre de archivo
        cleaned = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in base)
        return cleaned.replace("  ", " ").replace(" ", "_")
    
    def crearClienteManual(self, party):
        """
            crea el cliente en el portal manualmente por medio de todos los datos que 
            se pueden abstraer
        """
    
    def check_incorrecto(self) -> None:
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"//div[@id='toast-container']//div[contains(@class,'toast')]//div[contains(.,'Información incorrecta')]")))
            print("🔥 Se activó el toast de error del SAT")
        except:
            print("No apareció el toast")
        