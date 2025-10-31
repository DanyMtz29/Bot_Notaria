# bot/pages/projects_documents.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from .base_page import BasePage

class ProjectsDocumentsPage(BasePage):
    """
    Acciones relacionadas con la pestaña 'Documentos' del formulario de Proyecto.
    """

    # --- NAV / TABS ---
    DOCUMENTS_TAB = [
        # Ancla general por texto
        (By.XPATH, "//ul[contains(@role,'tablist') or contains(@class,'nav')]"
                   "//a[contains(@class,'nav-link') and contains(.,'Documentos')]"),
        # Rol=tab por texto
        (By.XPATH, "//*[self::a or self::button][contains(@role,'tab')][contains(.,'Documentos')]"),
        # Fallback por id (suele variar, pero lo dejamos como último recurso)
        (By.ID, "ngb-nav-2"),
    ]

    # Indicadores de que la pestaña Documentos ya quedó activa
    DOCUMENTS_ACTIVE_HINTS = [
        # El propio tab con aria-selected="true"
        (By.XPATH, "//a[contains(@class,'nav-link') and contains(.,'Documentos') and @aria-selected='true']"),
        # Contenido visible de Documentos: botón Agregar dentro del panel/tab actual
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                   "//button[contains(.,'Agregar')]"),
        # O bien la tabla del grid de Documentos
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]//table"),
    ]

    # --- CONTROLES DENTRO DE DOCUMENTOS (para lo que venga) ---
    ADD_BUTTON = [
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                   "//button[contains(.,'Agregar')]"),
        (By.XPATH, "//button[.//span[contains(.,'Agregar')] or contains(.,'Agregar')]"),
    ]

    GRID_TBODY = (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]//table//tbody")
    NO_RECORDS_ROW = (By.XPATH, "//tr[contains(@class,'k-grid-norecords')]")

    # ----------------------------------------------------------

    def open_documents_tab(self) -> None:
        """
        Cambia a la pestaña 'Documentos' y espera a que el contenido esté visible.
        """
        # Aseguramos que la app ya pintó el DOM (helper de BasePage)
        try:
            self.wait_for_app_ready(timeout=15)
        except Exception:
            # Si no existe ese helper en tu BasePage, ignora el try/except: no es crítico.
            pass

        # Encontrar el tab 'Documentos'
        tab = self.find_first_fast(self.DOCUMENTS_TAB, per_try=2.0, visible=True)

        # Llevarlo al viewport y clickear (normal o vía JS si hay overlay/sticky)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tab)
        try:
            tab.click()
        except Exception:
            self.js_click(tab)