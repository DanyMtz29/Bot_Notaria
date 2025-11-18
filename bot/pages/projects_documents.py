# bot/pages/projects_documents.py
from __future__ import annotations

from bot.utils.common_imports import *
from bot.utils.selenium_imports import *
from bot.utils.base import Base


class ProjectsDocumentsPage(Base):
    """
    Acciones relacionadas con la pestaña 'Documentos' del formulario de Proyecto.
    """
    # --- CONTENEDOR DEL GRID (SCROLL) Y TABLA ---
    GRID_SCROLL = [
        (By.CSS_SELECTOR, "div.tab-pane.active div.k-grid-content.k-virtual-content"),
        (By.CSS_SELECTOR, "div.tab-pane.active div.k-virtual-content"),
        (By.CSS_SELECTOR, "div.tab-pane.active div.k-grid-content"),
    ]
    GRID_TABLE = [
        (By.CSS_SELECTOR, "div.tab-pane.active div.k-virtual-content table.k-table"),
        (By.CSS_SELECTOR, "div.tab-pane.active div.k-grid-content table.k-table"),
    ]

    # --- CONTROLES ---
    ADD_BUTTON = [
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                   "//button[contains(.,'Agregar')]"),
        (By.XPATH, "//button[.//span[contains(.,'Agregar')] or contains(.,'Agregar')]"),
    ]

    GRID_TBODY = (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]//table//tbody")
    NO_RECORDS_ROW = (By.XPATH, "//tr[contains(@class,'k-grid-norecords')]")

    # --- Botones / inputs de la sección "Documentos Anexos" ---
    SUBIR_DOCS_INPUT = [
        (By.CSS_SELECTOR, "div.tab-pane.active input#attachment[type='file']"),
        (By.CSS_SELECTOR, "div.tab-pane.active input[type='file'].inputfile"),
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]//input[@type='file']"),
    ]
    SUBIR_DOCS_LABEL = [
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                "//label[contains(@class,'btn') and contains(.,'Subir Documentos')]"),
        (By.XPATH, "//label[@for='attachment' and contains(@class,'btn')]"),
    ]
    IMPORT_DOCS_BUTTON = [
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                "//button[.//i[contains(@class,'fa-file-import')] or contains(.,'Importar Documentos')]"),
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]"
                "//button[contains(.,'Importar Documentos')]"),
    ]

    def click_agregar_documento(self):
        btn = self.find_first_fast(self.ADD_BUTTON, per_try=2.0, visible=True)
        try:
            btn.click()
        except Exception:
            self.js_click(btn)

    # ----------------------------------------------------------
    # Helpers de grid / scroll
    def _get_grid_scroll(self):
        return self.find_first_fast(self.GRID_SCROLL, per_try=2.0, visible=True)

    def _get_grid_table(self):
        return self.find_first_fast(self.GRID_TABLE, per_try=2.0, visible=True)

    def _scroll_grid_by(self, grid, delta: int):
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[1];", grid, delta)

    def _scroll_to_top(self, grid):
        self.driver.execute_script("arguments[0].scrollTop = 0;", grid)

    # ----------------------------------------------------------
    # Búsqueda de fila por descripción (case-insensitive, soporta virtual scroll)
    def find_row_by_description(self, descripcion: str, max_pages: int = 120):
        """
        Busca una fila en el grid de 'Documentos Requeridos' por la columna 'Descripción' (1a columna).
        Scrollea el grid hasta encontrarla. Devuelve el WebElement <tr> si se encontró.
        """
        assert descripcion and descripcion.strip(), "Descripción no puede ser vacía."
        term = descripcion.strip().lower()

        grid = self._get_grid_scroll()
        table = self._get_grid_table()

        # Asegura inicio para recorrido completo
        self._scroll_to_top(grid)

        # XPath case-insensitive con translate()
        UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ"
        LOWER = "abcdefghijklmnopqrstuvwxyzáéíóúüñ"
        row_xpath = (
            f".//tbody//tr[contains(@class,'k-table-row')][.//td[1]"
            f"[contains(translate(normalize-space(.), '{UPPER}', '{LOWER}'), {repr(term)})]]"
        )

        # Dimensiones de scroll
        viewport = self.driver.execute_script("return arguments[0].clientHeight;", grid)
        step = int(viewport * 0.85) if viewport else 400

        seen_scroll_tops = set()

        for _ in range(max_pages):
            # Intenta hallarla en la vista actual
            try:
                row = table.find_element(By.XPATH, row_xpath)
                # Traerla bien a la vista y regresar la fila viva (no stale)
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
                return row
            except Exception:
                pass

            # Scrollea una "página"
            current_top = self.driver.execute_script("return arguments[0].scrollTop;", grid)
            self._scroll_grid_by(grid, step)
            new_top = self.driver.execute_script("return arguments[0].scrollTop;", grid)

            # Paro de seguridad si ya no avanza
            sig = (current_top, new_top)
            if sig in seen_scroll_tops or new_top == current_top:
                break
            seen_scroll_tops.add(sig)

        raise NoSuchElementException(f"No se encontró en 'Documentos Requeridos' la descripción: {descripcion!r}")

    # ----------------------------------------------------------
    # Seleccionar / deseleccionar el checkbox 'Faltante' de una fila por Descripción
    def set_faltante_by_description(self, descripcion: str, marcar: bool = True) -> None:
        """
        Localiza la fila por 'descripcion' y asegura el estado del checkbox 'Faltante'.
        """
        row = self.find_row_by_description(descripcion)

        # Checkbox dentro de la misma fila (columna 'Faltante')
        # Usamos input[type=checkbox] dentro de la fila.
        try:
            checkbox = row.find_element(By.XPATH, ".//input[@type='checkbox']")
        except Exception:
            # Fallback: hay layouts que ponen el label y el input hermanos
            checkbox = row.find_element(By.XPATH, ".//label[contains(@class,'form-check-label')]/preceding-sibling::input[@type='checkbox']")

        # Asegura visibilidad
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)

        # Si ya está en el estado deseado, no tocar
        try:
            checked = checkbox.is_selected()
        except Exception:
            checked = self.driver.execute_script("return arguments[0].checked === true;", checkbox)

        if marcar and not checked:
            try:
                checkbox.click()
            except Exception:
                self.js_click(checkbox)
        elif (not marcar) and checked:
            try:
                checkbox.click()
            except Exception:
                self.js_click(checkbox)

    # ----------------------------------------------------------
    # Bulk: marcar/desmarcar varias descripciones
    def set_faltante_bulk(self, descripciones: list[str], marcar: bool = True) -> None:
        """
        Itera una lista de descripciones y marca/desmarca 'Faltante' para cada una.
        """
        if not descripciones:
            return

        grid = self._get_grid_scroll()
        self._scroll_to_top(grid)  # empezamos arriba para recorridos consistentes

        for desc in descripciones:
            self.set_faltante_by_description(desc, marcar=marcar)

    # ----------------------------------------------------------
    # (Opcional) Obtener todas las descripciones del grid (recorriendo el scroll)
    def list_all_required_descriptions(self, max_pages: int = 200) -> list[str]:
        """
        Recorre el grid virtual y devuelve un listado único de las descripciones visibles en la primera columna.
        Útil para debug o para mapear nombres exactos.
        """
        grid = self._get_grid_scroll()
        table = self._get_grid_table()

        self._scroll_to_top(grid)
        viewport = self.driver.execute_script("return arguments[0].clientHeight;", grid)
        step = int(viewport * 0.85) if viewport else 400

        seen_scroll_tops = set()
        items = []

        for _ in range(max_pages):
            # Descripciones visibles en esta "página"
            cells = table.find_elements(By.XPATH, ".//tbody//tr[contains(@class,'k-table-row')]/td[1]")
            for c in cells:
                try:
                    txt = c.text.strip()
                    if txt and txt not in items:
                        items.append(txt)
                except StaleElementReferenceException:
                    continue

            current_top = self.driver.execute_script("return arguments[0].scrollTop;", grid)
            self._scroll_grid_by(grid, step)
            new_top = self.driver.execute_script("return arguments[0].scrollTop;", grid)
            sig = (current_top, new_top)
            if sig in seen_scroll_tops or new_top == current_top:
                break
            seen_scroll_tops.add(sig)

        return items

    def click_importar_documentos(self) -> None:
        """
        Click al botón 'Importar Documentos'.
        """
        btn = self.find_first_fast(self.IMPORT_DOCS_BUTTON, per_try=2.0, visible=True)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        try:
            btn.click()
        except Exception:
            self.js_click(btn)

    def click_subir_documentos(self) -> None:
        """
        Click al botón/label 'Subir Documentos' (abre el diálogo del SO).
        Nota: para subir archivos de forma automática, usa 'subir_documentos(...)'.
        """
        lbl = self.find_first_fast(self.SUBIR_DOCS_LABEL, per_try=2.0, visible=True)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl)
        try:
            lbl.click()
        except Exception:
            self.js_click(lbl)

    def subir_documentos(self, rutas: list[str] | str) -> None:
        """
        Sube archivos enviándolos directamente al <input type='file'> (soporta múltiples).
        - 'rutas' puede ser lista o string. Si son varios, se separan con '\n'.
        - Pasa rutas absolutas.
        """
        if isinstance(rutas, str):
            rutas_list = [rutas]
        else:
            rutas_list = list(rutas or [])

        rutas_list = [os.path.abspath(p) for p in rutas_list if p and str(p).strip()]
        assert rutas_list, "Debes pasar al menos un archivo para subir."

        inp = self.find_first_fast(self.SUBIR_DOCS_INPUT, per_try=2.0, visible=True)
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
        except Exception:
            pass

        # Selenium permite múltiples archivos unidos por '\n'
        inp.send_keys("\n".join(rutas_list))

    def _make_file_input_visible(self, inp) -> None:
        """Asegura que el input[type=file] se pueda usar con send_keys."""
        self.driver.execute_script(
            "arguments[0].style.display='block';"
            "arguments[0].style.visibility='visible';"
            "arguments[0].style.opacity=1;"
            "arguments[0].style.width='1px';"
            "arguments[0].style.height='1px';", inp
        )

    # (Opcional) grid de anexos para verificar que subió
    ANNEX_GRID = [
        # Anclado al texto 'Documentos Anexos'
        (By.XPATH, "//label[contains(.,'Documentos Anexos')]/following::kendo-grid[1]"),
        # Fallback: último kendo-grid del tab
        (By.XPATH, "//div[contains(@class,'tab-pane') and contains(@class,'active')]//kendo-grid[last()]"),
    ]

    def _wait_row_in_annexes(self, filename: str, timeout: float = 10.0) -> None:
        """Espera a ver en la tabla de anexos una fila que contenga el nombre del archivo."""
        grid = self.find_first_fast(self.ANNEX_GRID, per_try=2.0, visible=True)
        xpath = f".//table//tbody//tr[.//td[contains(., {repr(filename)})]]"
        self.wait.with_timeout(timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )


    def upload_anexo(self,ruta_archivo: str) -> None:
        """
        Sube un archivo al área 'Documentos Anexos' sin abrir el diálogo del SO.
        - 'ruta_archivo' debe ser absoluta.
        - Si 'verificar_en_tabla' es True, espera a ver el archivo listado en la tabla.
        """
        assert ruta_archivo and os.path.isabs(ruta_archivo), "Pasa una ruta absoluta."
        assert os.path.exists(ruta_archivo), f"No existe: {ruta_archivo}"

        # 1) localizar el input[type=file]
        inp = self.find_first_fast(self.SUBIR_DOCS_INPUT, per_try=2.0, visible=False)

        # 2) hacerlo interactuable (si está oculto por CSS)
        #self._make_file_input_visible(inp)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)

        # 3) subir el archivo (sin abrir diálogo)
        inp.send_keys(ruta_archivo)

    def _annex_last_row(self):
        grid = self.find_first_fast(self.ANNEX_GRID, per_try=2.0, visible=True)
        row = grid.find_element(By.XPATH, ".//table//tbody//tr[last()]")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
        return row

    def _wait_annex_row_by_filename(self, filename: str, timeout: float = 15.0):
        """
        Espera a que exista una <tr> cuyo 1er td contenga el nombre de archivo
        (texto o value de un input). Devuelve esa fila.
        """
        assert filename and filename.strip()
        fname = os.path.basename(filename).strip()
        grid = self.find_first_fast(self.ANNEX_GRID, per_try=2.0, visible=True)

        xpath = (
            ".//table//tbody//tr[contains(@class,'k-table-row')]["
            f"  .//td[1][contains(normalize-space(.), {repr(fname)})]"
            f" or .//td[1]//input[contains(@value, {repr(fname)})]"
            "]"
        )

        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        row = grid.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)
        return row

    def _select_in_row(self, row, tipo: str):
        """
        Selecciona 'tipo' en el <select> de la columna 'Documento' de la fila dada.
        Intenta match exacto y luego 'contains' (case-insensitive).
        """
        sel = row.find_element(By.XPATH, ".//td[2]//select | .//select[contains(@class,'form-control')]")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)

        s = Select(sel)

        def norm(t: str) -> str:
            return " ".join((t or "").split()).strip().lower()

        target = norm(tipo)
        # 1) exacto
        for opt in s.options:
            if norm(opt.text) == target:
                s.select_by_visible_text(opt.text)
                return
        # 2) contains
        for opt in s.options:
            if target and target in norm(opt.text):
                s.select_by_visible_text(opt.text)
                return

        disponibles = [opt.text.strip() for opt in s.options]
        raise NoSuchElementException(f"No encontré opción '{tipo}'. Opciones: {disponibles}")

    def set_tipo_documento_anexo(self, filename: str, tipo: str, fallback_ultima_fila: bool = True) -> None:
        """
        Busca la fila del anexo por 'filename' y selecciona 'tipo' en su combo.
        Si no la encuentra a tiempo, usa la última fila (útil justo después de subir).
        """
        try:
            row = self._wait_annex_row_by_filename(filename, timeout=15.0)
        except TimeoutException:
            if fallback_ultima_fila:
                row = self._annex_last_row()
            else:
                raise
        self._select_in_row(row, tipo)

    def _select_cliente_in_row(self, row, cliente: str):
        """
        Selecciona el 'Cliente' (combo en la 3ª columna) dentro de la fila dada.
        Intenta match EXACTO y luego 'contains' (case-insensitive).
        """
        # Cliente está en la columna 3 del grid de anexos
        sel = row.find_element(By.XPATH, ".//td[3]//select | .//select[contains(@class,'ng-pristine')]")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel)

        s = Select(sel)

        def norm(t: str) -> str:
            return " ".join((t or "").split()).strip().lower()

        target = norm(cliente)

        # 1) exacto
        for opt in s.options:
            if norm(opt.text) == target:
                s.select_by_visible_text(opt.text)
                return

        # 2) contains (por si pasas solo nombre o apellidos)
        for opt in s.options:
            if target and target in norm(opt.text):
                s.select_by_visible_text(opt.text)
                return

        disponibles = [opt.text.strip() for opt in s.options]
        raise NoSuchElementException(f"No encontré cliente '{cliente}'. Opciones: {disponibles}")

    def set_cliente_anexo(self, filename: str, cliente: str, fallback_ultima_fila: bool = True) -> None:
        """
        Busca la fila del anexo por 'filename' y selecciona el 'Cliente' indicado.
        Si no encuentra la fila a tiempo, usa la última fila (útil tras subir).
        """
        assert filename and cliente, "Pasa filename y nombre del cliente."

        try:
            row = self._wait_annex_row_by_filename(filename, timeout=15.0)
        except Exception:
            if not fallback_ultima_fila:
                raise
            row = self._annex_last_row()

        self._select_cliente_in_row(row, cliente)