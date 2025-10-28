# bot/pages/projects_page.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from .base_page import BasePage

class ProjectsPage(BasePage):
    # Título / ancla de la vista (sirve para saber que ya cargó)
    TITLE_HINTS = [
        (By.XPATH, "//h1[contains(.,'Proyectos')]"),
        (By.XPATH, "//h2[contains(.,'Proyectos')]"),
        (By.XPATH, "//*[contains(@class,'page-title') and contains(.,'Proyectos')]")
    ]

    # Botón "+ Nuevo" (aceptamos button o <a> con ese texto o un <span> dentro)
    NEW_BUTTONS = [
        (By.XPATH, "//button[contains(normalize-space(),'Nuevo')]"),
        (By.XPATH, "//a[contains(normalize-space(),'Nuevo')]"),
        (By.XPATH, "//*[self::button or self::a][.//span[contains(normalize-space(),'Nuevo')]]"),
        # Fallbacks típicos por estilo
        (By.CSS_SELECTOR, "button.btn.btn-primary"),
        (By.CSS_SELECTOR, "button.k-button.k-primary"),
    ]

    def wait_until_loaded(self):
        # URL y algún elemento propio de la página
        self.wait_for_app_ready(timeout=15)
        self.wait.until(lambda d: "/projects" in d.current_url.lower())
        try:
            self.find_first_fast(self.TITLE_HINTS, per_try=2.0, visible=True)
        except Exception:
            # si no hay título visible, no pasa nada; seguimos con el botón
            pass

    def click_nuevo(self):
        self.wait_until_loaded()
        nuevo = self.find_first_fast(self.NEW_BUTTONS, per_try=2.0, visible=True)
        # Asegura que esté en viewport
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", nuevo)
        # Intenta click normal y si no, JS (por overlays/sticky headers)
        try:
            nuevo.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", nuevo)

        # Espera a que se abra el formulario o cambie la URL (heurísticas comunes)
        def _moved(d):
            u = d.current_url.lower()
            if any(s in u for s in ["/projects/new", "/project/new", "/create"]):
                return True
            # modal/diálogo (Kendo/Bootstrap)
            return d.execute_script(
                "return !!(document.querySelector('.k-window, .modal.show, .modal.in') || "
                "document.querySelector('form input, form select'))"
            )
        self.wait.until(_moved)
