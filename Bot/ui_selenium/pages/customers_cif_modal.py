#Imports independientes
import time

#Imports selenium
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait


class CustomersCifModal:
    """
    Maneja el modal 'Crear cliente con IdCIF'.
    """

    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ---------- Locators ----------
    def _modal_windows(self):
        return (By.CSS_SELECTOR, "ngb-modal-window")

    def _modal_content_in(self, modal_window):
        return modal_window.find_element(By.CSS_SELECTOR, ".modal-content")

    def _rfc_locator(self):
        return (By.CSS_SELECTOR, "input#rfc, input[name='rfc']")

    def _idcif_locator(self):
        return (By.CSS_SELECTOR, "input#idCif, input[name='idcif']")

    def _consult_btn_locator(self):
        return (By.XPATH, ".//button[contains(normalize-space(.),'Consultar datos actualizados')]")

    def _create_btn_locator(self):
        # Texto puede variar en mayúsculas/minúsculas
        return (By.XPATH, ".//button[contains(translate(normalize-space(.),'CLIENTE','cliente'),'crear cliente')]")

    def _detail_component_locator(self):
        return (By.CSS_SELECTOR, "app-customers-detail-cif")

    def _loader_locator(self):
        # overlay que aparece al consultar
        return (By.CSS_SELECTOR, "app-loading-screen")

    # ---------- Utils ----------
    def _get_visible_modal_content(self, timeout: int = 15):
        deadline = time.time() + timeout
        last_content = None
        while time.time() < deadline:
            wins = self.driver.find_elements(*self._modal_windows())
            for w in wins[::-1]:
                try:
                    content = self._modal_content_in(w)
                except Exception:
                    continue
                last_content = content
                if content.is_displayed():
                    return content
            time.sleep(0.2)
        raise TimeoutException("Modal 'Crear cliente con IdCIF' no visible.")

    def _wait_visible_inside(self, container, locator, timeout: int = 10):
        by, sel = locator
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                el = container.find_element(by, sel)
                if el.is_displayed():
                    return el
            except Exception:
                pass
            time.sleep(0.2)
        raise TimeoutException(f"Elemento no visible dentro del modal: {locator}")

    def _wait_modal_closed(self, timeout: int = 15) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            wins = self.driver.find_elements(*self._modal_windows())
            if not any(w.is_displayed() for w in wins if w):
                return True
            time.sleep(0.2)
        return False

    def _wait_loader_gone(self, content, timeout: int = 15):
        by, sel = self._loader_locator()
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                overlay = content.find_element(by, sel)
                if overlay.is_displayed():
                    time.sleep(0.2)
                    continue
            except Exception:
                # no está el loader
                return True
            return True
        return True

    # ---------- API ----------
    def assert_open(self, timeout: int = 15):
        content = self._get_visible_modal_content(timeout=timeout)
        self._wait_visible_inside(content, self._rfc_locator(), timeout=timeout)
        self._wait_visible_inside(content, self._idcif_locator(), timeout=timeout)
        return content

    def _click_consult(self, content, timeout: int = 10):
        btn = self._wait_visible_inside(content, self._consult_btn_locator(), timeout=timeout)
        btn.click()

    def _wait_consult_result(self, content, timeout: int = 30) -> bool:
        by, sel = self._detail_component_locator()
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                comp = content.find_element(by, sel)
                if comp.is_displayed():
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def fill_and_consult(self, rfc: str, idcif: str, timeout: int = 25):
        content = self.assert_open(timeout=timeout)

        rfc_el = self._wait_visible_inside(content, self._rfc_locator(), timeout=timeout)
        idcif_el = self._wait_visible_inside(content, self._idcif_locator(), timeout=timeout)

        rfc = (rfc or "").upper().strip()
        idcif = (idcif or "").strip()

        rfc_el.clear()
        if rfc:
            rfc_el.send_keys(rfc)
        idcif_el.clear()
        if idcif:
            idcif_el.send_keys(idcif)

        print(f"Consultando CIF con RFC='{rfc or '-'}' IdCIF='{idcif or '-'}'")
        self._click_consult(content, timeout=timeout)

        # espera resultado + que se haya ido cualquier loader
        self._wait_consult_result(content, timeout=max(10, timeout))
        self._wait_loader_gone(content, timeout=10)

    def click_create_customer(self, timeout: int = 25) -> bool:
        """
        Pulsa 'Crear Cliente' con tolerancia a re-renders, loader y scroll.
        """
        content = self._get_visible_modal_content(timeout=timeout)
        self._wait_loader_gone(content, timeout=10)

        deadline = time.time() + timeout
        candidate = None
        while time.time() < deadline:
            # 1) Busca por texto dentro de cualquier modal visible
            btns = self.driver.find_elements(
                By.XPATH,
                "//ngb-modal-window//button[contains(translate(normalize-space(.),'CLIENTE','cliente'),'crear cliente')]"
            )
            btns = [b for b in btns if b.is_displayed()]

            # 2) Fallback por CSS (clase de éxito en el footer)
            if not btns:
                btns = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "ngb-modal-window .modal-footer .btn.btn-outline-success"
                )
                btns = [b for b in btns if b.is_displayed()]

            if btns:
                candidate = btns[0]
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", candidate)
                    time.sleep(0.15)
                    try:
                        candidate.click()
                    except Exception:
                        # si el click normal falla, intenta click por JS
                        self.driver.execute_script("arguments[0].click();", candidate)
                    print("Clic en 'Crear Cliente'. Esperando cierre del modal…")
                    break
                except Exception as e:
                    # si falló el scroll o algo antes, intenta directo el click por JS
                    try:
                        self.driver.execute_script("arguments[0].click();", candidate)
                        print("Clic vía JS en 'Crear Cliente'. Esperando cierre del modal…")
                        break
                    except Exception as e2:
                        pass

            time.sleep(0.25)

        if candidate is None:
            raise TimeoutException("No se encontró el botón visible 'Crear Cliente' en el modal.")

        closed = self._wait_modal_closed(timeout=timeout)
        # if closed:
        #     logger.success("Modal cerrado. Cliente creado (según la UI).")
        # else:
        #     logger.warning("El modal no se cerró tras 'Crear Cliente'.")
        return closed
