# bot/pages/clients_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
import time
from loguru import logger

class ClientsPage:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    # ============== Navegación =================
    def open_direct(self, base_url: str):
        """
        Abre la página de Clientes directo por URL: {base}/customers
        """
        url = base_url.rstrip("/") + "/customers"
        self.driver.get(url)

    def assert_loaded(self):
        """
        Página de clientes lista cuando:
        - URL contiene '/customers'
        - Existe el input de búsqueda con el placeholder de 'Buscar por Nombre...'
        """
        self.wait.until(EC.url_contains("/customers"))
        self.wait.until(EC.presence_of_element_located(self._search_input()))

    def assert_new_loaded(self):
        """
        Formulario de 'Nuevo Cliente' listo cuando la URL contiene '/customers/new'.
        """
        self.wait.until(EC.url_contains("/customers/new"))

    # ============== Selectores =================
    @staticmethod
    def _search_input():
        # placeholder: "Buscar por Nombre, Razón Social, Email, o RFC..."
        return (By.XPATH, "//input[contains(@placeholder,'Buscar por Nombre')]")

    @staticmethod
    def _tbody():
        return (By.XPATH, "//table//tbody")

    @staticmethod
    def _no_records_row():
        # Fila especial de Kendo cuando no hay datos
        return (By.XPATH, "//table//tbody/tr[contains(@class,'k-grid-norecords')]")

    @staticmethod
    def _table_rows():
        # Solo filas de datos reales (excluye k-grid-norecords y filas de agrupación)
        return (By.XPATH, "//table//tbody/tr[not(contains(@class,'k-grid-norecords')) and not(contains(@class,'k-grouping-row'))]")

    @staticmethod
    def _no_results_banner():
        # Fallback textual por si cambia el mensaje
        return (By.XPATH, "//*[contains(.,'No hay datos disponibles') or contains(.,'Sin resultados') or contains(.,'No se encontraron')]")

    @staticmethod
    def _new_button_candidates():
        # + Nuevo (enlace a /customers/new)
        return [
            (By.XPATH, "//a[contains(@href,'/customers/new') and contains(@class,'btn') and contains(@class,'btn-primary')]"),
            (By.XPATH, "//a[contains(@class,'btn') and contains(@class,'btn-primary') and (normalize-space()='Nuevo' or contains(.,'Nuevo'))]"),
        ]

    @staticmethod
    def _search_action_candidates():
        """
        Botón a la derecha del input (check/lupa). Probamos varias variantes.
        """
        return [
            (By.XPATH, "//input[contains(@placeholder,'Buscar por Nombre')]/following-sibling::*[(self::a or self::button)][1]"),
            (By.XPATH, "//input[contains(@placeholder,'Buscar por Nombre')]/following::*[(self::a or self::button) and (contains(@title,'Buscar') or contains(@aria-label,'Buscar') or .//i[contains(@class,'search')])][1]"),
        ]

    # ---- NUEVOS: selectores para 'Crear por IdCIF' y verificación de formulario CIF
    @staticmethod
    def _crear_por_idcif_candidates():
        return [
            (By.XPATH, "//button[contains(@class,'btn') and contains(@class,'btn-primary') and contains(normalize-space(.),'Crear por IdCIF')]"),
            (By.XPATH, "//button[contains(normalize-space(.),'Crear por IdCIF')]"),
        ]

    @staticmethod
    def _cif_form_markers():
        # Marcadores razonables para cuando carga el formulario de IdCIF
        return [
            (By.CSS_SELECTOR, "app-customers-create-cif"),
            (By.XPATH, "//label[contains(translate(.,'idcif','IDCIF'),'IDCIF')]"),
            (By.XPATH, "//*[contains(translate(.,'idcif','IDCIF'),'IDCIF') and (self::input or self::label or self::div)]"),
        ]

    # ============== Utilidades internas =========
    def _visible_element_or_none(self, by_locator):
        try:
            el = self.driver.find_element(*by_locator)
            return el if el.is_displayed() else None
        except Exception:
            return None

    def _first_row_text_snapshot(self):
        rows = self.driver.find_elements(*self._table_rows())
        if not rows:
            return None
        try:
            return (rows[0].find_element(By.XPATH, "./td[1]").text or "").strip()
        except Exception:
            return (rows[0].text or "").strip() or None

    def _click_element_robust(self, el):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except Exception:
            pass
        try:
            ActionChains(self.driver).move_to_element(el).pause(0.05).click(el).perform()
        except (ElementClickInterceptedException, StaleElementReferenceException, Exception):
            self.driver.execute_script("arguments[0].click();", el)

    def _trigger_search(self):
        """
        Intenta activar la búsqueda con ENTER + botón cercano (check/lupa).
        """
        for locator in self._search_action_candidates():
            try:
                el = self._visible_element_or_none(locator)
                if el:
                    self._click_element_robust(el)
                    return
            except Exception:
                continue

    def _has_no_data(self):
        # Primero: fila k-grid-norecords visible
        try:
            norec = self.driver.find_element(*self._no_records_row())
            if norec.is_displayed():
                return True
        except Exception:
            pass
        # Fallback textual
        try:
            b = self.driver.find_element(*self._no_results_banner())
            return b.is_displayed()
        except Exception:
            return False

    # ============== Acciones ===================
    def search_by_name(self, name_upper: str, timeout: int = 12) -> bool:
        """
        Escribe el nombre (MAYÚSCULAS), dispara la búsqueda y ESPERA a que la
        tabla realmente se refresque. Devuelve True si hay filas de datos; False si no.
        """
        inp = self.wait.until(EC.element_to_be_clickable(self._search_input()))

        # snapshots antes de buscar (tbody y primer texto)
        tbody_before = None
        try:
            tbody_before = self.driver.find_element(*self._tbody())
        except Exception:
            pass
        first_before = self._first_row_text_snapshot()

        # escribir y ENTER
        inp.click()
        inp.send_keys(Keys.CONTROL, "a")
        inp.send_keys(Keys.DELETE)
        inp.send_keys((name_upper or "").strip())
        inp.send_keys(Keys.ENTER)

        # además, intenta el botón (check/lupa)
        self._trigger_search()

        # Espera de refresco real
        deadline = time.time() + timeout
        while time.time() < deadline:
            # ¿Se reemplazó el tbody?
            if tbody_before is not None:
                try:
                    if EC.staleness_of(tbody_before)(self.driver):
                        tbody_before = None  # ya cambió
                except Exception:
                    pass

            # Primero: caso "no hay datos"
            if self._has_no_data():
                return False

            # Luego: filas reales (excluyendo k-grid-norecords)
            rows = self.driver.find_elements(*self._table_rows())
            if rows:
                first_now = self._first_row_text_snapshot()
                # Consideramos refrescado si cambió la primera fila
                # o si la primera fila contiene parte del nombre buscado
                if (first_now and first_now != first_before) or (
                    (name_upper or "").split()[0] in (first_now or "").upper()
                ):
                    return True

            time.sleep(0.2)

        # Timeout sin señales concluyentes: asumimos no encontrado
        return False

    def first_row_client_text(self) -> str | None:
        """
        Texto de la primera celda (columna 'Cliente') de la primera fila.
        """
        rows = self.driver.find_elements(*self._table_rows())
        if not rows:
            return None
        try:
            first_cell = rows[0].find_element(By.XPATH, "./td[1]")
            return (first_cell.text or "").strip()
        except Exception:
            return (rows[0].text or "").strip() or None

    # -------- Nuevo cliente (clic robusto) --------
    def click_new(self, timeout: int = 10):
        """
        Hace clic en +Nuevo y espera el formulario.
        Usa scroll + ActionChains y, si es necesario, JS click.
        """
        self.assert_loaded()

        end = time.time() + timeout
        target = None
        while time.time() < end and target is None:
            for loc in self._new_button_candidates():
                el = self._visible_element_or_none(loc)
                if el:
                    target = el
                    break
            if target is None:
                time.sleep(0.2)

        if target is None:
            raise RuntimeError("No se pudo localizar el botón '+ Nuevo'.")

        self._click_element_robust(target)
        self.assert_new_loaded()

    # -------- NUEVO: clic en "Crear por IdCIF" y verificación --------
    def click_crear_por_idcif(self, timeout: int = 10):
        """
        Hace clic en el botón 'Crear por IdCIF' y espera a que aparezca
        el formulario/componente correspondiente.
        """
        # Debemos estar en /customers/new
        self.assert_new_loaded()

        end = time.time() + timeout
        btn = None
        while time.time() < end and btn is None:
            for loc in self._crear_por_idcif_candidates():
                el = self._visible_element_or_none(loc)
                if el:
                    btn = el
                    break
            if btn is None:
                time.sleep(0.2)

        if btn is None:
            raise RuntimeError("No se encontró el botón 'Crear por IdCIF'.")

        self._click_element_robust(btn)

        # Esperar a que cargue el componente/inputs de CIF
        end2 = time.time() + timeout
        loaded = False
        while time.time() < end2 and not loaded:
            for loc in self._cif_form_markers():
                try:
                    el = self.driver.find_element(*loc)
                    if el and el.is_displayed():
                        loaded = True
                        break
                except Exception:
                    continue
            if not loaded:
                time.sleep(0.2)

        if not loaded:
            raise RuntimeError("No se detectó el formulario de 'Crear por IdCIF' tras el clic.")

     # ====== Locators útiles ======
    def _grid_body(self):
        # tbody de la tabla Kendo
        return (By.CSS_SELECTOR, "table.k-table tbody")

    def _first_row_view_link(self):
        # En la PRIMERA fila, el <a> que contiene el ícono de lupa
        return (By.XPATH,
                "//table[contains(@class,'k-table')]//tbody//tr[1]"
                "//a[.//i[contains(@class,'fa-search')]]")

    # ====== Helper de click seguro ======
    def _click_smart(self, el):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.1)
            el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", el)

    # ====== NUEVO: abrir detalle (lupita) de la primera fila ======
    def click_first_view(self, timeout: int = 15):
        """
        Da clic en la lupita (botón 'ver') de la PRIMERA fila del grid.
        Espera a que cargue la página de 'Detalle de Cliente'.
        """
        # Asegura que el grid esté presente
        self.wait.until(EC.presence_of_element_located(self._grid_body()))

        # 1) Intento directo a la PRIMERA fila
        try:
            link = self.wait.until(EC.element_to_be_clickable(self._first_row_view_link()))
            self._click_smart(link)
            print("Click en lupita (primer resultado).")
        except Exception:
            # 2) Fallback: busca cualquier lupa visible en el grid y clica su <a> ancestro
            icons = self.driver.find_elements(By.CSS_SELECTOR, "table.k-table tbody i.fas.fa-search")
            link = None
            for ic in icons:
                if not ic.is_displayed():
                    continue
                try:
                    link = ic.find_element(By.XPATH, "./ancestor::a[1]")
                    self._click_smart(link)
                    print("Click en lupita (fallback por ícono).")
                    break
                except Exception:
                    continue

            if link is None:
                raise RuntimeError("No se encontró la lupita para abrir el detalle del cliente.")

        # 3) (Opcional) Espera corta a que cargue el detalle
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//h2[contains(normalize-space(.),'Detalle de Cliente')]")
            ))
        except Exception:
            # Si el título tarda, no lo reventamos; ya hicimos clic.
            pass

     # Primer enlace de detalle (lupita) en la tabla
    def _first_detail_link(self):
        # En tus capturas el botón es un <a> con href /customers/detail/####
        return (By.XPATH, "(//a[contains(@href,'/customers/detail')])[1]")

    def click_first_view(self, timeout: int = 25):
        link = self.wait.until(EC.element_to_be_clickable(self._first_detail_link()))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        time.sleep(0.1)
        href = link.get_attribute("href")
        try:
            link.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", link)
        print(f"Click en lupita -> {href}")

        # Espera navegación al detalle
        self.wait.until(EC.url_contains("/customers/detail/"))
        print("Detalle de cliente cargando…")