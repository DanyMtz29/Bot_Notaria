from __future__ import annotations
from typing import List, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

Locator = Tuple[str, str]

class BasePage:
    def __init__(self, driver: WebDriver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    def open(self, url: str):
        self.driver.get(url)

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