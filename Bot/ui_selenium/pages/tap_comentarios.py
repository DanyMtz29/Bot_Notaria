#Improts independientes
import time

#Imports selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#Imports mios
from Bot.ui_selenium.pages.base import Base
from Bot.helpers.logs import registrar_log


class comentariosTab(Base):

    def open_tap_comentarios(self):
        comentarios_tab = self.driver.find_element(
            By.XPATH,
            "//a[contains(@class,'nav-link') and normalize-space()='Comentarios']"
        )
        self.driver.execute_script("arguments[0].click();", comentarios_tab)
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//h4[contains(@class, 'card-title') and contains(., 'Comentarios')]"))
        )

    def agregar_comentario(self, comentario):
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[contains(@class, 'form-control')]")))
            text_area = self.driver.find_element(By.XPATH, "//textarea[contains(@class, 'form-control')]")
            text_area.send_keys(comentario)
        except Exception:
            textarea_locator = (By.XPATH,"//div[contains(@class,'tab-pane') and contains(@class,'active')]//textarea[@id='w3mission']")
            text_area = self.wait.until(EC.element_to_be_clickable(textarea_locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", text_area)
            text_area.clear()
            text_area.send_keys(comentario)

    def enviar_comentario(self, CARPETA_LOGS_ACTO: str):
        xpath = [
            "//button[normalize-space()='Enviar']",
            "//button[.//span[normalize-space()='Enviar']]",
            "//button[@aria-label='Enviar' or @title='Enviar']",
        ]
        for xp in xpath:
            try:
                but = self.driver.find_element(By.XPATH, xp)
                break
            except Exception:
                continue
        if but:
            self.driver.execute_script("arguments[0].click();", but)
        else:
            registrar_log(CARPETA_LOGS_ACTO,"NO SE PUDO SELECCIONAR EL BOTON DE ENVIAR", "ERROR" )
    
    def guardar_proyecto(self, CARPETA_LOGS_ACTO: str, timeout=30):
        xpath = [
            "//button[normalize-space()='Guardar']",
            "//button[.//span[normalize-space()='Guardar']]",
            "//button[@aria-label='Guardar' or @title='Guardar']",
        ]
        for xp in xpath:
            try:
                but = self.driver.find_element(By.XPATH, xp)
                break
            except Exception:
                continue
        if but:
            self.driver.execute_script("arguments[0].click();", but)
            #self.driver.execute_script("arguments[0].style.border='3px solid red'", but)
            try:
                # Esperar hasta 30 s que aparezca el modal de descarga
                modal = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'modal-content')]"))
                )

                # Buscar el botón "Cancelar" dentro del modal
                cancelar_btn = modal.find_element(
                    By.XPATH, ".//button[contains(@class,'btn-outline-dark') and normalize-space()='Cancelar']"
                )

                time.sleep(0.3)  # por animación del modal
                cancelar_btn.click()
                time.sleep(1)

            except Exception:
                pass
        else:
            registrar_log(CARPETA_LOGS_ACTO, "NO SE PUDO SELECCIONAR EL BOTON DE GUARDAR", "ERROR")

    def get_folio(self, descripcion:str) -> str :
        xpath = (
            "//tbody[@role='rowgroup']"
            "//tr[.//td[@aria-colindex='3'][contains(., %s)]]"
            "//td[@aria-colindex='1']//a"
        ) % repr(descripcion)

        elem = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return elem.text.strip()