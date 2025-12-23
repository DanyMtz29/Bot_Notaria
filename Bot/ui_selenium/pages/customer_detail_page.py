#Imports selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
)

class CustomerDetailPage:
    """
    Página de detalle del cliente.
    Aquí vive el botón 'Búsqueda UIF' que abre el modal.
    """

    def __init__(self, driver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ---------- Selectors ----------
    def _btn_busqueda_uif(self):
        # Botón en la página de detalle que abre el modal
        # Localizamos por el texto visible.
        return (By.XPATH, "//button[contains(normalize-space(.),'Búsqueda UIF')]")

    def _title(self):
        # Algo muy estable en la página de detalle (puede variar entre deploys),
        # pero el botón de búsqueda UIF siempre está allí; usamos eso como
        # 'proof-of-life' de la página.
        return self._btn_busqueda_uif()

    def _modal_root(self):
        # Raíz del modal Ngb (observado en el DOM)
        # <ngb-modal-window class="d-block modal fade show" ...>
        return (By.CSS_SELECTOR, "ngb-modal-window.d-block.modal.show")

    # ---------- Utils ----------
    def _click_smart(self, el):
        try:
            el.click()
            return
        except (ElementClickInterceptedException, StaleElementReferenceException):
            pass
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.driver.execute_script("arguments[0].click();", el)
        

    # ---------- API ----------
    def assert_loaded(self, timeout: int = 12) -> None:
        # Asegura que estamos en el detalle (al menos el botón UIF existe)
        self.wait.until(EC.presence_of_element_located(self._title()))
        self.wait.until(EC.presence_of_element_located(self._btn_busqueda_uif()))

    def click_busqueda_uif(self, timeout: int = 15) -> None:
        """
        Da clic al botón 'Búsqueda UIF' y espera a que el modal se muestre.
        """
        self.assert_loaded(timeout=timeout)
        btn = self.wait.until(EC.element_to_be_clickable(self._btn_busqueda_uif()))
        self._click_smart(btn)
        print("Abriendo modal 'Búsqueda UIF'…")

        # Esperar la presencia + visibilidad del modal ngb
        self.wait.until(EC.presence_of_element_located(self._modal_root()))
        self.wait.until(EC.visibility_of_element_located(self._modal_root()))
        print("Modal 'Búsqueda UIF' visible.")
