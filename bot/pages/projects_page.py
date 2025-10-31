# bot/pages/projects_page.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from .base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time

NEW_PROJECT_URL = "https://not84.singrafos.com/projects/new"

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
    
    def open_new_project(self):
        self.driver.get(NEW_PROJECT_URL)
        # Espera que cargue el tab "General"
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//h4[contains(.,'Nuevo Proyecto') or contains(.,'Nuevo Proyecto')]")))

    def select_cliente(self, nombre_completo: str):
        # En este portal el Cliente se busca escribiendo y luego seleccionando la sugerencia
        ok = self.kendo_search_and_pick("Cliente", nombre_completo, exact=True)
        if not ok:
            # intenta por contiene cuando haya tildes/espacios extra
            self.kendo_search_and_pick("Cliente", nombre_completo, exact=False)

    def set_descripcion(self, descripcion: str):
        self.set_textarea_by_label("Descripción", descripcion)

    def select_acto(self, nombre_acto: str):
        # Abre combo de Actos, busca y selecciona
        ok = self.kendo_search_and_pick("Actos", nombre_acto, exact=True)
        if not ok:
            self.kendo_search_and_pick("Actos", nombre_acto, exact=False)

    def guardar(self):
        # Botón Guardar azul con ícono
        btn = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Guardar') or @title='Guardar'] | //a[contains(@class,'btn')][contains(.,'Guardar')]")
        ))
        btn.click()

    def create_project(self, abogado: str, cliente: str, descripcion: str, acto: str, auto_save: bool = False):
        self.open_new_project()
        #Abre el combo abogado y selecciona el abogado
        self._pick_kendo_opcion(self._abrir_combo_en_fila("Abogado"),abogado)
        #Colocar el cliente
        self.set_cliente_principal(cliente)
        #Seleccionar acto correspondiente
        combo_actos = self.abrir_flechita_actos()
        self._pick_kendo_opcion(combo_actos, acto)
        #Colocar descripcion
        self.set_descripcion(descripcion)
        #Ir a partes
        self.ir_a_partes()
    
    def _abrir_combo_en_fila(self, label_text: str):
        """
        Abre el dropdown de la fila con etiqueta 'label_text' y devuelve el WebElement
        del combobox (el <kendo-dropdownlist ... role="combobox">).
        """
        fila = self._field_row_by_label(label_text)

        # 1) Localiza el combobox dentro de esa fila (sin asumir <div>)
        combo = fila.find_element(
            By.XPATH,
            ".//*[@role='combobox' and (self::kendo-dropdownlist or @aria-haspopup='listbox')]"
        )

        # 2) Intenta abrir con el botón de flecha (más estable en Kendo)
        try:
            btn = fila.find_element(By.XPATH, ".//button[@aria-label='Select']")
            btn.click()
        except Exception:
            combo.click()

        # 3) Espera a que quede realmente abierto (aria-expanded=true)
        self.wait.until(lambda d: combo.get_attribute("aria-expanded") == "true")
        return combo


    def _pick_kendo_opcion(self, combo_elem, visible_text: str, scroll_attempts: int = 40):
        """
        Con el combo YA ABIERTO (combo_elem), selecciona la opción cuyo texto visible coincida.
        Usa aria-controls para ubicar el popup correcto.
        """
        # 1) Ubica el contenedor del popup/listbox a partir del aria-controls
        listbox_id = combo_elem.get_attribute("aria-controls")
        if listbox_id:
            popup = self.wait.until(EC.visibility_of_element_located((By.ID, listbox_id)))
        else:
            # Fallback por si no expone aria-controls (raro)
            popup = self.wait.until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "(//*[contains(@class,'k-animation-container') or contains(@class,'k-popup')]"
                    "[not(contains(@style,'display: none'))])[last()]"
                ))
            )

        def _find_option():
            # match exacto
            xp_exact = (
                ".//*[@role='option' and normalize-space()=$TXT] | "
                ".//li[normalize-space()=$TXT]"
            ).replace("$TXT", f"'{visible_text}'")
            els = popup.find_elements(By.XPATH, xp_exact)
            if els:
                return els[0]
            # match por contiene (fallback)
            xp_contains = (
                ".//*[@role='option' and contains(normalize-space(),$TXT)] | "
                ".//li[contains(normalize-space(),$TXT)]"
            ).replace("$TXT", f"'{visible_text}'")
            els2 = popup.find_elements(By.XPATH, xp_contains)
            return els2[0] if els2 else None

        # 2) ¿Hay caja de filtro? úsala
        opt = _find_option()
        if opt is None:
            try:
                search = popup.find_element(By.XPATH, ".//input[contains(@class,'k-input-inner')]")
            except Exception:
                # A veces el input está en el propio combo
                try:
                    search = combo_elem.find_element(By.XPATH, ".//input[contains(@class,'k-input-inner')]")
                except Exception:
                    search = None

            if search is not None:
                try:
                    search.clear()
                except Exception:
                    pass
                search.send_keys(visible_text)
                time.sleep(0.35)
                opt = _find_option()

        # 3) Scroll en lista virtualizada hasta hallar la opción
        if opt is None:
            try:
                listbox_scroll = popup.find_element(
                    By.XPATH,
                    ".//*[@role='listbox' or self::ul[contains(@class,'k-list-ul')] or contains(@class,'k-list-content')]"
                )
            except Exception:
                listbox_scroll = popup

            for _ in range(scroll_attempts):
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;",
                    listbox_scroll
                )
                time.sleep(0.10)
                opt = _find_option()
                if opt:
                    break

        if not opt:
            raise RuntimeError(f"No se encontró la opción '{visible_text}' en el combo.")

        # 4) Click seguro
        self.driver.execute_script("arguments[0].scrollIntoView({block:'nearest'});", opt)
        try:
            opt.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", opt)

    def set_cliente_principal(self, nombre_cliente: str):
        """
        Escribe el nombre del cliente en el combobox 'Cliente' y QUITA el focus
        """
        # 1) Localiza la fila por etiqueta y el combobox/input
        fila = self._field_row_by_label("Cliente")

        # El contenedor puede ser <kendo-combobox> o un input con role=combobox
        try:
            combo = fila.find_element(
                By.XPATH,
                ".//*[self::kendo-combobox or @role='combobox']"
            )
        except Exception:
            combo = fila  # fallback

        try:
            combo.click()
        except Exception:
            pass

        # Input interno donde se escribe (clase k-input-inner suele estar)
        try:
            inp = combo.find_element(By.XPATH, ".//input[contains(@class,'k-input-inner')]")
        except Exception:
            # a veces el propio input trae role='combobox'
            inp = fila.find_element(By.XPATH, ".//input[@role='combobox' or contains(@class,'k-input-inner')]")

        # 2) Escribir el nombre SIN Enter
        inp.clear()
        inp.send_keys(nombre_cliente)
        time.sleep(1)

    def abrir_flechita_actos(self):
        """
        Abre el combobox de 'Actos' haciendo click en la flechita.
        Devuelve el WebElement del combobox ya abierto.
        """
        fila = self._field_row_by_label("Actos")

        # 1) Botón flechita (más estable en Kendo)
        try:
            btn = fila.find_element(By.XPATH, ".//button[@aria-label='Select']")
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            btn.click()
        except Exception:
            # Fallback: por si el botón cambia de aria-label/clases
            caret = fila.find_element(
                By.XPATH,
                ".//button[contains(@class,'k-input-button') or .//kendo-svgicon[contains(@class,'caret')]]"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", caret)
            caret.click()

        # 2) Espera a que el combo quede abierto
        combo = fila.find_element(By.XPATH, ".//*[@role='combobox']")
        self.wait.until(lambda d: combo.get_attribute("aria-expanded") == "true")
        return combo
    
    def set_descripcion(self, texto: str):
        """
        Escribe la descripción y QUITA el foco sin presionar Enter.
        Soporta id fijo (#description) y fallback por fila 'Descripción'.
        """
        # 1) Localiza el input
        try:
            inp = self.driver.find_element(By.ID, "description")
        except Exception:
            # Fallback por etiqueta de la fila
            try:
                fila = self._field_row_by_label("Descripción")
            except Exception:
                fila = self._field_row_by_label("Descripcion")  # por si viene sin acento
            # input de texto dentro de la fila
            inp = fila.find_element(By.XPATH, ".//input[@type='text' or contains(@class,'form-control')]")

        # 2) A la vista y foco
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        inp.click()

        # 3) Limpiar de forma robusta
        try:
            inp.clear()
        except Exception:
            inp.send_keys(Keys.CONTROL, "a")
            inp.send_keys(Keys.BACK_SPACE)

        # 4) Escribir el texto
        if texto:
            inp.send_keys(texto)

        # 5) Quitar el foco SIN Enter (blur)
        try:
            self.driver.execute_script("arguments[0].blur();", inp)
        except Exception:
            # Fallback: TAB a siguiente control (p.ej. Estado)
            inp.send_keys(Keys.TAB)

        # 6) (Opcional) esperar a que Angular marque 'touched' o muestre la palomita
        try:
            self.wait.until(lambda d: "ng-touched" in inp.get_attribute("class"))
        except Exception:
            pass

    def _open_tab(self, tab_text: str):
        """
        Da click en la pestaña (tab) por su texto visible, ej. 'Partes'.
        Funciona para Cotización, Comisiones, Partes, Documentos, Actos / Inmuebles, Comentarios.
        """
        # ul de tabs
        ul = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//ul[contains(@class,'nav-tabs')]")
        ))
        # link del tab por texto
        link = ul.find_element(
            By.XPATH,
            f".//a[contains(@class,'nav-link') and normalize-space()={repr(tab_text)}]"
        )

        # a la vista y click
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        try:
            link.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", link)

        # esperar estado seleccionado
        try:
            self.wait.until(lambda d: link.get_attribute("aria-selected") == "true"
                                    or "active" in link.get_attribute("class"))
        except Exception:
            pass

    def ir_a_partes(self):
        self._open_tab("Partes")