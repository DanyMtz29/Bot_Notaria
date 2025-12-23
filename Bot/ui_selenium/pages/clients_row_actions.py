#Imports independientes
import time
from typing import Tuple

#Import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ClientsRowActions:
    """
    Acciones sobre la primera fila del grid de Clientes (listado).
    Se usa cuando ya verificamos que EXISTE al menos un resultado.
    """

    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ---------------- Locators genéricos (Kendo Grid) ----------------
    def _grid(self) -> Tuple[str, str]:
        return (By.XPATH, "//kendo-grid | //div[contains(@class,'k-grid')]")

    def _first_data_row(self) -> Tuple[str, str]:
        # Primera fila con datos (evita el row 'k-grid-norecords')
        return (
            By.XPATH,
            "(//kendo-grid//tbody//tr[not(contains(@class,'k-grid-norecords'))] "
            "| //div[contains(@class,'k-grid')]//tbody//tr[not(contains(@class,'k-grid-norecords'))])[1]"
        )

    def _detail_anchor_inside_row(self) -> Tuple[str, str]:
        # La 'lupita' suele ser <a ... href="/customers/detail/..."><i class="fas fa-search"></i></a>
        return (
            By.XPATH,
            ".//a[contains(@href,'/customers/detail') or .//i[contains(@class,'fa-search')]]"
        )

    # ---------------- Helpers ----------------
    def _wait_grid_ready(self, timeout: int = 10) -> WebElement:
        grid = self.wait.until(EC.presence_of_element_located(self._grid()))
        # Un respiro breve para que Kendo termine de hidratar
        time.sleep(0.25)
        return grid

    # ---------------- API pública ----------------
    def open_first_row_detail(self, timeout: int = 12) -> None:
        """
        Hace clic en la 'lupita' de la PRIMERA fila del grid y espera a que
        navegue a /customers/detail/...
        """
        self._wait_grid_ready(timeout=timeout)

        row = self.wait.until(EC.presence_of_element_located(self._first_data_row()))
        # Por si la fila aún no está visible
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
        except Exception:
            pass

        # Busca la 'lupita' dentro de la fila
        try:
            lupita = row.find_element(*self._detail_anchor_inside_row())
        except Exception:
            # Si no la encuentra dentro de la fila, probamos a nivel de celda de acciones
            raise Exception("No se encontró la 'lupita' (detalle) dentro de la primera fila.")

        # Click con fallback JS
        try:
            lupita.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", lupita)

        print("Clic en la lupita de la primera fila. Esperando navegación a detalle…")

        # Espera navegación a la URL de detalle
        end = time.time() + timeout
        while time.time() < end:
            try:
                if "/customers/detail" in self.driver.current_url:
                    return
            except Exception:
                pass
            time.sleep(0.2)

        # Como fallback, valida que exista algún contenedor típico del detalle
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//app-customers-detail | //app-customers-detail-cif")
                )
            )
        except Exception:
            raise TimeoutError("No se abrió el detalle del cliente tras clicar la lupita.")
