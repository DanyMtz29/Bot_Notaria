from __future__ import annotations
import re, time
from selenium.webdriver.common.keys import Keys
from ..base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class tapModify(BasePage):
    def buscarNombreProyecto(self, descripcion):
        """
            Coloca el nombre en el input del dashboard del portal
        """
        # Esperar campo de búsqueda por placeholder
        try:
            input_buscar = self.wait.until(EC.visibility_of_element_located((By.XPATH,"//input[contains(@placeholder,'Buscar por Folio, Descripción, Cliente, o Abogado...')]")))

            # Asegurar que también esté interactuable
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"//input[contains(@placeholder,'Buscar por Folio, Descripción, Cliente, o Abogado...')]")))

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
        
    def presionar_lupa_nombre(self):
        """Simplemente presiona la lupa del portal del nombre buscado"""
        lupa = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//table//i[contains(@class,'fa-search')]/ancestor::a[contains(@class,'btn-light')]")))
        self.driver.execute_script("arguments[0].click();", lupa)
        #driver.execute_script("arguments[0].style.border='3px solid red'", lupa)s

    def presionar_modificar_proyecto(self):
        """
            Presiona el boton modificar en la parte de proyectos (ya creado)
        """
        try:
            boton_modificar = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class,'btn-primary') and contains(@href,'/projects/edit')]")))
            self.driver.execute_script("arguments[0].click();", boton_modificar)
            print(" Botón 'Modificar' presionado correctamente.")
        except Exception as e:
            print(f" No se pudo presionar el botón 'Modificar': {e}")