# bot/pages/projects_page.py
from __future__ import annotations


from bot.utils.common_imports import *
from bot.utils.base import Base
from bot.utils.selenium_imports import *

NEW_PROJECT_URL = "https://not84.singrafos.com/projects/new"

class generalTap(Base):
    # Título / ancla de la vista (sirve para saber que ya cargó)
    TITLE_HINTS = [
        (By.XPATH, "//h1[contains(.,'Proyectos')]"),
        (By.XPATH, "//h2[contains(.,'Proyectos')]"),
        (By.XPATH, "//*[contains(@class,'page-title') and contains(.,'Proyectos')]")
    ]
    
    def open_new_project(self):
        self.driver.get(NEW_PROJECT_URL)
        # Espera que cargue el tab "General"
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//h4[contains(.,'Nuevo Proyecto') or contains(.,'Nuevo Proyecto')]")))

    def set_cliente(self, cliente:str) -> None:
        fila_cliente =self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'form-group') and contains(@class, 'row') and .//label[normalize-space()='Cliente']]"
        )
        input_cliente = fila_cliente.find_element(By.XPATH, ".//input[contains(@class, 'k-input-inner')]")
        input_cliente.send_keys(cliente)
        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li[contains(., '{cliente}')]")
            )
        )
        input_cliente.send_keys(Keys.ARROW_DOWN)
        input_cliente.send_keys(Keys.ENTER)

    def set_descripcion(self,descripcion: str):
        fila_desc =self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'form-group') and contains(@class, 'row') and .//label[normalize-space()='Descripción']]"
        )
        input_cliente = fila_desc.find_element(By.ID, "description")
        input_cliente.send_keys(descripcion)

    def set_actos(self, actos:list) -> None:
        fila_actos =self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'form-group') and contains(@class, 'row') and .//label[normalize-space()='Actos']]"
        )
        combo_actos = fila_actos.find_element(By.XPATH,".//input[@role='combobox']")
        for acto in actos:
            combo_actos.send_keys(acto)
            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li[contains(., '{acto}')]")
                )
            )
            combo_actos.send_keys(Keys.ARROW_DOWN)
            combo_actos.send_keys(Keys.ENTER)
            time.sleep(1)

    def set_abogado(self, abogado: str):
        fila_abogado = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class,'form-group') and .//label[normalize-space()='Abogado']]"
        )
        campo_abogado = fila_abogado.find_element(By.XPATH, ".//span[contains(@class,'k-input-inner')]")
        campo_abogado.click()
        self.wait.until(EC.presence_of_element_located(
            (By.XPATH, "//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li")
        ))
        opcion = self.wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f"//ul[contains(@id,'listbox') or contains(@class,'k-list')]//li[contains(., '{abogado}')]"
        )))
        opcion.click()
        self.wait.until(EC.text_to_be_present_in_element(
            (By.XPATH, "//kendo-dropdownlist//span[contains(@class,'k-input-value-text')]"),
            abogado
        ))

    def create_project(self, abogado: str, cliente: str, descripcion: str, acto: str, auto_save: bool = False):
        self.open_new_project()
        #Abre el combo abogado y selecciona el abogado
        #self._pick_kendo_opcion(self._abrir_combo_en_fila("Abogado"),abogado)
        self.set_abogado(abogado)
        #Colocar el cliente
        self.set_cliente(cliente)
        #Establecer la descripcion
        self.set_descripcion(descripcion)
        #Seleccionar actos correspondientes
        actos = []#==================PENDIENTE DE QUITAR POR EL PARAMETRO
        actos.append(acto)
        self.set_actos(actos)
        
        logger.info("PESTAÑA 'GENERAL' RELLENADA CORRECTAMENTE")

        #Ir a partes
        partes_tab = self.driver.find_element(
            By.XPATH,
            "//a[contains(@class,'nav-link') and normalize-space()='Partes']"
        )
        partes_tab.click()