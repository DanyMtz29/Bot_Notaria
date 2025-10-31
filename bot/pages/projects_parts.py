# bot/pages/projects_partes.py
from __future__ import annotations

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class ProjectsPartesPage:
    """
    Acciones dentro de la pestaña 'Partes' del formulario de 'Nuevo Proyecto'.
    """

    def __init__(self, driver, wait: WebDriverWait):
        self.driver = driver
        self.wait = wait

    # ---------- utils internos ----------

    def _root(self):
        """
        Devuelve el nodo raíz del componente de Partes.
        """
        return self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//app-project-parts")
        ))

    def _asegurar_acordeon_abierto(self, root):
        """
        En algunos layouts, 'Partes' viene dentro de un acordeón.
        Si está colapsado, intenta abrirlo.
        """
        try:
            cuerpo = root.find_element(
                By.XPATH, ".//div[contains(@class,'accordion-body') or contains(@class,'collapse')]"
            )
            clases = cuerpo.get_attribute("class") or ""
            if "collapse" in clases and "show" not in clases:
                toggle = root.find_element(By.XPATH, ".//button[contains(@class,'accordion-button')]")
                try:
                    toggle.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", toggle)
                # esperar a que se expanda
                self.wait.until(lambda d: "show" in cuerpo.get_attribute("class"))
        except Exception:
            # si no hay acordeón, no pasa nada
            pass

    def _click_seguro(self, el):
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", el)

    # ---------- acciones públicas ----------

    def click_agregar(self):
        """
        Presiona el botón 'Agregar' dentro de Partes.
        Soporta:
        - <button>Agregar</button>
        - <button><span>Agregar</span></button>
        - aria-label/title='Agregar'
        - fallback a primer .btn.btn-primary visible dentro de Partes
        """
        root = self._root()
        self._asegurar_acordeon_abierto(root)

        btn = None
        candidatos = [
            ".//button[normalize-space()='Agregar']",
            ".//button[.//span[normalize-space()='Agregar']]",
            ".//button[@aria-label='Agregar' or @title='Agregar']",
            # fallback genérico
            ".//button[contains(@class,'btn') and contains(@class,'btn-primary')][not(@disabled)]",
        ]
        for xp in candidatos:
            try:
                btn = root.find_element(By.XPATH, xp)
                break
            except Exception:
                continue

        if btn is None:
            # último fallback: cualquier btn-primary dentro del tab
            btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//app-project-parts//button[contains(@class,'btn-primary')]")
            ))

        self._click_seguro(btn)

        # Espera best-effort a que aparezca la UI de alta (modal o fila editable)
        try:
            self.wait.until(
                lambda d: d.find_elements(By.XPATH, "//div[contains(@class,'modal') or contains(@class,'k-dialog')]")
                or root.find_elements(By.XPATH, ".//input | .//select | .//textarea")
            )
        except Exception:
            pass
    
    def escribir_busqueda_directorio(self, driver, wait, nombre: str) -> None:
        """
        Escribe en el campo 'Busca datos existentes por Nombre, CURP o RFC.' del modal 'Parte Nueva'
        y confirma (ENTER). Si quieres seleccionar de la lista, abre la flecha y elige.
        """
        # 1) Raíz del modal visible (ngb-modal-window con .show)
        modal = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "ngb-modal-window.d-block.modal.show")
        ))

        # 2) Localiza el <input> del Kendo ComboBox (varios fallbacks)
        locators = [
            # por name del combobox (si lo mantiene)
            (By.XPATH, ".//kendo-combobox[@name='customersDropDownParts']//input[contains(@class,'k-input-inner')]"),
            # por label cercano
            (By.XPATH, ".//label[contains(.,'Buscar en Directorio de Clientes')]/following::input[contains(@class,'k-input-inner')][1]"),
            # por placeholder (parcial)
            (By.XPATH, ".//input[contains(@placeholder,'Nombre, CURP o RFC') and contains(@class,'k-input-inner')]"),
            (By.XPATH, ".//input[contains(@placeholder,'Busca datos existentes') and contains(@class,'k-input-inner')]"),
        ]

        campo = None
        for by, sel in locators:
            try:
                el = modal.find_element(by, sel)
                if el.is_displayed():
                    campo = el
                    break
            except Exception:
                pass

        if not campo:
            # Fallback global si todo falla
            campo = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//kendo-combobox//input[contains(@class,'k-input-inner')]")
            ))

        # 3) Focus + escribir + confirmar
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", campo)
        campo.click()
        campo.send_keys(Keys.CONTROL, "a")
        campo.send_keys(Keys.DELETE)
        campo.send_keys((nombre or "").strip())
        time.sleep(0.2)   # micro respiro para que Kendo filtre

        # (Opcional) si quieres abrir la flecha y elegir la 1ª opción explícitamente:
        try:
            btn = modal.find_element(By.XPATH, ".//kendo-combobox//button[contains(@class,'k-input-button')]")
            driver.execute_script("arguments[0].click();", btn)
            # espera que aparezcan las opciones y confirma la primera
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".k-animation-container .k-list .k-list-ul li")
            ))
            campo.send_keys(Keys.ENTER)
        except Exception:
            # si no hay lista, con ENTER ya quedó
            pass

    def _modal_container(self):
        """
        Devuelve el contenedor del modal actualmente visible (ngb-modal-window,
        modal-dialog estándar o kendo-dialog).
        """
        return self.wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "("
            "//ngb-modal-window[contains(@class,'show')]"
            " | //div[contains(@class,'modal') and contains(@class,'show')]//div[contains(@class,'modal-dialog')]"
            " | //kendo-dialog//div[contains(@class,'k-dialog-content')]"
            ")[last()]"
        )))

    def abrir_combo_rol(self):
        """
        Abre el dropdown de 'Rol' en el modal 'Parte Nueva'.
        Devuelve el WebElement del combobox ya abierto (aria-expanded='true').
        """
        modal = self._modal_container()

        # Fila del campo 'Rol'
        fila = modal.find_element(
            By.XPATH,
            ".//label[normalize-space()='Rol']/ancestor::*[contains(@class,'form-group')][1]"
        )

        # El combobox de Kendo para Rol
        combo = fila.find_element(
            By.XPATH,
            ".//*[@role='combobox' and (@aria-haspopup='listbox' or self::kendo-dropdownlist)]"
        )

        # Llevar al viewport
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", combo)

        # Preferir la flechita; si no, clic directo al combo
        try:
            btn = fila.find_element(By.XPATH, ".//button[@aria-label='Select' or contains(@class,'k-icon-button')]")
            btn.click()
        except Exception:
            combo.click()

        # Esperar a que quede abierto
        self.wait.until(lambda d: combo.get_attribute("aria-expanded") == "true")
        return combo
    
    def seleccionar_rol(self, rol_texto: str):
        """
        Abre el combo 'Rol' del modal y selecciona la opción indicada.
        """
        combo = self.abrir_combo_rol()  # lo que hicimos en el paso anterior
        self._pick_kendo_opcion_modal(combo, rol_texto.upper())


    def _pick_kendo_opcion_modal(self, combo_elem, visible_text: str, scroll_attempts: int = 40):
        """
        Igual que _pick_kendo_opcion de projects_page, pero declarada aquí para usarla
        en el modal. Si ya tienes la versión compartida en otra clase/util, puedes
        llamar a esa en lugar de duplicarla.
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

    def set_persona_moral(self, value: bool = True):
        """
        Marca o desmarca el checkbox '¿Es persona moral?' en el formulario de Parte.
        No depende del contenedor del modal: busca el checkbox visible con id/name/formcontrolname ~ isMoral.
        """
        # Checkbox visible (evitamos popups ocultos / display:none)
        chk_xpath = (
            "(//input[@type='checkbox' and "
            " ( @id='isMoral' or contains(@name,'isMoral') or contains(@formcontrolname,'isMoral') ) "
            " and not(ancestor::div[contains(@style,'display: none')])"
            " and not(ancestor::div[contains(@class,'k-hidden')])"
            "])[last()]"
        )

        # 1) Espera a que sea clickeable
        chk = self.wait.until(EC.element_to_be_clickable((By.XPATH, chk_xpath)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", chk)

        # 2) Sólo clic si cambia de estado
        if chk.is_selected() != value:
            try:
                chk.click()
            except Exception:
                # 2.a) Fallback: click en el label vinculado
                try:
                    lbl = self.driver.find_element(
                        By.XPATH,
                        "(//label[@for='isMoral' or contains(normalize-space(),'persona moral')])[last()]"
                    )
                    self.driver.execute_script("arguments[0].click();", lbl)
                except Exception:
                    # 2.b) Fallback final: click por JS directo
                    self.driver.execute_script("arguments[0].click();", chk)

        # 3) Confirma el estado final
        self.wait.until(lambda d: d.find_element(By.XPATH, chk_xpath).is_selected() == value)

    def marcar_persona_moral(self):
        """Marca el checkbox '¿Es persona moral?'."""
        self.set_persona_moral(True)

    
    def guardar_parte(self):
        """
        Hace clic en el botón 'Guardar' del modal de Parte y espera a que el modal se cierre.
        Soporta modales Bootstrap/ngb y (fallback) Kendo.
        """
        # 1) Localiza el último modal visible
        modal = self.wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "("
            "//div[contains(@class,'modal') and contains(@class,'show')]"
            " | //ngb-modal-window//div[@role='document']"
            " | //kendo-dialog//div[contains(@class,'k-dialog-content')]"
            ")[last()]"
        )))

        # 2) Busca el botón Guardar dentro del modal
        btn_xpath = (
            ".//button[@type='submit' and (normalize-space()='Guardar' or contains(.,'Guardar'))]"
        )
        try:
            btn = modal.find_element(By.XPATH, btn_xpath)
        except Exception:
            # Fallback por clase verde de éxito
            btn = modal.find_element(
                By.XPATH,
                ".//button[(contains(@class,'btn-success') or contains(@class,'btn-outline-success'))"
                " and (normalize-space()='Guardar' or contains(.,'Guardar'))]"
            )

        # 3) Asegura visibilidad y clic (con fallback por JS)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        try:
            self.wait.until(lambda d: btn.is_enabled() and btn.is_displayed())
            btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", btn)

        # 4) Espera a que el modal se cierre (evita dobles clics)
        try:
            from selenium.webdriver.support.expected_conditions import invisibility_of_element
            self.wait.until(invisibility_of_element(modal))
        except Exception:
            # Si el helper no está, usa el locator del modal
            self.wait.until(EC.invisibility_of_element_located((
                By.XPATH,
                "("
                "//div[contains(@class,'modal') and contains(@class,'show')]"
                " | //ngb-modal-window//div[@role='document']"
                " | //kendo-dialog//div[contains(@class,'k-dialog-content')]"
                ")[last()]"
            )))