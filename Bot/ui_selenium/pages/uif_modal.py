#Imports independientes
from loguru import logger
import glob, os, time, shutil

#Imports selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException,StaleElementReferenceException,ElementClickInterceptedException,)
from selenium.webdriver.remote.webdriver import WebDriver

#Imports mios
from Bot.constantes.rutas import RUTA_TEMPORALES
from Bot.helpers.logs import registrar_log


class UifModal:

    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ----------------------
    # Selectores de contexto
    # ----------------------
    def _root(self):
        # <ngb-modal-window class="d-block modal fade show" ...>
        return (By.CSS_SELECTOR, "ngb-modal-window.d-block.modal.show")

    def _within_root(self, by_tuple):
        root = self.wait.until(EC.presence_of_element_located(self._root()))
        return root.find_element(*by_tuple)

    # ----------------------
    # Selectores específicos
    # ----------------------
    def _btn_buscar_de_nuevo(self):
        # Botón de header (clase 'btn btn-sm btn-primary ms-1'), texto 'Buscar de nuevo'
        return (By.XPATH, ".//button[contains(normalize-space(.),'Buscar de nuevo')]")

    def _btn_descargar_grid(self):
        # Botón GRIS dentro del kendo-grid (no confundir con el azul del header)
        return (
            By.XPATH,
            ".//kendo-grid//button[contains(@class,'btn-light') and "
            "contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ',"
            "'abcdefghijklmnopqrstuvwxyzáéíóúü'),"
            "'Comprobante Histórico')]",
        )

    def _btn_descargar_grid_relaxed(self):
        # Variante si cambian estilos y ya no trae 'btn-light'
        return (
            By.XPATH,
            ".//kendo-grid//button[contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ',"
            "'abcdefghijklmnopqrstuvwxyzáéíóúü'),"
            "'Comprobante Histórico')]",
        )

    # ----------------------
    # Utilidades
    # ----------------------
    def _click_smart(self, el):
        try:
            el.click()
            return
        except (ElementClickInterceptedException, StaleElementReferenceException):
            pass
        # Fallback con JS
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", el
        )
        self.driver.execute_script("arguments[0].click();", el)

    # ----------------------
    # API
    # ----------------------
    def click_buscar_de_nuevo(self, timeout: int = 20):
        # Asegura que el modal esté visible y haz click en el botón azul
        self.wait.until(EC.visibility_of_element_located(self._root()))
        btn = self.wait.until(
            EC.element_to_be_clickable(self._btn_buscar_de_nuevo())
        )
        self._click_smart(btn)

    def esperar_boton_descargar(self, timeout: int = 60):
        """
        Espera a que aparezca (y sea clickable) el botón *gris* 'Descargar Comprobante'
        del grid. Primero intenta con selector estricto (btn-light) y después relajado.
        """
        try:
            el = WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(
                EC.element_to_be_clickable(self._btn_descargar_grid())
            )
            return el
        except TimeoutException:
            el = WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(
                EC.element_to_be_clickable(self._btn_descargar_grid_relaxed())
            )
            return el

    def existe_boton_descargar(self, timeout_check: int = 3) -> bool:
        """
        Revisa RÁPIDO si ya existe el botón gris en el grid (sin lanzar excepción).
        Devuelve True si se encuentra, False si no.
        """
        self.wait.until(EC.visibility_of_element_located(self._root()))
        try:
            WebDriverWait(self.driver, timeout_check, poll_frequency=0.2).until(
                EC.presence_of_element_located(self._btn_descargar_grid())
            )
            return True
        except TimeoutException:
            try:
                WebDriverWait(self.driver, timeout_check, poll_frequency=0.2).until(
                    EC.presence_of_element_located(self._btn_descargar_grid_relaxed())
                )
                return True
            except TimeoutException:
                return False

    def click_descargar_comprobante(self, timeout: int = 60):
        el = self.esperar_boton_descargar(timeout=timeout)
        self._click_smart(el)

    def buscar_de_nuevo_y_descargar(
        self, timeout_busqueda: int = 40, timeout_descarga: int = 60, timeout_check: int = 3
    ):
        """
        NUEVA LÓGICA:
          - Si YA hay botón gris de 'Descargar Comprobante', descárgalo DIRECTO.
          - Si NO hay, entonces click en 'Buscar de nuevo' y luego descargar.
        """
        # 1) ¿Ya está el botón de descarga listo?
        if self.existe_boton_descargar(timeout_check=timeout_check):
            self.click_descargar_comprobante(timeout=timeout_descarga)
            return

        # 2) Si no estaba, ejecuta la búsqueda y luego descarga
        #self.click_buscar_de_nuevo(timeout=timeout_busqueda)
        self.click_descargar_comprobante(timeout=timeout_descarga)

    def renombrar_ultimo_pdf(self, carpeta_logs: str):
        time.sleep(3)  # Espera breve para que termine la descarga

        buscar = os.path.join(RUTA_TEMPORALES, "*.pdf")

        archivos = sorted(
            glob.glob(buscar),
            key=os.path.getmtime,
            reverse=True
        )
        if not archivos:
            registrar_log(carpeta_logs,"No se encontró ningún PDF para renombrar.", "ERROR")
            return

        return archivos[0]
