
import re, time
from selenium.webdriver.support import expected_conditions as EC
from ..base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Escritura(BasePage):
    def open_url_deeds(self, url:str):
        """
            Abre https://not84.singrafos.com/deeds
        """
        try:
            full_url = url.rstrip("/") + "/deeds"
            self.driver.get(full_url)
            # Esperar que cargue el 'projects'
            self.wait.until(EC.url_contains("/deeds"))
            print("Escrituras cargado correctamente.")
        except Exception as e:
            print(f"Error al cargar escrituras: {e}")
            return
        
    def buscarProyecto(self, descripcion):
        """
            Coloca el nombre en el input del dashboard del portal
        """
        # Esperar campo de búsqueda por placeholder
        try:
            input_buscar = self.wait.until(EC.visibility_of_element_located((By.XPATH,"//input[contains(@placeholder,'Buscar por Escritura, Descripción, Cliente, o Abogado...')]")))

            # Asegurar que también esté interactuable
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@placeholder,'Buscar por Escritura, Descripción, Cliente, o Abogado...')]")))

            # Limpiar la descripción
            descripcion = re.sub(r"[-–—]+", " ", descripcion).strip()
            descripcion = re.sub(r"[\"“”']", "", descripcion).strip()

            # Escribir y presionar ENTER
            input_buscar.clear()
            input_buscar.send_keys(descripcion)
            input_buscar.send_keys(Keys.ENTER)
            print("Campo de búsqueda detectado y texto enviado correctamente.")
            time.sleep(2)
        except Exception as e:
            print(f"No se detectó el campo de búsqueda: {e}")
            return
    
    def subir_adjunto(self):
        try:
            boton_subir = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Subir Adjunto']")))
            # self.driver.execute_script("arguments[0].style.border='3px solid red';", boton_subir)
            # time.sleep(2)
            self.js_click(boton_subir)
        except Exception:
            print(f"No se pudo seleccionar el boton de subir adjunto")

    def set_tipo_documento(self,documento: str):
        # 1) Seleccionar el recuadro (abre el dropdown)
        recuadro = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, "//kendo-dropdownlist//span[contains(@class,'k-input-inner')]"
        )))
        recuadro.click()

        # 2) Esperar la lista de opciones
        opciones_xpath = "//ul[contains(@id,'listbox') or contains(@class,'k-list')]/li"
        self.wait.until(EC.presence_of_all_elements_located((By.XPATH, opciones_xpath)))

        # 3) Hacer click en la opción EXACTA por texto
        opcion = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, f"//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li[normalize-space()='{documento}']"
        )))
        opcion.click()

        # 4) Confirmar que el texto quedó seleccionado
        self.wait.until(EC.text_to_be_present_in_element((
            By.XPATH, "//kendo-dropdownlist//span[contains(@class,'k-input-value-text')]"
        ), documento))

        print(f"✔ Tipo de Documento seleccionado correctamente: {documento}")

    def subir_documento(self,ruta_archivo: str):
        try:
            inp = self.wait.until(EC.presence_of_element_located((
                By.XPATH, "//input[@type='file' and @id='deedDocument']"
            )))
            inp.send_keys(ruta_archivo)

            print(f"✔ Archivo cargado correctamente: {ruta_archivo}")
        except Exception as e:
            print(f"No se pudo cargar el archivo: {e}")
    def set_descripcion(self,cliente: str):
        descripcion = self.wait.until(EC.element_to_be_clickable((
            By.XPATH, "//textarea[@id='description']"
        )))
        descripcion.clear()
        descripcion.send_keys(cliente)

        print(f"✔ Descripción establecida: {cliente}")
    
    def click_cancelar(self):
        boton_cancelar = self.wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'modal-footer')]//button[normalize-space()='Cancelar']"
        )))
        boton_cancelar.click()
        #self.driver.execute_script("arguments[0].style.border='3px solid red';", boton_cancelar)

        print("✔ Botón 'Cancelar' presionado correctamente.")

    def click_subir(self):
        boton_subir = self.wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'modal-footer')]//button[normalize-space()='Subir']"
        )))
        #boton_subir.click()
        self.driver.execute_script("arguments[0].style.border='3px solid blue';", boton_subir)

        print("✔ Botón 'Subir' presionado correctamente.")
    
    def marcar_faltante(self,nombre_documento: str):
        # 1) Esperar a que cargue la tabla
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//kendo-grid//table//tbody")))

        # 2) Buscar la fila cuyo primer td (Descripción) coincida EXACTO
        fila = self.wait.until(EC.presence_of_element_located((By.XPATH,f"//kendo-grid//table//tbody//tr[td[1][normalize-space()='{nombre_documento}']]")))

        # 3) Dentro de esa fila, buscar el checkbox de Faltante
        checkbox = fila.find_element(By.XPATH, ".//input[@type='checkbox']")

        # 4) Si NO está marcado, hacer click
        #if not checkbox.is_selected():
            #self.driver.execute_script("arguments[0].click();", checkbox)

        self.driver.execute_script("arguments[0].click();", checkbox)

        print(f"✔ Marcado como Faltante: {nombre_documento}")
    def click_guardar(self):
        boton_guardar = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'btn-success') and contains(@class,'ms-1')]")))
        #boton_guardar.click()
        self.driver.execute_script("arguments[0].style.border='3px solid red';", boton_guardar)
        print("✔ Botón 'Guardar' presionado correctamente.")