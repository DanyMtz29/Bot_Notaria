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
        self.lista_uifs = []

    def procesar_partes(self, partes) -> list[str]:
        for idx, party in enumerate(partes, start=1):
            if party.get('tipo') == "PM":
                self.procesar_cliente(party.get("representante"))
            self.procesar_cliente(party)
        return self.lista_uifs

    def procesar_cliente(self, party) -> None:
        self.CP.open_direct(self.url)
        self.CP.assert_loaded()

        time.sleep(1)
        found = self.CP.search_by_name(party["nombre_upper"], timeout=12)
        time.sleep(1)
        if found:
            logger.info("Cliente EXISTE en Singrafos: {}", party["nombre_upper"])
            self._descargar_uif_existente(party)
        else:
            logger.info("Cliente NO existe, creando por IdCIF... [{}]", party.get("idcif", "sin IdCIF"))
            self._crear_cliente_por_idcif(party)
            self._descargar_uif_existente(party)


    def _descargar_uif_existente(self, party):
        self.CP.click_first_view()
        logger.info("Detalle de cliente abierto (lupita).")

        self.wait.until(
        EC.text_to_be_present_in_element((By.XPATH,"//h4[contains(@class,'page-title')]""//small[contains(@class,'fw-lighter')]"),party["nombre_upper"]))

        cdp = CustomerDetailPage(self.driver, self.wait)
        cdp.click_busqueda_uif(timeout=20)

        boton_hist = self._obtener_boton_hist()

        self.wait.until(EC.element_to_be_clickable(boton_hist))
        boton_hist.click()
        time.sleep(3)

        nombre_pdf = self._safe_pdf_name(party)
        pdf = UifModal(self.driver, self.wait).renombrar_ultimo_pdf(nombre_pdf)
        self.lista_uifs.append(pdf)

        logger.success("UIF descargado y renombrado.")

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

    def _crear_cliente_por_idcif(self, party):
        self.CP.click_new()
        logger.success("Formulario 'Nuevo Cliente' abierto.")

        self.CP.click_crear_por_idcif()
        logger.success("Flujo 'Crear por IdCIF' abierto.")

        modal = CustomersCifModal(self.driver, self.wait)
        modal.fill_and_consult(
            (party.get("rfc") or "").strip(),
            (party.get("idcif") or "").strip()
        )

        try:
            modal.click_create_customer(timeout=25)
            confirm = CustomersCreateConfirmModal(self.driver, self.wait)
            confirm.confirm_without_email(timeout=25)
            logger.success("Cliente creado por IdCIF.")
        except Exception as e:
            logger.warning(f"No se pudo completar creación automática: {e}")


    def _safe_pdf_name(self, party: Dict[str, str]) -> str:
        base = f"{party.get('tipo','')}_{party.get('rol','')}_{party.get('nombre_upper','')}".strip("_")
        # Limpia caracteres raros para nombre de archivo
        cleaned = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in base)
        return cleaned.replace("  ", " ").replace(" ", "_")