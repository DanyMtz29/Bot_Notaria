#imports independientes
import re, time

#Imports selenium
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

#Imports mios
from Bot.ui_selenium.pages.base import Base
from Bot.ui_selenium.pages.projects_documents import ProjectsDocumentsPage
from Bot.ui_selenium.pages.tap_comentarios import comentariosTab
from Bot.models.modelos import ProyectoMod


class tapModify(Base):
    def buscarNombreProyecto(self, descripcion):
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
        time.sleep(2)

    def limpiar_busqueda_proyecto(self):
        try:
            tacha = self.wait.until(EC.element_to_be_clickable(...))
            tacha.click()
        except Exception:
            pass
    
    def presionar_lupa_nombre(self):
        """Simplemente presiona la lupa del portal del nombre buscado"""
        lupa = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//table//i[contains(@class,'fa-search')]/ancestor::a[contains(@class,'btn-light')]")))
        self.driver.execute_script("arguments[0].click();", lupa)
        #driver.execute_script("arguments[0].style.border='3px solid red'", lupa)s

    def esperar_subida(self):
        """Espera hasta que el archivo a subir se suba correctamente"""
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'col-md-8') and contains(@class,'ms-2')][.//strong[normalize-space()='1']]")))
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")))

    def presionar_modificar_proyecto(self):
        """Presiona el boton modificar en la parte de proyectos (ya creado)"""
        boton_modificar = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class,'btn-primary') and contains(@href,'/projects/edit')]")))
        self.driver.execute_script("arguments[0].click();", boton_modificar)
            
    
    def subir_documentos(self,  proyecto: ProyectoMod) -> None:
        #Esperar a que llegue a la pagina de subir dpcumentos
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#attachment[type='file']")))
        #Seleccionar el input de subida
        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")

        #Iterador para poder seleccionar la papeleria que se sube
        it = 0

        #Auxiliares para metodos ya creados
        comentarios_tab = comentariosTab(self.driver,self.wait)
        docs = ProjectsDocumentsPage(self.driver, self.wait)
    
        for info_parte, docs_parte in proyecto.archivos_para_subir.items():
            nombre_parte, tipo_parte = info_parte
            for doc in docs_parte:
                ruta_doc = doc[1]
                nombre_doc = doc[0]
                inp.send_keys(ruta_doc)
                self.esperar_subida()
                #filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//*[contains(normalize-space(),'.pdf')]]")
                filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tbody[contains(@class,'k-table-tbody')]//tr[@role='row']")
                fila = filas[it]
                it+=1
                Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(nombre_doc)
                if tipo_parte != 'INM':
                    Select(fila.find_element(By.XPATH, ".//td[3]//select")).select_by_visible_text(nombre_parte)
                else:
                    fila.find_element(By.XPATH, ".//td[4]//input").send_keys(nombre_parte)
                    time.sleep(1)
                self.driver.execute_script("arguments[0].value = '';", inp)
                proyecto.contadores[nombre_doc]-=1
                if proyecto.contadores[nombre_doc] == 0:
                    del proyecto.contadores[nombre_doc]
                    docs.set_faltante_by_description(nombre_doc, marcar=True)
                time.sleep(1)
        comentarios_tab.guardar_proyecto()


    def esta_en_revision(self):
        status = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'badge-project')]"))).text.strip().lower()

        return "revisión" in status