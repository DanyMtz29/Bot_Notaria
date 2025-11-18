# bot/pages/login_page.py
from __future__ import annotations
from selenium.webdriver.common.by import By
from bot.utils.base import Base
from bot.utils.common_imports import *

class LoginPage(Base):
    # Selectores combinados (un solo wait por campo, MUY rápido)
    EMAIL = (By.CSS_SELECTOR,
        "input[formcontrolname='email'],"
        "input[formcontrolname='username'],"
        "input[type='email'],"
        "#email,"
        "input[name='email'],"
        "input[placeholder*='correo' i],"
        "input[placeholder*='mail' i],"
        "input[aria-label*='correo' i],"
        "input[aria-label*='email' i]"
    )

    PASSWORD = (By.CSS_SELECTOR,
        "input[formcontrolname='password'],"
        "input[type='password'],"
        "#password,"
        "input[name='password']"
    )

    # Primero intentamos el típico submit; si no, caemos a texto con XPath
    SUBMIT_CSS = (By.CSS_SELECTOR, "button[type='submit'], button.k-button[type='submit']")
    SUBMIT_XPATH = (By.XPATH, "//button[contains(translate(.,'INICIARÉÓÁÍÚ','iniciareóáíú'), 'iniciar') or contains(translate(.,'ENTRAR','entrar'),'entrar')]")

    def accept_cookies_if_any(self):
        try:
            b = self.find_first_fast([
                (By.XPATH, "//button[contains(.,'Aceptar') or contains(.,'Aceptar todo') or contains(.,'OK')]"),
                (By.CSS_SELECTOR, "button.cookie-accept, .cookies-accept")
            ], per_try=0.8, visible=True)
            b.click()
        except Exception:
            pass

    def login(self, email: str, password: str):
        try: 
            self.open_url("login")
            self.accept_cookies_if_any()

            # <<< CLAVE >>> espera a que Angular pinte el DOM del login
            self.wait_for_app_ready(timeout=15)

            email_el = self.find_first_fast([self.EMAIL], per_try=2.0, visible=True)
            pass_el  = self.find_first_fast([self.PASSWORD], per_try=2.0, visible=True)
            self.type_text(email_el, email)
            self.type_text(pass_el,  password)

            try:
                self.click_when_clickable(self.SUBMIT_CSS, timeout=2.0).click()
            except Exception:
                # fallback por si el botón no es type=submit
                btn = self.find_first_fast([self.SUBMIT_XPATH], per_try=1.2, visible=True)
                self.driver.execute_script("arguments[0].click();", btn)

            # Sal de /login (espera a que cambie la URL o se muestre el dashboard)
            self.wait.until(lambda d: "login" not in d.current_url.lower())
        except Exception as e:
            logger.error(f"No se pudo iniciar sesion {e}")
