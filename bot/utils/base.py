from dotenv import load_dotenv
from bot.utils.selenium_imports import *
from bot.utils.common_imports import *
from bot.utils.Logger import setup_logger
from typing import List, Tuple

load_dotenv("bot/config/.env")
URL = os.getenv("PORTAL_URL", "")
setup_logger("Proceso principal")
Locator = Tuple[str, str]

class Base:

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
        self.url = URL

    #Abre una url del portal
    def open_url(self, page: str) -> None:
        try:
            login_url = self.url + page
            print(f"URL: {login_url}")
            self.driver.get(login_url)
            print(f"Abriendo projects: {page}")

            # Esperar que cargue el 'projects'
            self.wait.until(EC.url_contains(f"/{page}"))
            print("Login cargado correctamente.")
        except Exception as e:
            logger.error(f"No se pudo abrir el login {e}")

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

    def type_text(self, element, text: str, clear: bool = True):
        if clear:
            element.clear()
        element.send_keys(text)

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