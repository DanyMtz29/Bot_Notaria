from __future__ import annotations

from bot.utils.base import Base
from bot.utils.common_imports import *
from bot.utils.selenium_imports import *
from bot.core.faltantes import FaltantesService

from bot.utils.common_imports import *

#Posibles quites
from bot.pages.projects_documents import ProjectsDocumentsPage
from bot.pages.Proyectos.tap_comentarios import comentariosTab

class tapModify(Base):
    def buscarNombreProyecto(self, descripcion):
        """
            Coloca el nombre en el input del dashboard del portal
        """
        # Esperar campo de búsqueda por placeholder
        #try:
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
        # except Exception as e:
        #     logger.error(f"No se detectó el campo de búsqueda: {e}")
        #     return

    def limpiar_busqueda_proyecto(self):
        tacha = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'sin-btn-close')]/i[contains(@class,'fa-times')]")))
        tacha.click()
    
    def presionar_lupa_nombre(self):
        """Simplemente presiona la lupa del portal del nombre buscado"""
        lupa = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//table//i[contains(@class,'fa-search')]/ancestor::a[contains(@class,'btn-light')]")))
        self.driver.execute_script("arguments[0].click();", lupa)
        #driver.execute_script("arguments[0].style.border='3px solid red'", lupa)s

    def esperar_subida(self):
        """
            Espera hasta que el archivo a subir se suba correctamente
        """
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'col-md-8') and contains(@class,'ms-2')][.//strong[normalize-space()='1']]")))
        self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'d-none') and contains(@class,'ms-2')][.//strong[normalize-space()='0']]")))

    def presionar_modificar_proyecto(self):
        """
            Presiona el boton modificar en la parte de proyectos (ya creado)
        """
        boton_modificar = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class,'btn-primary') and contains(@href,'/projects/edit')]")))
        self.driver.execute_script("arguments[0].click();", boton_modificar)
            
    
    def subir_documentos(self, archivos_para_subir, contadores) -> None:
        #Esperar a que llegue a la pagina de subir dpcumentos
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#attachment[type='file']")))
        #Seleccionar el input de subida
        inp = self.driver.find_element(By.CSS_SELECTOR, "input#attachment[type='file']")

        #Iterador para poder seleccionar la papeleria que se sube
        it = 0

        #Auxiliares para metodos ya creados
        comentarios_tab = comentariosTab(self.driver,self.wait)
        docs = ProjectsDocumentsPage(self.driver, self.wait)

        for info_parte, docs_parte in archivos_para_subir.items():
            tipo, nombre_parte, rol = FaltantesService._parse_tuple_key(info_parte)
            print(f"Nombre_parte: {nombre_parte}") 
            for nombre_doc, ruta_doc in docs_parte:
                print(f"Procesando doc: {nombre_doc}")
                inp.send_keys(ruta_doc)
                self.esperar_subida()
                filas = self.driver.find_elements(By.XPATH,f"//div[@role='grid']//tr[.//*[contains(normalize-space(),'.pdf')]]")
                fila = filas[it]
                it+=1
                Select(fila.find_element(By.XPATH, ".//td[2]//select")).select_by_visible_text(nombre_doc)
                if rol != 'INM':
                    Select(fila.find_element(By.XPATH, ".//td[3]//select")).select_by_visible_text(nombre_parte)
                else:
                    fila.find_element(By.XPATH, ".//td[4]//input").send_keys(nombre_parte)
                    time.sleep(1)
                self.driver.execute_script("arguments[0].value = '';", inp)
                contadores[nombre_doc]-=1
                if contadores[nombre_doc] == 0:
                    docs.set_faltante_by_description(nombre_doc, marcar=True)
                time.sleep(1)
                                
        comentarios_tab.guardar_proyecto()


    def esta_en_revision(self):
        status = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'badge-project')]"))).text.strip().lower()
        status2 = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'badge-project')]")))

        if "revisión" in status:
            logger.info("⛔ El proyecto está EN REVISIÓN, no se puede modificar.")
            return True
        else:
            logger.info("✅ Proyecto no está en revisión, continuar.")
            return False