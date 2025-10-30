from __future__ import annotations

from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

class UifModal:
    """
    Interacciones dentro del modal 'Búsqueda UIF'.

    Flujo:
      1) click 'Buscar de nuevo' (arriba derecha)
      2) esperar que aparezca el botón gris 'Descargar Comprobante' dentro del grid
      3) click en ese botón gris (NO el azul de arriba)
    """

    def __init__(self, driver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ---------- Selectors de raíz ----------
    def _root(self):
        # <ngb-modal-window class="d-block modal fade show" ...>
        return (By.CSS_SELECTOR, "ngb-modal-window.d-block.modal.show")

    # scope helper: busca dentro del modal abierto
    def _within_root(self, by_tuple):
        root = self.wait.until(EC.presence_of_element_located(self._root()))
        return root.find_element(*by_tuple)

    # ---------- Selectors específicos ----------
    def _btn_buscar_de_nuevo(self):
        # Botón de header (clase 'btn btn-sm btn-primary ms-1'), texto 'Buscar de nuevo'
        return (By.XPATH, ".//button[contains(normalize-space(.),'Buscar de nuevo')]")

    def _btn_descargar_grid(self):
        # Botón GRIS dentro del grid Kendo, texto 'Descargar Comprobante'
        # Evitamos el azul del header filtrando por 'btn-light' o yendo por el grid directamente.
        return (
            By.XPATH,
            ".//kendo-grid//button[contains(@class,'btn-light') and "
            "contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ',"
            "'abcdefghijklmnopqrstuvwxyzáéíóúü'),"
            "'descargar comprobante')]",
        )

    # Alternativa por si el DOM cambia y el botón no trae 'btn-light'
    def _btn_descargar_grid_relaxed(self):
        return (
            By.XPATH,
            ".//kendo-grid//button[contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜ',"
            "'abcdefghijklmnopqrstuvwxyzáéíóúü'),"
            "'descargar comprobante')]",
        )

    # ---------- Utils ----------
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

    # ---------- API ----------
    def click_buscar_de_nuevo(self, timeout: int = 20):
        modal = self.wait.until(EC.visibility_of_element_located(self._root()))
        btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, self._btn_buscar_de_nuevo()[1]))
        )
        self._click_smart(btn)
        logger.info("Clic en 'Buscar de nuevo'.")

    def esperar_boton_descargar(self, timeout: int = 60):
        """
        Espera a que aparezca el botón *gris* 'Descargar Comprobante' en el grid.
        """
        try:
            el = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, self._btn_descargar_grid()[1]))
            )
            logger.info("Botón gris 'Descargar Comprobante' detectado (estricto).")
            return el
        except TimeoutException:
            # Intento relajado por si cambian las clases
            el = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, self._btn_descargar_grid_relaxed()[1])
                )
            )
            logger.info("Botón 'Descargar Comprobante' detectado (relajado).")
            return el

    def click_descargar_comprobante(self, timeout: int = 10):
        el = self.esperar_boton_descargar(timeout=timeout)
        self._click_smart(el)
        logger.info("Clic en botón gris 'Descargar Comprobante' dentro del grid.")

    def buscar_de_nuevo_y_descargar(
        self, timeout_busqueda: int = 40, timeout_descarga: int = 60
    ):
        """
        Secuencia completa pedida:
        - Clic en 'Buscar de nuevo'
        - Espera a que aparezca el botón de descarga del grid
        - Clic en 'Descargar Comprobante' (gris)
        """
        self.click_buscar_de_nuevo(timeout=timeout_busqueda)
        self.click_descargar_comprobante(timeout=timeout_descarga)
