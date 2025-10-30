# bot/pages/customers_create_confirm_modal.py
from __future__ import annotations

import time
from typing import Tuple, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger


class CustomersCreateConfirmModal:
    """
    Maneja el modal final 'Creación de cliente' que aparece después de
    'Crear por IdCIF' -> 'Crear Cliente'. En este modal se puede (opcionalmente)
    capturar el correo y se confirma con el botón 'Crear Cliente'.
    """

    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ----------------------
    # Locators (relativos)
    # ----------------------
    def _modal_contents_xpath(self) -> str:
        # Todos los contenidos de modales visibles de ngb (toma siempre el último visible)
        return "//ngb-modal-window//div[contains(@class,'modal-content')]"

    def _confirm_btn(self) -> Tuple[str, str]:
        # Botón 'Crear Cliente' dentro del modal
        return (By.XPATH, ".//button[contains(normalize-space(.),'Crear Cliente')]")

    def _cancel_btn(self) -> Tuple[str, str]:
        return (By.XPATH, ".//button[contains(normalize-space(.),'Cancelar')]")

    def _email_input(self) -> Tuple[str, str]:
        # Input de correo; a veces no tiene type='email', así que usamos varias heurísticas
        # (placeholder, name, aria-label con la palabra 'correo').
        return (
            By.XPATH,
            ".//input[ "
            "translate(@type,'EMAIL','email')='email' or "
            "contains(translate(@placeholder,'CORREO','correo'),'correo') or "
            "contains(translate(@aria-label,'CORREO','correo'),'correo') or "
            "contains(translate(@name,'EMAIL','email'),'email') "
            "]"
        )

    # ----------------------
    # Helpers internos
    # ----------------------
    def _get_visible_modal_content(self, timeout: int = 15) -> WebElement:
        deadline = time.time() + timeout
        last_visible: Optional[WebElement] = None
        while time.time() < deadline:
            contents = self.driver.find_elements(By.XPATH, self._modal_contents_xpath())
            # Escoge el último que esté displayed
            visibles = [c for c in contents if c.is_displayed()]
            if visibles:
                last_visible = visibles[-1]
                return last_visible
            time.sleep(0.15)
        raise TimeoutError("No se encontró un modal visible de confirmación ('Creación de cliente').")

    def _wait_visible_inside(
        self,
        container: WebElement,
        locator: Tuple[str, str],
        timeout: int = 10
    ) -> WebElement:
        deadline = time.time() + timeout
        by, sel = locator
        while time.time() < deadline:
            try:
                el = container.find_element(by, sel)
                if el.is_displayed():
                    return el
            except Exception:
                pass
            time.sleep(0.2)
        raise TimeoutError(f"Elemento no visible dentro del modal: {locator!r}")

    def _wait_modal_closed(self, timeout: int = 15) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            contents = self.driver.find_elements(By.XPATH, self._modal_contents_xpath())
            visibles = [c for c in contents if c.is_displayed()]
            if not visibles:
                return True
            time.sleep(0.2)
        return False

    # ----------------------
    # API pública
    # ----------------------
    def assert_open(self, timeout: int = 15) -> None:
        """
        Verifica que el modal esté presente/visible y que exista el botón 'Crear Cliente'.
        """
        content = self._get_visible_modal_content(timeout=timeout)
        self._wait_visible_inside(content, self._confirm_btn(), timeout=timeout)
        logger.info("Modal 'Creación de cliente' visible.")

    def click_confirm(self, timeout: int = 20) -> bool:
        """
        Deja el correo vacío (si existe el input) y hace clic en 'Crear Cliente'.
        Regresa True si el modal se cerró.
        """
        content = self._get_visible_modal_content(timeout=timeout)

        # Dejar el correo vacío si encontramos el input (opcional)
        try:
            email_el = self._wait_visible_inside(content, self._email_input(), timeout=3)
            # Limpia cualquier residuo y NO escribimos nada (requisito del cliente)
            try:
                email_el.clear()
            except Exception:
                pass
        except Exception:
            # No pasa nada si no se encontró; algunos casos podrían no mostrar el input
            logger.debug("Input de correo no localizado; continuamos.")

        # Click en 'Crear Cliente' con fallback JS
        btn = self._wait_visible_inside(content, self._confirm_btn(), timeout=timeout)
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.1)
        except Exception:
            pass

        try:
            btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", btn)

        logger.info("Clic en 'Crear Cliente' (confirmación final). Esperando cierre del modal…")
        closed = self._wait_modal_closed(timeout=timeout)
        if closed:
            logger.success("Modal de confirmación cerrado. Cliente creado (según UI).")
        else:
            logger.warning("El modal de confirmación no se cerró tras 'Crear Cliente'.")
        return closed

    def confirm_without_email(self, timeout: int = 20) -> bool:
        """
        Azúcar sintáctica: assert + click_confirm.
        """
        self.assert_open(timeout=timeout)
        return self.click_confirm(timeout=timeout)
