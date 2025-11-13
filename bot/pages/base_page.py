from __future__ import annotations
from typing import List, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

Locator = Tuple[str, str]

class BasePage:

    DOCUMENTS_TAB = [
        (By.XPATH, "//ul[contains(@role,'tablist') or contains(@class,'nav')]"
                   "//a[contains(@class,'nav-link') and contains(.,'Documentos')]"),
        (By.XPATH, "//*[self::a or self::button][contains(@role,'tab')][contains(.,'Documentos')]"),
        (By.ID, "ngb-nav-2"),
    ]

    DOCUMENTS_ACTIVE_HINTS = [
        (By.XPATH, "//a[contains(@class,'nav-link') and contains(.,'Documentos') and @aria-selected='true']"),
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                   "//button[contains(.,'Agregar')]"),
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]//table"),
    ]

    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    def open(self, url: str):
        self.driver.get(url)

    def open_url_projects(self, url):
        # Abrir projects
        try:
            full_url = url.rstrip("/") + "/projects"
            self.driver.get(full_url)
            print(f"Abriendo projects: {full_url}")

            # Esperar que cargue el 'projects'
            self.wait.until(EC.url_contains("/projects"))
            print("projects cargado correctamente.")
        except Exception as e:
            print(f"Error al cargar el projects: {e}")
            return
    
    def open_documents_tap(self):
        try:
            self.wait_for_app_ready(timeout=15)
        except Exception:
            pass

        tab = self.find_first_fast(self.DOCUMENTS_TAB, per_try=2.0, visible=True)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tab)
        try:
            tab.click()
        except Exception:
            self.js_click(tab)

        def _tab_selected(_):
            try:
                return tab.get_attribute("aria-selected") == "true"
            except StaleElementReferenceException:
                return True

        try:
            self.wait.until(_tab_selected)
        except Exception:
            pass

        self.find_first_fast(self.DOCUMENTS_ACTIVE_HINTS, per_try=2.0, visible=True)

    # === NUEVO: espera a que Angular termine de montar el DOM ===
    def wait_for_app_ready(self, timeout: int = 15):
        w = WebDriverWait(self.driver, timeout, poll_frequency=0.2)
        # 1) que exista app-root
        w.until(lambda d: d.execute_script("return !!document.querySelector('app-root')"))
        # 2) que app-root tenga hijos (ya pintó algo)
        w.until(lambda d: d.execute_script("const r=document.querySelector('app-root'); return r && r.children && r.children.length>0"))
        # 3) que el loader ya no esté visible
        w.until(lambda d: d.execute_script("""
            const el = document.querySelector('.app-loading');
            if (!el) return true;
            const cs = getComputedStyle(el);
            return el.style.display==='none' || el.style.opacity==='0' || cs.display==='none' || cs.opacity==='0';
        """))

    def find_first_fast(self, locators: List[Locator], per_try: float = 1.2, visible: bool = True):
        cond = EC.visibility_of_element_located if visible else EC.presence_of_element_located
        last_exc = None
        for by, sel in locators:
            try:
                return WebDriverWait(self.driver, per_try, poll_frequency=0.2).until(cond((by, sel)))
            except Exception as e:
                last_exc = e
        if last_exc:
            raise last_exc
        raise Exception("Element not found with provided locators.")

    def click_when_clickable(self, locator: Locator, timeout: float = 3.0):
        return WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(EC.element_to_be_clickable(locator))

    def type_text(self, element, text: str, clear: bool = True):
        if clear:
            element.clear()
        element.send_keys(text)

    def js_click(self, element):
        self.driver.execute_script("arguments[0].click();", element)

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def _field_row_by_label(self, label_text: str):
        """
        Regresa el contenedor (row) del campo cuyo <label> visible coincide.
        Soporta labels como: Abogado, Cliente, Descripción, Actos, etc.
        """
        # Busca el label por texto y toma el primer contenedor de input siguiente.
        xpath = f"//label[normalize-space()='{label_text}']/following::*[self::div or self::input or self::textarea][1]"
        return self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

    def kendo_open_dropdown_by_label(self, label_text: str):
        """
        Abre un Kendo DropDown/Combo asociado al label.
        """
        container = self._field_row_by_label(label_text)

        # 1) intenta botón de flecha (k-input-button)
        try:
            btn = container.find_element(By.XPATH, ".//button[contains(@class,'k-input-button')]")
            btn.click()
            return container
        except Exception:
            pass

        # 2) si no hay botón, intenta dar foco al input interno y abrir con ALT+↓ o click
        try:
            inp = container.find_element(By.XPATH, ".//input[contains(@class,'k-input-inner') or @placeholder='Buscar...']")
            inp.click()
            inp.send_keys(Keys.ALT, Keys.ARROW_DOWN)
            return container
        except Exception:
            # último recurso: click al contenedor
            container.click()
            return container

    def kendo_pick_visible_option(self, text: str, exact: bool = True, timeout: int = 10):
        """
        Selecciona un <li> del popup Kendo visible.
        """
        # popup visible de Kendo (no display:none)
        popup_xpath = "//div[contains(@class,'k-animation-container') and not(contains(@style,'display: none'))]"
        list_item_exact = f"{popup_xpath}//li[normalize-space()='{text}']"
        list_item_contains = f"{popup_xpath}//li[contains(normalize-space(),'{text}')]"

        try:
            if exact:
                opt = self.wait.until(EC.element_to_be_clickable((By.XPATH, list_item_exact)))
            else:
                opt = self.wait.until(EC.element_to_be_clickable((By.XPATH, list_item_contains)))
            opt.click()
            return True
        except TimeoutException:
            return False

    def kendo_search_and_pick(self, label_text: str, query_text: str, exact: bool = True):
        """
        Abre el combo por label, escribe query y elige opción.
        Sirve para Cliente y Actos.
        """
        container = self.kendo_open_dropdown_by_label(label_text)
        # input de búsqueda/entrada
        inp = None
        try:
            inp = container.find_element(By.XPATH, ".//input[contains(@class,'k-input-inner') or @placeholder='Buscar...']")
        except Exception:
            # a veces el input vive en el popup; forzamos abrir de nuevo y buscamos global
            self.kendo_open_dropdown_by_label(label_text)

        if inp is None:
            # busca input global visible
            inp = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'k-popup') and not(contains(@style,'display: none'))]//input")
            ))
        inp.clear()
        inp.send_keys(query_text)

        # esperar resultados y elegir
        picked = self.kendo_pick_visible_option(query_text if exact else query_text, exact=exact)
        if not picked:
            # intenta por "contiene" por si hay acentos/diferencias
            picked = self.kendo_pick_visible_option(query_text, exact=False)
        return picked

    def set_textarea_by_label(self, label_text: str, value: str):
        el = self._field_row_by_label(label_text)
        # textarea o input
        try:
            ta = el if el.tag_name.lower() in ("input", "textarea") else el.find_element(By.XPATH, ".//textarea|.//input")
        except Exception:
            ta = el
        ta.click()
        ta.clear()
        ta.send_keys(value)
