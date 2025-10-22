from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class LoginPage(BasePage):
    # Varios selectores robustos para cada campo
    EMAIL_LOCATORS = [
        (By.ID, "email"),
        (By.NAME, "email"),
        (By.CSS_SELECTOR, "input[aria-label='Username']"),
        (By.CSS_SELECTOR, "input[placeholder*='Correo']"),
    ]
    PASS_LOCATORS = [
        (By.ID, "password"),
        (By.NAME, "password"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[placeholder*='Contraseña']"),
    ]
    SUBMIT_LOCATORS = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(.,'Iniciar Sesión') or contains(.,'Iniciar Sesion')]"),
    ]

    def accept_cookies_if_any(self):
        # Opcional: por si hay banner de cookies o modal
        possibles = [
            (By.XPATH, "//button[contains(.,'Aceptar') or contains(.,'Aceptar todo') or contains(.,'OK')]"),
            (By.CSS_SELECTOR, "button.cookie-accept, .cookies-accept"),
        ]
        try:
            btn = self.find_first(possibles)
            if btn:
                btn.click()
        except Exception:
            pass  # si no hay, seguimos

    def login(self, url: str, email: str, password: str):
        self.open(url)
        self.accept_cookies_if_any()

        email_el = self.find_first(self.EMAIL_LOCATORS)
        pass_el  = self.find_first(self.PASS_LOCATORS)
        submit   = self.find_first(self.SUBMIT_LOCATORS)

        email_el.clear()
        email_el.send_keys(email)
        pass_el.clear()
        pass_el.send_keys(password)
        submit.click()

        # Espera a que desaparezca el botón de login o cambie la vista
        self.wait.until(
            EC.invisibility_of_element_located(self.SUBMIT_LOCATORS[0])
        )