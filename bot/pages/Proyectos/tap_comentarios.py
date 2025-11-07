# bot/pages/projects_page.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from ..base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

class comentariosTab(BasePage):

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
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//textarea[contains(@class, 'form-control')]"))
        )
        text_area = self.driver.find_element(By.XPATH, "//textarea[contains(@class, 'form-control')]")
        text_area.send_keys(comentario)

    def enviar_comentario(self):
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
            print("NO SE PUDO SELECCIONAR EL BOTON DE ENVIAR XC")
    
    def guardar_proyecto(self, timeout=30):
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
                print("💬 Modal detectado. Intentando presionar 'Cancelar'...")

                # Buscar el botón "Cancelar" dentro del modal
                cancelar_btn = modal.find_element(
                    By.XPATH, ".//button[contains(@class,'btn-outline-dark') and normalize-space()='Cancelar']"
                )

                time.sleep(0.3)  # por animación del modal
                cancelar_btn.click()
                print("✅ Se presionó 'Cancelar' correctamente.")
                time.sleep(1)

            except Exception:
                # Si no aparece en 30 s o no se encuentra el modal
                print("ℹ️ No apareció ningún modal de descarga, continuando con el flujo...")
        else:
            print("NO SE PUDO SELECCIONAR EL BOTON DE ENVIAR XC")
