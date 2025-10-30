# bot/pages/dashboard_page.py
from selenium.webdriver.support import expected_conditions as EC

class DashboardPage:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def assert_loaded(self):
        """
        Consideramos listo el dashboard cuando la URL contiene '/dashboard'.
        """
        self.wait.until(EC.url_contains("/dashboard"))
