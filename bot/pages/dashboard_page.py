# bot/pages/dashboard_page.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from .base_page import BasePage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DashboardPage(BasePage):
    _MENU_BY_TEXT = "//nav//*[self::a or self::button or self::div][contains(normalize-space(),'{text}')]"

    # contenedor típico del dropdown (si existe)
    DROPDOWN_CONTAINER = (
        By.XPATH,
        "//*[contains(@class,'dropdown-menu') or contains(@class,'k-animation') "
        "or contains(@class,'mat-menu') or contains(@class,'popover')]"
    )

    def _dropdown_item_by_text(self, text: str):
        # intenta dentro de contenedores de dropdown (cuando existen)
        return (By.XPATH,
            "(//*[contains(@class,'dropdown-menu') or contains(@class,'k-animation') "
            "or contains(@class,'mat-menu') or contains(@class,'popover')]"
            "//*[self::a or self::button or self::div][contains(normalize-space(),'%s')])[1]" % text
        )

    def _find_item_below_menu_js(self, menu_el, text: str):
        # Fallback “espacial”: toma el primer elemento visible con 'text'
        # que esté DEBAJO del botón del menú en la pantalla.
        return self.driver.execute_script("""
            var menu = arguments[0], text = arguments[1].toLowerCase();
            var mrect = menu.getBoundingClientRect();
            var nodes = Array.from(document.querySelectorAll("a,button,div"));
            nodes = nodes.filter(function(e){
                if(!e.textContent) return false;
                var t = e.textContent.trim().toLowerCase();
                if(t.indexOf(text) === -1) return false;
                var r = e.getBoundingClientRect();
                var visible = !!(e.offsetParent) && getComputedStyle(e).visibility !== 'hidden'
                              && r.width > 2 && r.height > 2;
                // Debajo del menú (unos px de margen)
                return visible && r.top > (mrect.bottom - 2);
            });
            return nodes.length ? nodes[0] : null;
        """, menu_el, text)

    def _open_menu_and_click(self, menu_text: str, item_text: str, url_contains=None, page_hints=None):
        self.wait_for_app_ready(timeout=15)

        # 1) Abrir menú
        menu_locator = (By.XPATH, self._MENU_BY_TEXT.format(text=menu_text))
        menu = self.find_first_fast([menu_locator], per_try=2.0, visible=True)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", menu)
        try:
            ActionChains(self.driver).move_to_element(menu).pause(0.2).perform()
        except Exception:
            pass
        try:
            menu.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", menu)

        # 2) Intento 1: si existe un contenedor de dropdown, espera y busca dentro
        item = None
        try:
            WebDriverWait(self.driver, 2.0, poll_frequency=0.2).until(
                EC.visibility_of_element_located(self.DROPDOWN_CONTAINER)
            )
            item = self.find_first_fast([self._dropdown_item_by_text(item_text)], per_try=1.5, visible=True)
        except Exception:
            item = None

        # 3) Intento 2 (fallback): localizar el ítem que esté DEBAJO del botón del menú
        if item is None:
            item = WebDriverWait(self.driver, 4.0, poll_frequency=0.2).until(
                lambda d: self._find_item_below_menu_js(menu, item_text)
            )

        href = None
        try:
            href = item.get_attribute("href")
        except Exception:
            pass

        # 4) Click
        try:
            item.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", item)

        # 5) Espera navegación / pistas
        def url_ok(d):
            return url_contains and any(s in d.current_url.lower() for s in url_contains)

        def hint_ok():
            if not page_hints: return False
            try:
                self.find_first_fast(page_hints, per_try=2.0, visible=True)
                return True
            except Exception:
                return False

        try:
            WebDriverWait(self.driver, 5, poll_frequency=0.2).until(lambda d: url_ok(d))
        except Exception:
            if not hint_ok() and href and href.startswith("http"):
                self.driver.get(href)
            WebDriverWait(self.driver, 6, poll_frequency=0.2).until(
                lambda d: url_ok(d) or hint_ok()
            )

    # ====== Proyectos (sigue igual)
    def go_to_proyectos(self):
        self._open_menu_and_click(
            menu_text="Escrituras",
            item_text="Proyectos",
            url_contains=["/projects", "/proyectos"],
            page_hints=[
                (By.XPATH, "//h1[contains(normalize-space(),'Proyectos') and not(ancestor::nav)]"),
                (By.XPATH, "//button[contains(.,'Nuevo') and not(ancestor::nav)]")
            ]
        )

    # ====== Clientes → Clientes (con fallback espacial)
    def go_to_clientes(self):
        self._open_menu_and_click(
            menu_text="Clientes",
            item_text="Clientes",
            url_contains=["/customers", "/clients", "/clientes"],
            page_hints=[
                (By.XPATH, "//h1[contains(normalize-space(),'Clientes') and not(ancestor::nav)]"),
                (By.XPATH, "//*[contains(@class,'k-grid') or contains(@class,'table')][.//th[contains(.,'Cliente') or contains(.,'Nombre')]]"),
                (By.XPATH, "//button[contains(.,'Nuevo') and not(ancestor::nav)]"),
            ]
        )
