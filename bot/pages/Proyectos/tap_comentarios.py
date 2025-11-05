# bot/pages/projects_page.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from ..base_page import BasePage
from selenium.webdriver.support import expected_conditions as EC

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
    
    def guardar_proyecto(self):
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
            #self.driver.execute_script("arguments[0].click();", but)
            self.driver.execute_script("arguments[0].style.border='3px solid red'", but)
        else:
            print("NO SE PUDO SELECCIONAR EL BOTON DE ENVIAR XC")